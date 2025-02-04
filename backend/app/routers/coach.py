from fastapi import APIRouter, File, Form, UploadFile, Depends
from typing import Dict, Optional, Any
import base64
from ..services.conversation import generate_initial_message, generate_response
from ..services.speech import transcribe_audio, generate_speech
import io
import wave
import struct
import ffmpeg
import os
import json
from app.services.pronunciation import generate_pronunciation_help, analyze_pronunciation
from app.schemas.conversation import PronunciationHelpRequest, ConversationRequest, HistoryMessage
import random

router = APIRouter(prefix="/api/coach", tags=["coach"])

@router.post("/start-conversation")
async def start_conversation_endpoint(
    language: str = Form(...), 
    accent: str = Form(...), 
    voice_name: str = Form('en-US-JennyNeural'),
    topic: Optional[str] = Form(None),
    is_kids_mode: bool = Form(False)
):
    try:
        # Validate language and accent
        if language not in ["en", "fr", "es", "ar", "it", "zh", "pt"]:
            return {
                "message": "",
                "audio": "",
                "topic": "",
                "topicName": "",
                "error": f"Unsupported language: {language}"
            }
        
        print(f"Start Conversation Debug - Input: language={language}, accent={accent}, voice_name={voice_name}, topic={topic}")
        
        # Determine the voice gender based on the voice name
        gender_mapping = {
            "en-US-GuyNeural": "male",
            "en-GB-RyanNeural": "male", 
            "en-AU-WilliamNeural": "male",
            "fr-FR-ClaudeNeural": "male",
            "fr-CA-JeanNeural": "male",
            "es-ES-AlvaroNeural": "male",
            "es-MX-JorgeNeural": "male",
            
            "en-US-JennyNeural": "female",
            "en-GB-LibbyNeural": "female",
            "en-AU-NatashaNeural": "female", 
            "fr-FR-DeniseNeural": "female",
            "fr-CA-SylvieNeural": "female",
            "es-ES-ElviraNeural": "female",
            "es-MX-DaliaNeural": "female"
        }
        
        # Get the gender from the voice name, default to 'female'
        gender = gender_mapping.get(voice_name, 'female')
        print(f"Determined gender: {gender}")
        
        # Mapping of language and accent to Azure language codes
        language_code_mapping = {
            'en': {
                'us': 'en-US',
                'neutral': 'en-US',
                'british': 'en-GB',
                'australian': 'en-AU'
            },
            'fr': {
                'neutral': 'fr-FR',
                'canadian': 'fr-CA'
            },
            'es': {
                'neutral': 'es-ES',
                'mexican': 'es-MX'
            },
            'ar': {
                'neutral': 'ar-EG',
                'eg': 'ar-EG',
                'sa': 'ar-SA'
            },
            'it': {
                'neutral': 'it-IT'
            },
            'zh': {
                'neutral': 'zh-CN'
            },
            'pt': {
                'neutral': 'pt-BR'
            }
        }
        
        # Get the correct language code
        language_code = language_code_mapping.get(language, {}).get(accent, f"{language}-{accent}")
        print(f"Using language code: {language_code}")
        
        # Language and accent mapping for more descriptive names
        language_accent_mapping = {
            'EN-US': {
                'language': 'American English',
                'accent': 'American accent'
            },
            'EN-GB': {
                'language': 'British English',
                'accent': 'British accent'
            },
            'EN-AU': {
                'language': 'Australian English',
                'accent': 'Australian accent'
            },
            'FR-FR': {
                'language': 'Français',
                'accent': 'accent français'
            },
            'FR-CA': {
                'language': 'Français',
                'accent': 'accent québécois'
            },
            'ES-ES': {
                'language': 'Español',
                'accent': 'acento español'
            },
            'ES-MX': {
                'language': 'Español',
                'accent': 'acento mexicano'
            },
            'AR-EG': {
                'language': 'Arabic',
                'accent': 'Egyptian accent'
            },
            'IT-IT': {
                'language': 'Italiano',
                'accent': 'Italian accent'
            },
            'ZH-CN': {
                'language': 'Mandarin Chinese',
                'accent': 'Chinese accent'
            },
            'PT-BR': {
                'language': 'Português',
                'accent': 'Brazilian accent'
            }
        }
        
        # Get the descriptive language and accent names
        language_details = language_accent_mapping.get(language_code.upper(), {
            'language': language_code,
            'accent': f'{language_code} accent'
        })
        
        print(f"Debug - Language Code: {language_code}")
        print(f"Debug - Language Details: {language_details}")
        print(f"Debug - Original Language: {language}")
        print(f"Debug - Original Accent: {accent}")
        
        if topic:
            from app.topics.manager import TopicManager
            topic_manager = TopicManager()
            print('heeehhehhhe',topic_manager,topic)
            selected_topic = topic_manager.get_topic(topic)
            if not selected_topic:
                print(f"Warning: Topic {topic} not found, falling back to random")
                initial_message_data = await generate_initial_message(
                    language=language, 
                    accent=accent, 
                    voice_gender=gender, 
                    topic_id=topic,
                    is_kids_mode=is_kids_mode
                )
            else:
                # Language-specific greetings and message structures
                # Determine the language base for prompt selection
                language_base = language_code[:2].lower()
                
                # Select the initial prompt based on language
                if isinstance(selected_topic.initial_prompt, dict):
                    initial_prompt = selected_topic.initial_prompt.get(language_base, 
                                                                       selected_topic.initial_prompt.get('en', 'Let\'s start a conversation'))
                else:
                    initial_prompt = selected_topic.initial_prompt
                
                # Select topic name based on language
                topic_name = selected_topic.name
                if isinstance(topic_name, dict):
                    # Use language-specific name or fallback to English
                    if language_base == 'fr':
                        topic_name = topic_name.get('fr', topic_name.get('en', 'Topic'))
                    elif language_base == 'es':
                        topic_name = topic_name.get('es', topic_name.get('en', 'Topic'))
                    else:  # Default to English
                        topic_name = topic_name.get('en', 'Topic')
                
                # Construct the message with language-specific topic name
                if language_base == 'fr':
                    message = (
                        f"Bonjour ! Je suis votre coach linguistique IA. "
                        f"Pratiquons votre {language_details['accent']} en {language_details['language']}. "
                        f"Aujourd'hui, nous allons parler de {topic_name}. {initial_prompt}"
                    )
                elif language_base == 'es':
                    message = (
                        f"¡Hola! Soy tu coach de idiomas IA. "
                        f"Practiquemos tu {language_details['accent']} en {language_details['language']}. "
                        f"Hoy hablaremos sobre {topic_name}. {initial_prompt}"
                    )
                else:  # Default to English
                    message = (
                        f"{'Hello' if gender == 'female' else 'Hey'} there! I'm your AI language coach. "
                        f"Let's practice your {language_details['accent']} in {language_details['language']}. "
                        f"Today, we'll talk about {topic_name}. {initial_prompt}"
                    )
                topic_id = selected_topic.id
                print('jkklfgkf',topic_id, topic)
                initial_message_data = {
                    "message": message,
                    "topic_id": topic_id,
                    "topic_name": topic_name,
                    "initial_history_message": None
                }
        else:
            initial_message_data = await generate_initial_message(
                language=language, 
                accent=accent, 
                voice_gender=gender, 
                topic_id=topic,
                is_kids_mode=is_kids_mode
            )
        
        message = initial_message_data["message"]
        topic_id = initial_message_data["topic_id"]
        topic_name = initial_message_data["topic_name"]
        initial_history_message = initial_message_data["initial_history_message"]
        
        # Add initial history message to conversation history
        conversation_history = []
        if initial_history_message:
            conversation_history.append(initial_history_message)
        
        print(f"Generated message: {message}")
        
        # Generate speech for initial message
        audio_file_path = await generate_speech(message, voice_name=voice_name)
        
        # Read the audio file and convert to base64
        with open(audio_file_path, 'rb') as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        
        # Return the response
        return {
            "message": message,
            "audio": audio_base64,
            "topic": topic_id,
            "topicName": topic_name
        }
        
    except Exception as e:
        print(f"Error starting conversation: {str(e)}")
        return {
            "message": "",
            "audio": "",
            "topic": "",
            "topicName": "",
            "error": f"Failed to start conversation: {str(e)}"
        }

