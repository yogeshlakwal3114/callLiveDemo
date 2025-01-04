from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from PyPDF2 import PdfReader
import os
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend URL for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Hardcoded PDF path
PDF_PATH = "./Knowledge_base/test.pdf"  # Replace with your PDF path

class ChatbotWithMemory:
    def __init__(self):
        self.conversation_history = []
        self.user_info = {
            'name': None,
            'contact': None,
            'preferred_time': None
        }
        self.pdf_content = self.load_pdf_content()

    def load_pdf_content(self):
        """Load and extract text from the PDF."""
        try:
            with open(PDF_PATH, 'rb') as pdf_file:
                pdf_reader = PdfReader(io.BytesIO(pdf_file.read()))
                text = "".join(page.extract_text() for page in pdf_reader.pages)
                return text
        except Exception as e:
            print(f"Error loading PDF content: {e}")
            raise HTTPException(status_code=500, detail="Failed to load PDF content")

    def update_user_info(self, query):
        if "name is" in query.lower():
            name = query.lower().split("name is")[-1].strip()
            self.user_info['name'] = name

        if "contact" in query.lower() and any(char.isdigit() for char in query):
            contact = ''.join(filter(str.isdigit, query))
            self.user_info['contact'] = contact

        if any(time_indicator in query.lower() for time_indicator in ['am', 'pm']) or \
           any(str(hour) in query for hour in range(1, 13)):
            self.user_info['preferred_time'] = query

    def generate_response(self, query):
        system_prompt = f"""
        Current user information:
        Name: {self.user_info['name'] or 'Not provided'}
        Contact: {self.user_info['contact'] or 'Not provided'}
        Preferred Time: {self.user_info['preferred_time'] or 'Not provided'}

        Previous conversation:
        {' '.join(self.conversation_history[-3:] if self.conversation_history else [])}

        PDF Context:
        {self.pdf_content}

        Instructions:
        - The responses shouldn't be too text heavy
        - If the user's name is not provided, ask for it
        - If you have the name but no time preference, ask for preferred appointment time
        - If you have both name and time, suggest available slots close to their preference
        - Once all details are confirmed, proceed with booking confirmation
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating response: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate response")

    def chatbot(self, query):
        self.update_user_info(query)
        self.conversation_history.append(f"User: {query}")
        response = self.generate_response(query)
        self.conversation_history.append(f"Bot: {response}")
        return response

chatbot_instance = ChatbotWithMemory()

class TranscriptionResponse(BaseModel):
    query: str
    response: str
    status_code: int

@app.post("/transcribe_and_chat", response_model=TranscriptionResponse)
async def transcribe_and_chat(file: UploadFile):
    try:
        file_content = await file.read()

        # Use OpenAI's Whisper API for transcription
        with open("temp_audio.wav", "wb") as temp_file:
            temp_file.write(file_content)

        with open("temp_audio.wav", "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        transcribed_text = transcription.text.strip()
        print(f"Transcription result: {transcribed_text}")

        # End chat if the user says "Exit"
        if "exit" in transcribed_text.lower():
            return JSONResponse(status_code=301, content={"response": "Thanks for Calling Callbot"})

        # Generate chatbot response
        response = chatbot_instance.chatbot(transcribed_text)
        return TranscriptionResponse(query=transcribed_text, response=response, status_code=200)

    except Exception as e:
        print(f"Error in /transcribe_and_chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists("temp_audio.wav"):
            os.remove("temp_audio.wav")