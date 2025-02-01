import azure.cognitiveservices.speech as speechsdk
import os
from typing import Optional
from dotenv import load_dotenv
import traceback
import asyncio
import tempfile
import time

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
        raise Exception(f"Speech service configuration error: {str(e)}")

async def transcribe_audio(audio_data, language):
    """
    Transcribe audio using Azure Speech-to-Text with continuous recognition
    
    Args:
        audio_data (bytes): Audio data to transcribe
        language (str): Language for transcription
    
    Returns:
        str: Transcribed text
    """
    try:
        # Create speech configuration
        speech_config = speechsdk.SpeechConfig(
            subscription=os.getenv('AZURE_SPEECH_KEY'),
            region=os.getenv('AZURE_SPEECH_REGION')
        )
        print('languageeee',language)
        # Set recognition language
        speech_config.speech_recognition_language = language
        
        # Configure recognition settings for very long pauses
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
            "300000"  # 5 minutes initial silence timeout
        )
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
            "300000"  # 5 minutes end silence timeout
        )
        
        # Create push stream for audio input
        push_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.AudioConfig(stream=push_stream)
        
        # Create speech recognizer
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        
        # Event to signal completion
        recognition_done = asyncio.Event()
        
        # Thread-safe list to collect transcription results
        transcription_results = []
        
        # Event handler for recognized speech
        def handle_recognized(evt):
            if evt.result.text.strip():
                transcription_results.append(evt.result.text.strip())
        
        # Event handler to mark recognition as complete
        def stop_cb(evt):
            print(f'Recognition stopped: {evt}')
            recognition_done.set()
        
        # Connect event handlers
        recognizer.recognized.connect(handle_recognized)
        recognizer.session_stopped.connect(stop_cb)
        recognizer.canceled.connect(stop_cb)
        
        # Start continuous recognition
        recognizer.start_continuous_recognition()
        
        # Write audio data to push stream
        push_stream.write(audio_data)
        push_stream.close()
        
        # Wait for recognition to complete with timeout
        try:
            await asyncio.wait_for(recognition_done.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            print("Recognition timed out")
        
        # Stop continuous recognition
        recognizer.stop_continuous_recognition()
        
        # Combine and return full transcription
        full_text = " ".join(transcription_results)
        return full_text if full_text.strip() else ""
    
    except Exception as e:
        print(f"Error in transcribe_audio: {str(e)}")
        return ""

async def generate_speech(text: str, voice_name: str = "en-US-JennyNeural") -> Optional[str]:
    """Generate speech from text using Azure TTS, return path to audio file"""
    try:
        speech_config = get_speech_config()
        if not speech_config:
            return None
        
        # Set voice name
        speech_config.speech_synthesis_voice_name = voice_name
        
        # Create a more persistent temporary file for audio output
        temp_file_path = os.path.join(tempfile.gettempdir(), f"speech_{os.getpid()}_{id(text)}.wav")
        
        # Create audio output config with temporary file
        audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_file_path)
        
        # Create speech synthesizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, 
            audio_config=audio_config
        )
        
        print('Starting synthesis',voice_name)
        # Synthesize speech to file
        result = speech_synthesizer.speak_text_async(text).get()
        print('Synthesis completed',speech_config)
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f'Synthesis successful. Audio saved to {temp_file_path}')
            # Verify file exists and has content
            if os.path.exists(temp_file_path):
                file_size = os.path.getsize(temp_file_path)
                print(f'Audio file size: {file_size} bytes')
                if file_size > 0:
                    return temp_file_path
                else:
                    print('Audio file is empty')
            else:
                print('Audio file was not created')
            return None
        else:
            # Clean up the temporary file if synthesis fails
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            #error_details = result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonErrorDetails)
            print(f"Speech synthesis failed: {result.reason}")
            #if error_details:
                #print(f"Error details: {error_details}")
            return None
            
    except Exception as e:
        print(f"Error generating speech: {str(e)}")
        traceback.print_exc()
        return None