@router.post("/transcribe")
async def transcribe_audio_endpoint(
    audio: UploadFile = File(...),
    language: str = Form(...),
    accent: str = Form(...)
):
    """Transcribe audio file"""
    try:
        print(f"Transcribing audio - language: {language}, accent: {accent}, audio: {audio.filename}")
        print(f"Audio content type: {audio.content_type}")
        
        # Read audio file
        audio_data = await audio.read()
        print(f"Audio data size: {len(audio_data)} bytes")
        
        # Convert audio to WAV
        wav_data = await convert_audio(audio_data)
        if not wav_data:
            print("Failed to convert audio to WAV")
            return {
                "transcription": "",
                "error": "Failed to convert audio"
            }
        
        # Mapping of language and accent to Azure language codes
        language_code_mapping = {
            'en': {
                'us': 'en-US',
                'neutral': 'en-US',
                'british': 'en-GB',
                'australian': 'en-AU'
            },
            'fr': {
                'neutral': 'fr-FR',
                'canadian': 'fr-CA'
            },
            'es': {
                'neutral': 'es-ES',
                'mexican': 'es-MX'
            },
            'ar': {
                'neutral': 'ar-EG',
                'eg': 'ar-EG',
                'sa': 'ar-SA'
            },
            'it': {
                'neutral': 'it-IT'
            },
            'zh': {
                'neutral': 'zh-CN'
            },
            'pt': {
                'neutral': 'pt-BR'
            }
        }
        
        # Get the correct language code
        language_code = language_code_mapping.get(language, {}).get(accent, f"{language}-{accent}")
        print(f"Using language code: {language_code}")
        
        # Transcribe audio
        transcription = await transcribe_audio(wav_data, language_code)
        
        # If transcription is a string (which shouldn't happen), convert to dict
        if isinstance(transcription, str):
            transcription = {
                "text": transcription,
                "confidence": "none"
            }
        
        # Check if transcription contains an error
        if 'error' in transcription:
            print(f"Transcription error: {transcription['error']}")
            return {
                "transcription": transcription.get('text', ''),
                "error": transcription['error']
            }
        
        # If no error, return transcription
        print(f"Transcribed text: {transcription}")
        return {
            "transcription": transcription.get('text', ''),
            "confidence": transcription.get('confidence', 'none')
        }
        
    except Exception as e:
        print(f"Unexpected error transcribing audio: {str(e)}")
        return {
            "transcription": "",
            "error": str(e)
        }

