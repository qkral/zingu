import os
import openai
from typing import List, Optional
from .models import UserQuery, CoachResponse, Exercise
import json
import logging

logger = logging.getLogger(__name__)

class AICoach:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        openai.api_key = self.api_key

    async def get_response(self, query: UserQuery) -> CoachResponse:
        """Get AI coach response for user query."""
        try:
            # Construct the system message
            system_message = """You are an expert pronunciation coach, specializing in English pronunciation. 
            Your role is to help users improve their pronunciation by:
            1. Providing clear, actionable feedback
            2. Creating targeted exercises
            3. Explaining pronunciation concepts in an accessible way
            4. Focusing on the user's specific needs and problem areas"""

            # Construct the context from pronunciation history
            context = ""
            if query.pronunciation_history:
                context = "Based on your previous attempts:\n"
                for hist in query.pronunciation_history:
                    context += f"- Sound '{hist.get('phoneme', '')}': {hist.get('accuracy', 0)}% accuracy\n"

            # Create the messages array
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"{context}\nUser query: {query.message}"}
            ]

            # Get response from OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            # Parse the response
            content = response.choices[0].message['content']

            # Try to extract exercises if present
            exercises: List[Exercise] = []
            try:
                # Look for exercises in JSON format
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    if json_end > json_start:
                        exercises_json = content[json_start:json_end].strip()
                        exercises_data = json.loads(exercises_json)
                        if isinstance(exercises_data, list):
                            exercises = [Exercise(**ex) for ex in exercises_data]
                        content = content[:json_start-7] + content[json_end+3:]
            except Exception as e:
                logger.warning(f"Failed to parse exercises from response: {str(e)}")

            return CoachResponse(
                message=content.strip(),
                exercises=exercises
            )

        except Exception as e:
            logger.error(f"Error getting AI coach response: {str(e)}", exc_info=True)
            raise

    async def _generate_exercises(self, pronunciation_history: List[dict]) -> List[Exercise]:
        """Generate targeted exercises based on pronunciation history."""
        try:
            # Find the sounds that need the most work
            problem_sounds = [
                hist["phoneme"] for hist in pronunciation_history 
                if hist.get("accuracy", 100) < 70
            ]

            if not problem_sounds:
                return []

            # Create prompt for exercise generation
            prompt = f"""Create 3 pronunciation exercises targeting these sounds: {', '.join(problem_sounds)}
            For each exercise, provide:
            1. A sentence or word focusing on the sound
            2. An explanation of the correct pronunciation
            3. The difficulty level (1-5)
            Format as JSON."""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a pronunciation exercise generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            # Parse the response and convert to Exercise objects
            content = response.choices[0].message['content']
            exercises_data = json.loads(content)
            
            exercises = []
            for ex in exercises_data:
                exercises.append(Exercise(
                    type=ex["type"],
                    content=ex["content"],
                    focus_sounds=ex["focus_sounds"],
                    difficulty=ex["difficulty"],
                    explanation=ex["explanation"]
                ))

            return exercises

        except Exception as e:
            logger.error(f"Error generating exercises: {str(e)}")
            return []

    def _extract_suggestions(self, content: str) -> List[str]:
        """Extract specific suggestions from the AI response."""
        try:
            # Use GPT to extract suggestions
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract specific pronunciation suggestions from this text. Return as a JSON array."},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            suggestions = json.loads(response.choices[0].message['content'])
            return suggestions

        except Exception as e:
            logger.error(f"Error extracting suggestions: {str(e)}")
            return []

    def _extract_focus_areas(self, content: str) -> List[str]:
        """Extract focus areas from the AI response."""
        try:
            # Use GPT to extract focus areas
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract specific pronunciation focus areas from this text. Return as a JSON array."},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            focus_areas = json.loads(response.choices[0].message['content'])
            return focus_areas

        except Exception as e:
            logger.error(f"Error extracting focus areas: {str(e)}")
            return []
