import React, { useState, useEffect } from "react";
import AudioRecorder from "./AudioRecorder";
import "./CallLive.css";

const CallLive = () => {
  const [isChatActive, setIsChatActive] = useState(false);
  const [recording, setRecording] = useState(false);
  const [messages, setMessages] = useState([]);
  const [autoRecord, setAutoRecord] = useState(false);

  const resetChat = () => {
    console.log("Resetting chat...");
    setIsChatActive(false);
    setRecording(false);
    setMessages([]);
    setAutoRecord(false);
  };

  const handleTTS = (text, onComplete) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onend = onComplete; // Trigger callback after speech ends
    console.log("Speaking:", text);
    window.speechSynthesis.speak(utterance);
  };

  const handleStartChat = () => {
    console.log("Starting chat...");
    setIsChatActive(true);
    const initialMessage = "Hi, I'm Callbot. How can I assist you?";
    setMessages([{ sender: "Bot", text: initialMessage }]);
    handleTTS(initialMessage, () => handleStartRecording());
  };

  // const handleAudioStop = async (audioBlob) => {
  //   console.log("Audio recording stopped. Sending to backend...");
  //   console.log("Audio Blob details:", audioBlob);

  //   const formData = new FormData();
  //   formData.append("file", audioBlob, "recording.wav");

  //   try {
  //     const response = await fetch("http://localhost:8000/transcribe_and_chat", {
  //       method: "POST",
  //       body: formData,
  //     });

  //     console.log("Backend response:", response);

  //     if (response.status === 301) {
  //       const exitMessage = "Thanks for calling Callbot.";
  //       setMessages((prev) => [...prev, { sender: "Bot", text: exitMessage }]);
  //       handleTTS(exitMessage, resetChat);
  //       return;
  //     }

  //     const data = await response.json();
  //     console.log("Transcription and response from backend:", data);

  //     setMessages((prev) => [...prev, { sender: "Bot", text: data.response }]);
  //     handleTTS(data.response, () => {
  //       console.log("Re-enabling autoRecord after response.");
  //       setAutoRecord(true); // Trigger next recording
  //     });
  //   } catch (error) {
  //     console.error("Error communicating with backend:", error);
  //     setMessages((prev) => [
  //       ...prev,
  //       { sender: "Bot", text: "Sorry, something went wrong!" },
  //     ]);
  //   }
  // };
  const handleAudioStop = async (audioBlob) => {
    console.log("Audio recording stopped. Sending to backend...");
    console.log("Audio Blob details:", audioBlob);

    const formData = new FormData();
    formData.append("file", audioBlob, "recording.wav");

    try {
      const response = await fetch(
        "https://calllivedemo.onrender.com/transcribe_and_chat",
        {
          method: "POST",
          body: formData,
        }
      );

      console.log("Backend response:", response);

      if (response.status === 301) {
        const exitMessage = "Thanks for calling Callbot.";
        setMessages((prev) => [...prev, { sender: "Bot", text: exitMessage }]);
        handleTTS(exitMessage, resetChat);
        return;
      }

      const data = await response.json();
      console.log("Transcription and response from backend:", data);

      // Add the transcribed text and bot response to the chat
      setMessages((prev) => [
        ...prev,
        { sender: "User", text: data.query }, // Transcribed text
        { sender: "Bot", text: data.response }, // Bot response
      ]);
      handleTTS(data.response, () => {
        console.log("Re-enabling autoRecord after response.");
        setAutoRecord(true); // Trigger next recording
      });
    } catch (error) {
      console.error("Error communicating with backend:", error);
      setMessages((prev) => [
        ...prev,
        { sender: "Bot", text: "Sorry, something went wrong!" },
      ]);
    }
  };

  const handleStartRecording = () => {
    if (!recording) {
      console.log("Starting audio recording...");
      setRecording(true); // Trigger recording start
      setTimeout(() => {
        console.log("Timeout reached, stopping recording.");
        handleStopRecording(); // Stop recording after 8 seconds
      }, 8000);
    }
  };

  const handleStopRecording = () => {
    console.log("handleStopRecording triggered.");
    setRecording(false); // Stop recording
    setAutoRecord(false); // Ensure autoRecord is reset
  };

  useEffect(() => {
    if (autoRecord) {
      console.log("Auto recording triggered.");
      handleStartRecording();
    }
  }, [autoRecord]);

  return (
    <div className="container mt-4">
      <div className="card">
        <div className="card-body">
          <h5 className="card-title">CallBot</h5>
          {isChatActive ? (
            <>
              <div
                className="chat-window mb-3"
                style={{ maxHeight: "300px", overflowY: "auto" }}
              >
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`message ${
                      msg.sender === "Bot" ? "bot-message" : "user-message"
                    }`}
                    style={{
                      textAlign: msg.sender === "Bot" ? "left" : "right",
                      margin: "5px 0",
                    }}
                  >
                    <strong>{msg.sender}:</strong> {msg.text}
                  </div>
                ))}
              </div>

              {recording && <p className="text-warning">Recording...</p>}
              <div className="d-flex justify-content-between">
                <button className="btn btn-danger" onClick={resetChat}>
                  End Chat
                </button>
              </div>
            </>
          ) : (
            <button className="btn btn-success" onClick={handleStartChat}>
              Start CallLive.ai
            </button>
          )}
        </div>
      </div>
      <AudioRecorder recording={recording} onStop={handleAudioStop} />
    </div>
  );
};

export default CallLive;
