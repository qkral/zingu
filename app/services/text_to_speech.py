import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv
from fastapi import HTTPException
import tempfile

# Load environment variables
load_dotenv()

def get_speech_config():
    """Get Azure speech config with API key and region"""
    try:
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        service_region = os.getenv("AZURE_SPEECH_REGION", "eastus")
        
        if not speech_key:
            raise ValueError("Azure Speech API key not found")
            
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=service_region
        )
        return speech_config
    except Exception as e:
        print(f"Error getting speech config: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Speech service configuration error: {str(e)}"
        )

async def convert_text_to_speech(text: str, voice_name: str) -> bytes:
    """Convert text to speech using Azure Speech Services"""
    try:
        print(f"Converting text to speech with voice: {voice_name}")  # Debug log
        speech_config = get_speech_config()
        
        # Extract language code from voice name (e.g., "fr-FR-DeniseNeural" -> "fr-FR")
        language_code = "-".join(voice_name.split('-')[:2])
        print(f"Using language code: {language_code}")  # Debug log
        
        # Create a temp file for the audio output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            audio_config = speechsdk.audio.AudioOutputConfig(
                filename=temp_file.name
            )
            
            # Create the synthesizer
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            
            # Set SSML with explicit language and voice settings
            ssml_text = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{language_code}">
                <voice name="{voice_name}">
                    <prosody rate="0.9">
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            print(f"SSML: {ssml_text}")  # Debug log
            
            # Synthesize speech
            result = speech_synthesizer.speak_ssml_async(ssml_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Read the audio file
                with open(temp_file.name, "rb") as audio_file:
                    audio_data = audio_file.read()
                return audio_data
            else:
                error_details = result.properties.get(
                    speechsdk.PropertyId.SpeechServiceResponse_JsonErrorDetails
                )
                raise Exception(
                    f"Speech synthesis failed: {result.reason} {error_details}"
                )
                
    except Exception as e:
        print(f"Error converting text to speech: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Text to speech conversion failed: {str(e)}"
        )
        
    finally:
        # Clean up the temp file
        if 'temp_file' in locals():
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                print(f"Error deleting temp file: {str(e)}")
