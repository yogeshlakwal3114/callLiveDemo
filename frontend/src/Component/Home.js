import React, { useState } from "react";
import { Container, Row, Col, Form, Button, Spinner } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import "./Home.css";  

const HomePage = () => {
  const [firstMessage, setFirstMessage] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [knowledgeBase, setKnowledgeBase] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData();
    formData.append("firstMessage", firstMessage);
    formData.append("systemPrompt", systemPrompt);
    if (knowledgeBase) formData.append("knowledgeBase", knowledgeBase);

    try {
      const response = await fetch("your api", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        console.error("Submission failed");
      } else {
        console.log("Form submitted successfully");
        navigate("/chat");;
      }
    } catch (error) {
      console.error("Error in submitting form:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="shiny-background">
      <Container className="mt-5">
        <Row className="justify-content-center">
          <Col md={8} className="p-4 rounded shadow-lg bg-white">
            <h2 className="text-center mb-4">Model Configuration</h2>
            <Form onSubmit={handleSubmit}>
              <Form.Group controlId="firstMessage" className="mb-3">
                <Form.Label>First Message</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="Enter first message"
                  value={firstMessage}
                  onChange={(e) => setFirstMessage(e.target.value)}
                />
              </Form.Group>

              <Form.Group controlId="systemPrompt" className="mb-3">
                <Form.Label>System Prompt</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={4}
                  placeholder="Enter system prompt"
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                />
              </Form.Group>

              <Form.Group controlId="knowledgeBase" className="mb-3">
                <Form.Label>Knowledge Base</Form.Label>
                <Form.Control
                  type="file"
                  onChange={(e) => setKnowledgeBase(e.target.files[0])}
                />
              </Form.Group>

              <Row className="justify-content-end">
                <Col>
                  <Button
                    variant="primary"
                    type="submit"
                    onClick={handleSubmit}
                    disabled={isLoading}
                    className="d-flex align-items-center"
                  >
                    {isLoading ? (
                      <>
                        <Spinner
                          as="span"
                          animation="border"
                          size="sm"
                          role="status"
                          aria-hidden="true"
                        />
                        <span className="ms-2">Submitting...</span>
                      </>
                    ) : (
                      "Submit"
                    )}
                  </Button>
                </Col>
              </Row>
            </Form>
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default HomePage;