async def convert_audio(audio_data: bytes) -> Optional[bytes]:
    """Convert audio to WAV format using ffmpeg with audio preprocessing"""
    try:
        # Run ffmpeg to convert WebM to WAV with audio preprocessing
        process = (
            ffmpeg
            .input('pipe:0', format='webm')
            # Add audio filters for better speech recognition
            .filter('volume', '1.5')        # Slightly increase volume
            .filter('highpass', f='100')    # Remove very low frequencies
            .filter('lowpass', f='8000')    # Keep speech frequencies
            .filter('afftdn')               # Reduce noise
            .filter('dynaudnorm')           # Normalize audio levels
            # Set output format for Azure Speech Services
            .output(
                'pipe:1',
                format='wav',
                acodec='pcm_s16le',
                ac=1,              # Mono
                ar=16000,          # 16kHz
                loglevel='error'   # Reduce logging
            )
            .overwrite_output()
            .run_async(
                pipe_stdin=True,
                pipe_stdout=True,
                pipe_stderr=True
            )
        )
        
        try:
            # Write input data and get output
            stdout_data, stderr_data = process.communicate(input=audio_data)
            
            if process.returncode != 0:
                print(f"FFmpeg error: {stderr_data.decode() if stderr_data else 'Unknown error'}")
                raise ValueError("Failed to convert audio format")
            
            return stdout_data
            
        except Exception as e:
            print(f"Error during FFmpeg conversion: {str(e)}")
            if stderr_data:
                print(f"FFmpeg stderr: {stderr_data.decode()}")
            raise
            
    except Exception as e:
        print(f"Error converting audio: {str(e)}")
        return None

@router.post("/analyze-pronunciation")
async def analyze_pronunciation_endpoint(
    audio: UploadFile = File(...),
    language: str = Form(...),
    accent: str = Form(...),
    reference_text: str = Form(...),
    is_word_practice: str = Form(default="false")
):
    """Analyze pronunciation of audio file"""
    try:
        print("Pronunciation Analysis Endpoint Debug:")
        print(f"  Input Parameters:")
        print(f"    Language: {language}")
        print(f"    Accent: {accent}")
        print(f"    Reference Text: {reference_text}")
        print(f"    Is Word Practice: {is_word_practice}")
        
        # Mapping of language and accent to Azure language codes
        language_code_mapping = {
            'en': {
                'us': 'en-US',
                'neutral': 'en-US',
                'british': 'en-GB',
                'australian': 'en-AU'
            },
            'fr': {
                'neutral': 'fr-FR',
                'canadian': 'fr-CA'
            },
            'es': {
                'neutral': 'es-ES',
                'mexican': 'es-MX'
            },
            'ar': {
                'neutral': 'ar-EG',
                'eg': 'ar-EG',
                'sa': 'ar-SA'
            },
            'it': {
                'neutral': 'it-IT'
            },
            'zh': {
                'neutral': 'zh-CN'
            },
            'pt': {
                'neutral': 'pt-BR'
            }
        }
        
        # Get the correct language code
        language_code = language_code_mapping.get(language, {}).get(accent, f"{language}-{accent}")
        print(f"  Determined Language Code: {language_code}")
        
        # Read audio file
        audio_data = await audio.read()
        print(f"  Audio data size: {len(audio_data)} bytes")
        
        # Convert audio to WAV
        wav_data = await convert_audio(audio_data)
        if not wav_data:
            print("  Failed to convert audio to WAV")
            return {
                "pronunciation_feedback": "",
                "error": "Failed to convert audio"
            }
        
        # Analyze pronunciation
        pronunciation_feedback = await analyze_pronunciation(wav_data, reference_text, language_code, is_word_practice)
        
        if not pronunciation_feedback:
            print("  No pronunciation feedback generated")
            return {
                "pronunciation_feedback": "",
                "error": "No speech could be recognized. Please try speaking again."
            }
        
        print(f"  Pronunciation Feedback: {pronunciation_feedback}")
        return {
            "pronunciation_feedback": pronunciation_feedback
        }
        
    except Exception as e:
        print(f"Error analyzing pronunciation: {str(e)}")
        return {
            "pronunciation_feedback": "",
            "error": f"Failed to analyze pronunciation: {str(e)}"
        }

