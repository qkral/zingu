from pydantic import BaseModel
from typing import List, Optional, Dict

class Exercise(BaseModel):
    """Model for pronunciation exercises."""
    title: str
    description: str
    example_words: List[str]
    difficulty: int

class UserQuery(BaseModel):
    """Model for user queries to the AI coach."""
    message: str
    pronunciation_history: Optional[List[Dict[str, float]]] = None
    current_focus: Optional[str] = None

class CoachResponse(BaseModel):
    """Model for AI coach responses."""
    message: str
    exercises: Optional[List[Exercise]] = None
    suggestions: Optional[List[str]] = None
    focus_areas: Optional[List[str]] = None
