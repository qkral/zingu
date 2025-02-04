from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Union, Dict
import logging

from app.services.translation import translation_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/translation",
    tags=["translation"]
)

class TranslationRequest(BaseModel):
    text: str
    target_language: Optional[str] = 'en'
    native_language: Optional[str] = None

class TranslationResponse(BaseModel):
    translated_text: str

@router.post("/translate", response_model=Union[TranslationResponse, Dict[str, str]])
def translate_text(request: TranslationRequest):
    """
    Translate text to the specified target language.
    
    Args:
        request (TranslationRequest): Translation request with text, target language, and native language
    
    Returns:
        Union[TranslationResponse, Dict[str, str]]: Translated text or a language selection message
    """
    logger.info(f"Received translation request: {request}")
    try:
        result = translation_service.translate_text(
            request.text, 
            request.target_language,
            request.native_language
        )
        
        # Check if result is a dictionary (language selection message)
        if isinstance(result, dict):
            return result
        
        # Otherwise, return as a translation response
        logger.info(f"Translation result: {result}")
        return {"translated_text": result}
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