@router.post("/generate-response")
async def generate_response_endpoint(
    audio: UploadFile = File(...),
    text: Optional[str] = Form(None),
    language: str = Form(...), 
    accent: str = Form(...),
    voice_name: str = Form('en-US-JennyNeural'),
    topic_id: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    history: Optional[str] = Form(None),
    is_kids_mode: bool = Form(False)
):
    try:
        # First, transcribe the audio if text is not provided
        if not text:
            transcription_data = await transcribe_audio_endpoint(
                audio=audio, 
                language=language, 
                accent=accent
            )
            text = transcription_data.get('transcription', '')
            
            # Check if transcription is empty
            if not text.strip():
                return {
                    "error": "No speech detected. Please speak louder and more clearly."
                }
        
        # Parse history from JSON if provided
        parsed_history = []
        if history:
            try:
                history_data = json.loads(history)
                parsed_history = [
                    HistoryMessage(
                        text=msg.get('text', ''), 
                        isUser=msg.get('isUser', False),
                        topic_id=msg.get('topic_id')
                    ) for msg in history_data
                ]
            except json.JSONDecodeError:
                print("Failed to parse history JSON")
        
        # Determine topic_id (prefer topic_id over topic)
        print('tttdddtttdddtttdddtttdddtttdddtttdddtttddd',topic_id,topic)
        effective_topic_id = topic_id or topic
        
        # Add the current user message to history
        user_message = HistoryMessage(
            text=text, 
            isUser=True, 
            topic_id=effective_topic_id
        )
        parsed_history.append(user_message)
        
        # Generate AI response
        response = await generate_response(
            text, 
            language=language, 
            accent=accent, 
            voice_name=voice_name, 
            topic_id=effective_topic_id,
            history=parsed_history,
            is_kids_mode=is_kids_mode
        )
        
        # Add AI response to history
        ai_message = HistoryMessage(
            text=response['message'], 
            isUser=False, 
            topic_id=effective_topic_id
        )
        parsed_history.append(ai_message)
        
        # Convert history back to JSON for frontend
        history_json = json.dumps([
            {
                'text': msg.text, 
                'isUser': msg.isUser, 
                'topic_id': msg.topic_id
            } for msg in parsed_history
        ])
        
        return {
            **response,
            'transcribed_text': text,
            'history': history_json,
            'topic_id': effective_topic_id
        }
    except Exception as e:
        print(f"Error in generate_response_endpoint: {str(e)}")
        return {"error": str(e)}

@router.post("/generate-speech")
async def generate_speech_endpoint(
    text: str = Form(...),
    language: str = Form(default="en"),
    accent: str = Form(default="neutral"),
    voice_name: Optional[str] = Form(None)
):
    """Generate speech from text for a given language and accent"""
    try:
        # Determine voice name based on language and accent
        voice_mapping = {
            "en": {
                "neutral": {
                    "male": "en-US-GuyNeural",
                    "female": "en-US-JennyNeural"
                },
                "british": {
                    "male": "en-GB-RyanNeural", 
                    "female": "en-GB-LibbyNeural"
                },
                "australian": {
                    "male": "en-AU-WilliamNeural",
                    "female": "en-AU-NatashaNeural"
                }
            },
            "fr": {
                "neutral": {
                    "male": "fr-FR-ClaudeNeural",
                    "female": "fr-FR-DeniseNeural"
                },
                "canadian": {
                    "male": "fr-CA-JeanNeural",
                    "female": "fr-CA-SylvieNeural"
                }
            },
            "es": {
                "neutral": {
                    "male": "es-ES-AlvaroNeural",
                    "female": "es-ES-ElviraNeural"
                },
                "mexican": {
                    "male": "es-MX-JorgeNeural",
                    "female": "es-MX-DaliaNeural"
                }
            },
            "ar": {
                "neutral": {
                    "male": "ar-EG-AhmedNeural",
                    "female": "ar-EG-NouraNeural"
                }
            },
            "it": {
                "neutral": {
                    "male": "it-IT-FrancescoNeural",
                    "female": "it-IT-IsabellaNeural"
                }
            },
            "zh": {
                "neutral": {
                    "male": "zh-CN-YunyangNeural",
                    "female": "zh-CN-XiaoxiaoNeural"
                }
            },
            "pt": {
                "neutral": {
                    "male": "pt-BR-AntonioNeural",
                    "female": "pt-BR-FranciscaNeural"
                }
            }
        }
        
        # If voice_name is an accent or gender, convert it to the correct neural voice
        if voice_name in ["neutral", "british", "australian", "canadian", "mexican", "male", "female"]:
            # Extract gender from voice_name if possible, otherwise default to female
            gender = "female"
            if voice_name in ["male", "female"]:
                gender = voice_name
            
            # Get the voice based on language, accent, and gender
            voice_name = voice_mapping.get(language, {}).get(accent, {}).get(gender, "en-US-JennyNeural")
        
        print(f'Voice Mapping Debug: language={language}, accent={accent}, voice_name={voice_name}')
        print(f'Full Voice Mapping: {json.dumps(voice_mapping, indent=2)}')
        
        print(f'Final voice name: {voice_name}')
        
        # Generate speech
        audio_file_path = await generate_speech(text, voice_name=voice_name)
        
        # Read the audio file and convert to base64
        if audio_file_path and os.path.exists(audio_file_path):
            with open(audio_file_path, 'rb') as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
            
            # Clean up the temporary file
            os.unlink(audio_file_path)
            
            return {
                "audio": audio_base64,
                "voice_name": voice_name
            }
        else:
            return {
                "audio": "",
                "voice_name": voice_name,
                "error": "Failed to generate speech"
            }
    
    except Exception as e:
        print(f"Error in generate_speech_endpoint: {str(e)}")
        return {
            "audio": "",
            "voice_name": "",
            "error": f"Speech generation error: {str(e)}"
        }

