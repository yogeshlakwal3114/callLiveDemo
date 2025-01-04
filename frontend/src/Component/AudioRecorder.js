import React, { useState, useEffect } from "react";

const AudioRecorder = ({ recording, onStop }) => {
  const [mediaRecorder, setMediaRecorder] = useState(null);
  // const [audioChunks, setAudioChunks] = useState([]);
  const localAudioChunks = [];

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
  
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          // setAudioChunks((prev) => {
          //   console.log(event.data);
          //   return [...prev, event.data]
          // });
          localAudioChunks.push(event.data);
        } else {
          console.warn("Empty audio chunk received.");
        }
      };
      
      recorder.onstop = () => {
        console.log("Recorder stopped. Number of chunks:", localAudioChunks.length);
        if (localAudioChunks.length === 0) {
          console.error("No audio data captured. Ensure microphone access is allowed.");
          onStop(new Blob()); // Send an empty blob
        } else {
          const audioBlob = new Blob(localAudioChunks, { type: "audio/wav" });
          onStop(audioBlob);
        }
      };

      recorder.onerror = (event) => {
        console.error("Recording error:", event.error);
      };
  
      recorder.start();
      setMediaRecorder(recorder);
    } catch (error) {
      console.error("Error accessing microphone:", error);
    }
  };
  

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      setMediaRecorder(null);
    }
  };

  useEffect(() => {
    console.log("Recording state changed:", recording);
    if (recording) {
      console.log("Starting MediaRecorder...");
      startRecording();
    } else {
      console.log("Stopping MediaRecorder...");
      stopRecording();
    }
  }, [recording]);
  
};

export default AudioRecorder;
