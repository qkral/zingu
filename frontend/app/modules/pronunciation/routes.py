import logging
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from typing import Dict, List
from .pronunciation_assessor import PronunciationAssessor

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Create pronunciation assessor
pronunciation_assessor = PronunciationAssessor()

@router.post("/improve-pronunciation")
async def improve_pronunciation(
    audio: UploadFile = File(...),
    reference_text: str = Form(...),
) -> Dict:
    """
    Assess pronunciation and provide feedback.
    
    Args:
        audio: Audio file containing speech to assess
        reference_text: Text that was supposed to be spoken
        
    Returns:
        Dict containing pronunciation assessment and feedback
    """
    try:
        logger.info(f"Processing pronunciation assessment for reference text: {reference_text}")
        
        # Read audio data
        audio_data = await audio.read()
        
        # Get pronunciation assessment
        assessment = await pronunciation_assessor.assess_pronunciation(
            audio_data=audio_data,
            reference_text=reference_text
        )
        
        logger.info("Successfully processed pronunciation assessment")

        # Convert to response format
        return {
            "accuracy": assessment.accuracy_score,
            "pronunciation": assessment.pronunciation_score,
            "completeness": assessment.completeness_score,
            "fluency": assessment.fluency_score,
            "words": [
                {
                    "word": word["word"],
                    "accuracy": word["accuracy"],
                    "error_type": word["error_type"],
                    "syllables": [
                        {
                            "syllable": s["syllable"],
                            "accuracy": s["accuracy"]
                        }
                        for s in word["syllables"]
                    ],
                    "phonemes": [
                        {
                            "phoneme": p["phoneme"],
                            "accuracy": p["accuracy"]
                        }
                        for p in word["phonemes"]
                    ]
                }
                for word in assessment.words
            ],
            "phoneme_level_feedback": assessment.phoneme_level_feedback,
            "general_feedback": assessment.general_feedback
        }
        
    except Exception as e:
        logger.error(f"Error processing pronunciation assessment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing pronunciation assessment: {str(e)}"
        )
