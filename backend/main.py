from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import os
import uuid
import base64
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import io

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

# Qdrant client initialization
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "KnowledgeBase"
VECTOR_SIZE = 384

# Hardcoded PDF path
PDF_PATH = "./Knowledge_base/test.pdf"  # Replace with your PDF path

qdrant_client = QdrantClient(url=QDRANT_URL)

def initialize_qdrant_collection():
    """Ensure the Qdrant collection is initialized with the correct vector size."""
    try:
        collections = qdrant_client.get_collections()
        collection_names = [col.name for col in collections.collections]
        if COLLECTION_NAME in collection_names:
            print(f"Deleting existing collection '{COLLECTION_NAME}'...")
            qdrant_client.delete_collection(collection_name=COLLECTION_NAME)

        print(f"Creating collection '{COLLECTION_NAME}' with vector size {VECTOR_SIZE}...")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance="Cosine"),
        )
        print(f"Collection '{COLLECTION_NAME}' created.")
    except Exception as e:
        print(f"Error initializing Qdrant collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize Qdrant collection.")

@app.on_event("startup")
async def startup_event():
    """Initialize resources during app startup."""
    print("Initializing Qdrant collection...")
    initialize_qdrant_collection()
    print("Qdrant collection initialized.")
    
    # Process PDF and add to vector database during startup
    try:
        print(f"Processing PDF from {PDF_PATH}...")
        with open(PDF_PATH, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
            text = chatbot_instance.extract_text_from_pdf(pdf_content)
            chatbot_instance.add_to_qdrant(text)
        print("PDF processed and added to knowledge base")
    except Exception as e:
        print(f"Error processing PDF during startup: {e}")
        # Don't raise an exception here, as we want the app to start even if PDF processing fails

class ChatbotWithMemory:
    def __init__(self):
        self.conversation_history = []
        self.user_info = {
            'name': None,
            'contact': None,
            'preferred_time': None
        }
        # Initialize embedding model
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=60,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )

    def extract_text_from_pdf(self, pdf_file):
        """Extract text from a PDF file."""
        try:
            pdf_content = io.BytesIO(pdf_file)
            pdf_reader = PdfReader(pdf_content)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            raise HTTPException(status_code=500, detail="Failed to extract text from PDF")

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

    def generate_response(self, query, context):
        system_prompt = f"""
        Current user information:
        Name: {self.user_info['name'] or 'Not provided'}
        Contact: {self.user_info['contact'] or 'Not provided'}
        Preferred Time: {self.user_info['preferred_time'] or 'Not provided'}

        Previous conversation:
        {' '.join(self.conversation_history[-3:] if self.conversation_history else [])}

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
                    {"role": "user", "content": f"Context: {context}\n\nUser's query: {query}"}
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
        context = self.search(query)
        response = self.generate_response(query, context)
        self.conversation_history.append(f"Bot: {response}")
        return response

    def search(self, query):
        query_embedding = self.embedding_model.encode(query).tolist()
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=8
        )
        return [result.payload['context'] for result in search_results]

    def add_to_qdrant(self, text):
        """Split the text, generate embeddings, and store them in Qdrant."""
        chunks = self.text_splitter.split_text(text)
        embeddings = self.embedding_model.encode(chunks)
        payloads = [{'context': chunk} for chunk in chunks]
        points = [
            models.PointStruct(id=uuid.uuid4().hex, vector=embedding.tolist(), payload=payload)
            for embedding, payload in zip(embeddings, payloads)
        ]
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"Stored {len(chunks)} chunks in Qdrant.")

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
