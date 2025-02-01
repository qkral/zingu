import os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import asyncio
import tempfile
import wave
import io
import logging
from fastapi import HTTPException

# Load environment variables
load_dotenv()

# Configure Azure Speech Service
speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION")

if not speech_key or not service_region:
    raise ValueError("Azure Speech credentials not found in environment variables")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_azure_language_code(language: str, accent: str) -> str:
    """
    Convert language and accent to Azure-compatible language code
    """
    # Default mappings for supported languages and accents
    language_mappings = {
        "en": {
            "us": "en-US",
            "uk": "en-GB",
            "au": "en-AU",
            "ca": "en-CA",
            "in": "en-IN",
            "default": "en-US"
        },
        "fr": {
            "fr": "fr-FR",
            "ca": "fr-CA",
            "ch": "fr-CH",
            "default": "fr-FR"
        },
        "es": {
            "es": "es-ES",
            "mx": "es-MX",
            "ar": "es-AR",
            "default": "es-ES"
        },
        "default": "en-US"
    }

    # Clean and normalize input
    language = language.lower().strip()
    accent = accent.lower().strip()
    
    # Extract language code if it's in format "en-US"
    if "-" in language:
        return language
        
    # Extract country code if accent is in format "en-US"
    if "-" in accent:
        return accent

    # Get language mapping
    language_map = language_mappings.get(language, language_mappings["default"])
    
    # Get specific accent or default for the language
    if isinstance(language_map, dict):
        return language_map.get(accent, language_map["default"])
    
    return language_map

async def convert_speech_to_text(audio_data: bytes, language: str = "en-US", accent: str = "us") -> str:
    """
    Convert speech to text using Azure Speech Services
    """
    temp_file_path = None
    try:
        # Get proper language code for Azure
        azure_language_code = get_azure_language_code(language, accent)
        logger.info(f"Starting speech-to-text conversion. Audio data size: {len(audio_data)} bytes")
        logger.info(f"Using language code: {azure_language_code}")
        
        # Create a temporary WAV file with proper format
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file_path = temp_file.name
            logger.debug(f"Created temporary file: {temp_file_path}")
            
            # Ensure the WAV file has the correct format
            with wave.open(temp_file.name, 'wb') as wav_file:
                # Set WAV file parameters for optimal speech recognition
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # 16kHz
                
                # If input is already WAV, extract PCM data
                try:
                    with wave.open(io.BytesIO(audio_data), 'rb') as wav_in:
                        logger.debug("Input is WAV format, reading frames...")
                        frames = wav_in.readframes(wav_in.getnframes())
                        wav_file.writeframes(frames)
                        logger.debug(f"WAV properties - channels: {wav_in.getnchannels()}, framerate: {wav_in.getframerate()}, sampwidth: {wav_in.getsampwidth()}")
                except Exception as e:
                    logger.warning(f"Error reading input WAV, treating as raw audio: {str(e)}")
                    wav_file.writeframes(audio_data)
        
        # Create speech config with the specified language
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=service_region
        )
        speech_config.speech_recognition_language = azure_language_code
        
        # Create audio config
        audio_stream = speechsdk.audio.PushAudioInputStream()
        audio_stream.write(audio_data)
        audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
        
        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # Set up result future
        result_future = []
        
        def handle_result(evt):
            """Handle speech recognition result"""
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                result_future.append(evt.result.text)
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                if evt.result.no_match_details.reason == speechsdk.NoMatchReason.InitialSilenceTimeout:
                    raise ValueError("No speech detected. Please try speaking again.")
                elif evt.result.no_match_details.reason == speechsdk.NoMatchReason.NoMatch:
                    raise ValueError("Could not understand the speech. Please try speaking more clearly.")
            
        def handle_canceled(evt):
            """Handle speech recognition cancellation"""
            if evt.result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = evt.result.cancellation_details
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    raise ValueError(f"Speech recognition error: {cancellation_details.error_details}")
        
        # Connect callbacks
        speech_recognizer.recognized.connect(handle_result)
        speech_recognizer.canceled.connect(handle_canceled)
        
        # Start recognition
        speech_recognizer.start_continuous_recognition()
        
        # Wait for result (with timeout)
        try:
            # Wait up to 10 seconds for recognition
            await asyncio.sleep(10)
        finally:
            speech_recognizer.stop_continuous_recognition()
        
        # Check results
        if not result_future:
            raise ValueError("No speech detected. Please try speaking again.")
        
        return result_future[0]
        
    except Exception as e:
        logger.error(f"Speech-to-text error: {str(e)}")
        if "No speech detected" in str(e):
            raise ValueError("No speech detected. Please try speaking again.")
        elif "Could not understand" in str(e):
            raise ValueError("Could not understand the speech. Please try speaking more clearly.")
        else:
            raise ValueError(f"Speech recognition error: {str(e)}")
        
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Deleted temporary file: {temp_file_path}")
            except Exception as e:
                logger.error(f"Error deleting temporary file: {str(e)}")
