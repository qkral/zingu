from fastapi import APIRouter, HTTPException
from .models import UserQuery, CoachResponse
from .coach import AICoach
import logging

router = APIRouter()
coach = AICoach()
logger = logging.getLogger(__name__)

@router.post("/ai-coach", response_model=CoachResponse)
async def get_coach_response(query: UserQuery):
    """
    Get AI coach response for pronunciation improvement.
    """
    try:
        response = await coach.get_response(query)
        return response
    except Exception as e:
        logger.error(f"Error in AI coach endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
