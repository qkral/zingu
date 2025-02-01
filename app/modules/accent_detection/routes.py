from fastapi import APIRouter, UploadFile, HTTPException
from .accent_detector import AccentDetector
from typing import Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
accent_detector = AccentDetector()

@router.post("/detect-accent")
async def detect_accent(audio: UploadFile) -> Dict[str, float]:
    """
    Endpoint to detect accent from uploaded audio file.
    Returns a dictionary of accent probabilities.
    """
    logger.info(f"Received audio file: {audio.filename}, content_type: {audio.content_type}")
    
    if not audio.content_type.startswith('audio/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an audio file"
        )
    
    try:
        # Read the audio file
        audio_data = await audio.read()
        logger.info(f"Successfully read audio data, size: {len(audio_data)} bytes")
        
        # Detect accent
        result = await accent_detector.detect_accent(audio_data)
        logger.info(f"Accent detection result: {result}")
        
        return result
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        )
