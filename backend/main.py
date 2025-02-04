from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv
import base64
from app.services import speech, pronunciation, conversation
from app.main import app

# Load environment variables at startup
load_dotenv()

# Configure CORS
origins = [f"http://localhost:{port}" for port in range(5000, 6000)] + [f"http://127.0.0.1:{port}" for port in range(5000, 6000)] + [
    "https://sample-firebase-ai-app-a0694.web.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.routers import coach
app.include_router(coach.router)

class AccentDetectionResult(BaseModel):
    accents: Dict[str, float]
    confidence: float

class PronunciationFeedback(BaseModel):
    accuracy: float
    pronunciation: float
    completeness: float
    fluency: float
    words: List[Dict[str, Any]]
    phoneme_level_feedback: List[str]
    general_feedback: List[str]

class AICoachRequest(BaseModel):
    message: str
    pronunciation_history: List[Dict[str, Any]]

class AICoachResponse(BaseModel):
    message: str
    exercises: List[Dict[str, Any]]

@app.post("/api/detect-accent", response_model=AccentDetectionResult)
async def detect_accent(audio: UploadFile = File(...)):
    """
    Detect accent from uploaded audio file using Azure Speech Services
    """
    try:
        # TODO: Implement accent detection using Azure Speech Services
        # This is a placeholder response
        return AccentDetectionResult(
            accents={"French": 0.8, "Chinese": 0.2},
            confidence=0.9
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/improve-pronunciation", response_model=PronunciationFeedback)
async def improve_pronunciation(audio: UploadFile = File(...), reference_text: str = Form(...)):
    """
    Analyze pronunciation and provide feedback using Azure Speech Services
    """
    try:
        # TODO: Implement pronunciation assessment using Azure Speech Services
        # This is a placeholder response
        return PronunciationFeedback(
            accuracy=0.75,
            pronunciation=0.72,
            completeness=0.80,
            fluency=0.78,
            words=[
                {
                    "word": "example",
                    "accuracy": 0.75,  
                    "error_type": "pronunciation",
                    "syllables": [{"syllable": "ex", "accuracy": 0.7}, {"syllable": "am", "accuracy": 0.8}],
                    "phonemes": [{"phoneme": "ɪɡ", "accuracy": 0.7}]
                },
                {
                    "word": "test",
                    "accuracy": 0.65,  
                    "error_type": "stress",
                    "syllables": [{"syllable": "test", "accuracy": 0.65}],
                    "phonemes": [{"phoneme": "t", "accuracy": 0.6}, {"phoneme": "ɛ", "accuracy": 0.7}]
                }
            ],
            phoneme_level_feedback=["Work on the 'ex' sound in 'example'", "The 't' sound in 'test' needs improvement"],
            general_feedback=["Overall pronunciation needs some work", "Focus on word stress and clear articulation"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coach/analyze-pronunciation")
async def analyze_pronunciation_endpoint(
    audio: UploadFile = File(...),
    language: str = Form(...),
    accent: str = Form(...),
    reference_text: str = Form(...)
):
    """Endpoint to analyze pronunciation of an audio file"""
    try:
        # Read audio file
        audio_data = await audio.read()
        
        # Analyze pronunciation
        pronunciation_feedback = await pronunciation.analyze_pronunciation(
            audio_data,
            reference_text=reference_text,
            language=f"{language}-{accent}"
        )
        
        return {
            "pronunciation_feedback": pronunciation_feedback
        }
        
    except Exception as e:
        print(f"Error in analyze_pronunciation_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coach/process-response")
async def process_response(
    audio: UploadFile = File(...),
    language: str = Form(...),
    accent: str = Form(...),
    voice_name: str = Form(...),
    topic: Optional[str] = Form(None)
):
    """Process user's audio response and generate AI coach response"""
    try:
        # Read audio file
        audio_data = await audio.read()
        
        # Transcribe audio
        transcribed_text = await speech.transcribe_audio(
            audio_data,
            language=f"{language}-{accent}"
        )
        
        if not transcribed_text:
            raise HTTPException(status_code=400, detail="No speech detected in the audio")
            

        # If no topic is provided, use a default topic
        if not topic:
            # You might want to choose a default topic based on language or other criteria
            topic = 'travel'  # Default to 'travel' topic
            print(f"No topic provided. Using default topic: {topic}")
        
        print('come here?', topic)
        
        # Generate AI response without pronunciation feedback
        message = await conversation.generate_response(
            transcribed_text,
            language=language,
            accent=accent,
            topic_id=topic,
            history=None  # TODO: Implement conversation history tracking
        )

        
        # Generate audio response
        audio_response = await speech.generate_speech(
            message,
            voice_name=voice_name
        )
        

        # Encode audio to base64
        audio_base64 = base64.b64encode(audio_response).decode('utf-8')
        
        return {
            "transcribed_text": transcribed_text,
            "message": message,
            "audio": audio_base64
        }
        
    except Exception as e:
        print(f"Error in process_response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-coach", response_model=AICoachResponse)
async def get_ai_coach(request: AICoachRequest):
    """
    Get personalized coaching suggestions based on pronunciation history
    """
    try:
        # Create a prompt for GPT to generate personalized feedback
        pronunciation_issues = "\n".join([
            f"- Word: {item['word']}, Accuracy: {item['accuracy']}%, Problem phonemes: {item['phoneme']}"
            for item in request.pronunciation_history
        ])

        prompt = f"""As an AI pronunciation coach, create personalized feedback and exercises based on these pronunciation issues:

{pronunciation_issues}

Provide:
1. A supportive message acknowledging their effort and specific areas to improve
2. 2-3 targeted exercises with:
   - Clear title
   - Detailed description of how to practice
   - 4-5 example words
   - Difficulty level (1-5)

Format the response as JSON with this structure:
{{
    "message": "encouraging message here",
    "exercises": [
        {{
            "title": "exercise title",
            "description": "detailed practice instructions",
            "example_words": ["word1", "word2", "word3", "word4"],
            "difficulty": 2
        }}
    ]
}}"""

        # Get AI response
        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert pronunciation coach, skilled at creating targeted exercises for English learners."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )

        # Parse the JSON response
        import json
        coaching_response = json.loads(response.choices[0].message.content)
        
        return AICoachResponse(**coaching_response)

    except Exception as e:
        print(f"Error generating AI coach response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to Accent Improver API"}