@router.post("/pronunciation-help")
def get_pronunciation_help(request: PronunciationHelpRequest):
    """
    Generate detailed pronunciation help for words with poor pronunciation
    """
    try:
        # Default to English US and neutral accent if not provided
        language = request.language or 'en-US'
        accent = request.accent or 'neutral'
        
        print('testqk',language,accent)
        
        pronunciation_help = generate_pronunciation_help(
            request.poor_words, 
            language=language, 
            accent=accent
        )
        
        return {
            "success": True,
            "pronunciation_help": pronunciation_help
        }
    except Exception as e:
        print(f"Error in pronunciation help endpoint: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def generate_initial_message(
    language: str, 
    accent: str, 
    voice_gender: str, 
    topic_id: Optional[str] = None,
    is_kids_mode: bool = False
) -> Dict[str, Any]:
    """
    Generate an initial conversation message based on the selected topic
    
    Args:
        language (str): Language of the conversation
        accent (str): Accent for the conversation
        voice_gender (str): Voice gender for the conversation
        topic_id (Optional[str]): Specific topic ID or 'random'
        is_kids_mode (bool): Whether to use kids mode
    
    Returns:
        Dict containing initial message details
    """
    # Define all available topics
    kids_topics = [
        'animals',
        'superheroes',
        'fairy_tales',
        'space_adventure',
        'dinosaurs',
        'magic_school',
        'pirates',
        'jungle_safari',
        'underwater_world',
        'cartoon_characters'
    ] if is_kids_mode else []
    
    all_topics = kids_topics if is_kids_mode else [
        'hobbies', 
        'travel', 
        'food', 
        'movies', 
        'role_play', 
        'everyday_situations', 
        'debates', 
        'current_events', 
        'personal_growth'
    ]
    
    # Validate and normalize topic_id
    if not topic_id or topic_id.lower() == 'random':
        topic_id = random.choice(all_topics)
    
    # Ensure topic_id is in the list of available topics
    if topic_id not in all_topics:
        print(f"Warning: Topic {topic_id} not found, falling back to random")
        topic_id = random.choice(all_topics)
    
    # Mapping of language and accent to Azure language codes
    language_code_mapping = {
        'en': {
            'us': 'en-US',
            'neutral': 'en-US',
            'british': 'en-GB',
            'gb': 'en-GB',
            'australian': 'en-AU',
            'au': 'en-AU'
        },
        'fr': {
            'neutral': 'fr-FR',
            'canadian': 'fr-CA'
        },
        'es': {
            'neutral': 'es-ES',
            'mexican': 'es-MX'
        },
        'ar': {
            'neutral': 'ar-EG',
            'eg': 'ar-EG',
            'sa': 'ar-SA'
        },
        'it': {
            'neutral': 'it-IT'
        },
        'zh': {
            'neutral': 'zh-CN'
        },
        'pt': {
            'neutral': 'pt-BR'
        }
    }
    
    # Get the correct language code
    language_code = language_code_mapping.get(language, {}).get(accent, f"{language}-{accent}")
    
    # Fallback if language code is not found
    if language_code == f"{language}-{accent}":
        print(f"Warning: Language code not found for language={language}, accent={accent}")
        # Use a default mapping
        if language == 'en':
            language_code = 'en-US'
        elif language == 'fr':
            language_code = 'fr-FR'
        elif language == 'es':
            language_code = 'es-ES'
        elif language == 'ar':
            language_code = 'ar-EG'
        elif language == 'it':
            language_code = 'it-IT'
        elif language == 'zh':
            language_code = 'zh-CN'
        elif language == 'pt':
            language_code = 'pt-BR'
        
    # Language and accent mapping for more descriptive names
    language_accent_mapping = {
        'EN-US': {
            'language': 'American English',
            'accent': 'American accent'
        },
        'EN-GB': {
            'language': 'British English',
            'accent': 'British accent'
        },
        'EN-AU': {
            'language': 'Australian English',
            'accent': 'Australian accent'
        },
        'FR-FR': {
            'language': 'Français',
            'accent': 'accent parisien'
        },
        'FR-CA': {
            'language': 'Français',
            'accent': 'accent québécois'
        },
        'ES-ES': {
            'language': 'Español',
            'accent': 'acento español'
        },
        'ES-MX': {
            'language': 'Español',
            'accent': 'acento mexicano'
        },
         'ES-AR': {
            'language': 'Español',
            'accent': 'acento argentino'
        },
        'AR-EG': {
            'language': 'Arabic',
            'accent': 'Egyptian accent'
        },
        'IT-IT': {
            'language': 'Italiano',
            'accent': 'Italian accent'
        },
        'ZH-CN': {
            'language': 'Mandarin Chinese',
            'accent': 'Chinese accent'
        },
        'PT-BR': {
            'language': 'Português',
            'accent': 'Brazilian accent'
        }
    }
    
    language_code = f"{language}-{accent}"

    # Get language details
    language_code = language_code.upper()  # Convert to uppercase for consistent matching
    language_details = language_accent_mapping.get(language_code, {
        'language': language_code,
        'accent': f'{language_code} accent'
    })
    
    # Mapping of topics to their initial prompts
    kids_prompts = {
        'en': {
            'animals': "Hey there! Let's talk about your favorite animals! Do you have any pets? What's your favorite animal at the zoo?",
            'superheroes': "Wow! Let's talk about superheroes! Who's your favorite superhero? What super power would you like to have?",
            'fairy_tales': "Welcome to the magical world of fairy tales! What's your favorite story? Would you like to tell me about your favorite character?",
            'space_adventure': "3... 2... 1... Blast off! We're going on a space adventure! Have you ever wondered what it's like to be an astronaut?",
            'dinosaurs': "Roar! Let's explore the world of dinosaurs! Which dinosaur do you think is the coolest? Do you know any fun dinosaur facts?",
            'magic_school': "Welcome to the School of Magic! What kind of magical spells would you like to learn? What's your favorite magical creature?",
            'pirates': "Ahoy, matey! Ready for a pirate adventure? What would you name your pirate ship? Where should we sail to first?",
            'jungle_safari': "Welcome to the jungle! What amazing animals do you think we'll see on our safari? Can you hear the sounds of the jungle?",
            'underwater_world': "Dive in! We're exploring the ocean today! What sea creatures would you like to meet? Have you ever seen a real dolphin?",
            'cartoon_characters': "Hi! I'm Mortelle Adele, your favorite cartoon character! I love making jokes and having fun adventures with my cat Ajax. What would you like to talk about? We can chat about my funny stories or anything else you'd like!"
        }
    }
    
    topic_prompts = kids_prompts if is_kids_mode else {
        'en': {
            'hobbies': "Let's talk about hobbies! What do you enjoy doing in your free time?",
            'travel': "Tell me about your favorite travel experiences or dream destinations.",
            'food': "What's your favorite cuisine? Do you enjoy cooking?",
            'movies': "What kind of movies do you enjoy watching? Any recent favorites?",
            'role_play': "Let's practice a conversation scenario. Imagine we're meeting for the first time.",
            'everyday_situations': "Tell me about a typical day in your life.",
            'debates': "What's an interesting topic you'd like to discuss or debate?",
            'current_events': "What recent news or current event has caught your attention?",
            'personal_growth': "What personal goals are you working on right now?"
        },
        'fr': {
            'hobbies': "Parlons de vos loisirs ! Qu'aimez-vous faire pendant votre temps libre ?",
            'travel': "Parlez-moi de vos expériences de voyage préférées ou de vos destinations de rêve.",
            'food': "Quelle est votre cuisine préférée ? Aimez-vous cuisiner ?",
            'movies': "Quel type de films aimez-vous regarder ? Des films récents préférés ?",
            'role_play': "Pratiquons un scénario de conversation. Imaginons que nous nous rencontrons pour la première fois.",
            'everyday_situations': "Parlez-moi d'une journée typique de votre vie.",
            'debates': "Quel est un sujet intéressant dont vous aimeriez discuter ou débattre ?",
            'current_events': "Quelle actualité récente a retenu votre attention ?",
            'personal_growth': "Sur quels objectifs personnels travaillez-vous actuellement ?"
        },
        'es': {
            'hobbies': "¡Hablemos de pasatiempos! ¿Qué te gusta hacer en tu tiempo libre?",
            'travel': "Cuéntame sobre tus experiencias de viaje favoritas o destinos soñados.",
            'food': "¿Cuál es tu comida favorita? ¿Te gusta cocinar?",
            'movies': "¿Qué tipo de películas te gusta ver? ¿Alguna favorita reciente?",
            'role_play': "Practiquemos un escenario de conversación. Imaginemos que nos estamos conociendo por primera vez.",
            'everyday_situations': "Cuéntame sobre un día típico en tu vida.",
            'debates': "¿Cuál es un tema interesante del que te gustaría discutir o debatir?",
            'current_events': "¿Qué noticia o evento actual ha llamado tu atención?",
            'personal_growth': "¿En qué metas personales estás trabajando actualmente?"
        },
        'ar': {
            'hobbies': "ما هي هواياتك المفضلة؟",
            'travel': "حدثني عن تجارب السفر المفضلة لديك أو الوجهات التي تحلم بها.",
            'food': "ما هي طعامك المفضل؟ هل تحب الطبخ؟",
            'movies': "ما هو نوع الأفلام التي تحب مشاهدة؟ هل هناك أفلام حديثة مفضلة؟",
            'role_play': "دعونا نتدرب على سيناريو محادثة. تخيل أننا نلتقي لأول مرة.",
            'everyday_situations': "حدثني عن يومك العادي.",
            'debates': "ما هو الموضوع المثير الذي تود مناقشته أو مناقشته؟",
            'current_events': "ما هي الأخبار أو الأحداث الحالية التي لفتت انتباهك؟",
            'personal_growth': "ما هي الأهداف الشخصية التي تعمل عليها حاليًا؟"
        },
        'it': {
            'hobbies': "Di cosa ti piace parlare? Quali sono i tuoi hobby preferiti?",
            'travel': "Raccontami delle tue esperienze di viaggio preferite o delle destinazioni che sogni.",
            'food': "Qual è il tuo cibo preferito? Ti piace cucinare?",
            'movies': "Che tipo di film ti piace guardare? Ci sono film recenti preferiti?",
            'role_play': "Praticiamo uno scenario di conversazione. Immaginiamo di incontrarci per la prima volta.",
            'everyday_situations': "Raccontami di una giornata tipo nella tua vita.",
            'debates': "Qual è un argomento interessante di cui ti piacerebbe discutere o dibattere?",
            'current_events': "Qual è l'ultima notizia o evento che ha attirato la tua attenzione?",
            'personal_growth': "Su quali obiettivi personali stai lavorando attualmente?"
        },
        'zh': {
            'hobbies': "你喜欢做什么？",
            'travel': "告诉我你最喜欢的旅行经历或梦想中的目的地。",
            'food': "你最喜欢的食物是什么？你喜欢烹饪吗？",
            'movies': "你喜欢看什么类型的电影？最近有什么喜欢的电影吗？",
            'role_play': "我们来练习一个对话场景。想象我们第一次见面。",
            'everyday_situations': "告诉我你的一天。",
            'debates': "你想讨论或辩论什么有趣的话题？",
            'current_events': "最近有什么新闻或事件吸引了你的注意？",
            'personal_growth': "你目前正在努力实现什么个人目标？"
        },
        'pt': {
            'hobbies': "Do que você gosta de falar? Quais são seus hobbies preferidos?",
            'travel': "Conte-me sobre suas experiências de viagem preferidas ou destinos que você sonha.",
            'food': "Qual é sua comida preferida? Você gosta de cozinhar?",
            'movies': "Que tipo de filmes você gosta de assistir? Há filmes recentes preferidos?",
            'role_play': "Vamos praticar um cenário de conversa. Imaginemos que estamos nos conhecendo pela primeira vez.",
            'everyday_situations': "Conte-me sobre um dia típico na sua vida.",
            'debates': "Qual é um assunto interessante que você gostaria de discutir ou debater?",
            'current_events': "Qual é a última notícia ou evento que chamou sua atenção?",
            'personal_growth': "Em quais objetivos pessoais você está trabalhando atualmente?"
        }
    }
    
    # Get the initial prompt for the selected topic
    initial_prompt = topic_prompts.get(language, topic_prompts['en']).get(topic_id, "Let's start a conversation!")
    
    # Get the translated topic name
    topic_name_translations = {
        'en': {
            'hobbies': 'hobbies',
            'travel': 'travel',
            'food': 'food',
            'movies': 'movies',
            'role_play': 'role play',
            'everyday_situations': 'everyday situations',
            'debates': 'debates',
            'current_events': 'current events',
            'personal_growth': 'personal growth',
            'animals': 'animals',
            'superheroes': 'superheroes',
            'fairy_tales': 'fairy tales',
            'space_adventure': 'space adventure',
            'dinosaurs': 'dinosaurs',
            'magic_school': 'magic school',
            'pirates': 'pirates',
            'jungle_safari': 'jungle safari',
            'underwater_world': 'underwater world',
            'cartoon_characters': 'cartoon characters'
        },
        'fr': {
            'hobbies': 'loisirs',
            'travel': 'voyage',
            'food': 'cuisine',
            'movies': 'films',
            'role_play': 'jeu de rôle',
            'everyday_situations': 'situations quotidiennes',
            'debates': 'débats',
            'current_events': 'actualités',
            'personal_growth': 'développement personnel',
            'animals': 'animaux',
            'superheroes': 'superhéros',
            'fairy_tales': 'contes de fées',
            'space_adventure': 'aventure spatiale',
            'dinosaurs': 'dinosaures',
            'magic_school': 'école de magie',
            'pirates': 'pirates',
            'jungle_safari': 'safari en jungle',
            'underwater_world': 'monde sous-marin',
            'cartoon_characters': 'personnages de dessins animés'
        },
        'es': {
            'hobbies': 'pasatiempos',
            'travel': 'viaje',
            'food': 'comida',
            'movies': 'películas',
            'role_play': 'juego de roles',
            'everyday_situations': 'situaciones cotidianas',
            'debates': 'debates',
            'current_events': 'eventos actuales',
            'personal_growth': 'crecimiento personal',
            'animals': 'animales',
            'superheroes': 'superhéroes',
            'fairy_tales': 'cuentos de hadas',
            'space_adventure': 'aventura espacial',
            'dinosaurs': 'dinosaurios',
            'magic_school': 'escuela de magia',
            'pirates': 'piratas',
            'jungle_safari': 'safari en la jungla',
            'underwater_world': 'mundo submarino',
            'cartoon_characters': 'personajes de dibujos animados'
        },
        'ar': {
            'hobbies': 'هوايات',
            'travel': 'سفر',
            'food': 'طعام',
            'movies': 'أفلام',
            'role_play': 'تمثيل أدوار',
            'everyday_situations': 'حالات يومية',
            'debates': 'مناقشات',
            'current_events': 'أحداث حالية',
            'personal_growth': 'نمو شخصي',
            'animals': 'حيوانات',
            'superheroes': 'أبطال خارقون',
            'fairy_tales': 'قصص خرافية',
            'space_adventure': 'مغامرة فضائية',
            'dinosaurs': 'ديناصورات',
            'magic_school': 'مدرسة سحرية',
            'pirates': 'قراصنة',
            'jungle_safari': 'سفاري في الغابة',
            'underwater_world': 'عالم تحت الماء',
            'cartoon_characters': 'شخصيات كرتونية'
        },
        'it': {
            'hobbies': 'hobby',
            'travel': 'viaggio',
            'food': 'cibo',
            'movies': 'film',
            'role_play': 'gioco di ruolo',
            'everyday_situations': 'situazioni quotidiane',
            'debates': 'dibattiti',
            'current_events': 'eventi attuali',
            'personal_growth': 'crescita personale',
            'animals': 'animali',
            'superheroes': 'supereroi',
            'fairy_tales': 'fiabe',
            'space_adventure': 'avventura spaziale',
            'dinosaurs': 'dinosauri',
            'magic_school': 'scuola di magia',
            'pirates': 'pirati',
            'jungle_safari': 'safari nella giungla',
            'underwater_world': 'mondo sottomarino',
            'cartoon_characters': 'personaggi dei cartoni animati'
        },
        'zh': {
            'hobbies': '兴趣爱好',
            'travel': '旅行',
            'food': '食物',
            'movies': '电影',
            'role_play': '角色扮演',
            'everyday_situations': '日常情况',
            'debates': '辩论',
            'current_events': '当前事件',
            'personal_growth': '个人成长',
            'animals': '动物',
            'superheroes': '超级英雄',
            'fairy_tales': '童话',
            'space_adventure': '太空冒险',
            'dinosaurs': '恐龙',
            'magic_school': '魔法学校',
            'pirates': '海盗',
            'jungle_safari': '丛林探险',
            'underwater_world': '水下世界',
            'cartoon_characters': '卡通人物'
        },
        'pt': {
            'hobbies': 'hobbies',
            'travel': 'viagem',
            'food': 'comida',
            'movies': 'filmes',
            'role_play': 'jogo de papéis',
            'everyday_situations': 'situações do dia a dia',
            'debates': 'debates',
            'current_events': 'eventos atuais',
            'personal_growth': 'crescimento pessoal',
            'animals': 'animais',
            'superheroes': 'super-heróis',
            'fairy_tales': 'contos de fadas',
            'space_adventure': 'aventura espacial',
            'dinosaurs': 'dinossauros',
            'magic_school': 'escola de magia',
            'pirates': 'piratas',
            'jungle_safari': 'safari na selva',
            'underwater_world': 'mundo subaquático',
            'cartoon_characters': 'personagens de desenhos animados'
        }
    }
    
    # Get the translated topic name
    topic_name = topic_name_translations.get(language, topic_name_translations['en']).get(topic_id, topic_id.replace('_', ' ').title())
    
    # Construct the message with language-specific details
    if language == 'fr':
        message = (
            f"Bonjour ! Je suis votre coach linguistique IA. "
            f"Pratiquons votre {language_details['accent']} en {language_details['language']}. "
            f"Aujourd'hui, nous allons parler de {topic_name}. {initial_prompt}"
        )
    elif language == 'es':
        message = (
            f"¡Hola! Soy tu coach de idiomas IA. "
            f"Practiquemos tu {language_details['accent']} en {language_details['language']}. "
            f"Hoy hablaremos sobre {topic_name}. {initial_prompt}"
        )
    elif language == 'ar':
        message = (
            f"مرحبا! أنا مدربك اللغوي IA. "
            f"دعونا نتدرب على {language_details['accent']} في {language_details['language']}. "
            f"اليوم، سنتحدث عن {topic_name}. {initial_prompt}"
        )
    elif language == 'it':
        message = (
            f"Ciao! Sono il tuo coach linguistico IA. "
            f"Praticiamo il tuo {language_details['accent']} in {language_details['language']}. "
            f"Oggi parleremo di {topic_name}. {initial_prompt}"
        )
    elif language == 'zh':
        message = (
            f"你好! 我是你的语言教练 IA. "
            f"我们来练习你的 {language_details['accent']} 在 {language_details['language']}. "
            f"今天，我们将讨论 {topic_name}. {initial_prompt}"
        )
    elif language == 'pt':
        message = (
            f"Olá! Sou seu treinador de idiomas IA. "
            f"Vamos praticar seu {language_details['accent']} em {language_details['language']}. "
            f"Hoje, vamos falar sobre {topic_name}. {initial_prompt}"
        )
    else:  # Default to English
        message = (
            f"{'Hello' if voice_gender == 'female' else 'Hey'} there! I'm your AI language coach. "
            f"Let's practice your {language_details['accent']} in {language_details['language']}. "
            f"Today, we'll talk about {topic_name}. {initial_prompt}"
        )
    
    # Return the initial message details
    return {
        "topic_id": topic_id,
        "topic_name": topic_name,
        "message": message,
        "initial_history_message": None
    }
