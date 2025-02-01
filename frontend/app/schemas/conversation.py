from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class PronunciationHelpRequest(BaseModel):
    poor_words: List[Dict[str, Any]]
    language: Optional[str] = 'en-US'
    accent: Optional[str] = 'neutral'

class HistoryMessage(BaseModel):
    text: str
    isUser: bool
    topic_id: Optional[str] = None

class ConversationRequest(BaseModel):
    text: str
    language: str
    accent: str
    voice_name: str
    history: Optional[List[HistoryMessage]] = None
    topic_id: Optional[str] = None
