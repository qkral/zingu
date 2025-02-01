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

def diagnose_azure_speech_sdk():
    """Comprehensive diagnostic function for Azure Speech SDK"""
    import sys
    import platform
    import ctypes
    import os
    
    # System and Python information
    print("Comprehensive Azure Speech SDK Diagnostics:")
    print("=" * 50)
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Machine: {platform.machine()}")
    print(f"Architecture: {platform.architecture()}")
    
    # Environment variables
    print("\nEnvironment Variables:")
    print("-" * 50)
    azure_vars = {k: v for k, v in os.environ.items() if 'AZURE' in k or 'SPEECH' in k}
    for key, value in azure_vars.items():
        print(f"{key}: {'*' * len(str(value)) if value else 'Not Set'}")
    
    # Library loading diagnostics
    print("\nLibrary Diagnostics:")
    print("-" * 50)
    try:
        # Try to load the shared library directly
        print("Attempting to load Azure Speech SDK library...")
        lib_path = "/opt/render/project/src/.venv/lib/python3.11/site-packages/azure/cognitiveservices/speech/libMicrosoft.CognitiveServices.Speech.core.so"
        
        # Check file existence and permissions
        import os
        if not os.path.exists(lib_path):
            print(f"ERROR: Library file not found at {lib_path}")
        else:
            print(f"Library file exists at {lib_path}")
            print(f"File Permissions: {oct(os.stat(lib_path).st_mode)[-3:]}")
        
        # Try loading with ctypes
        ctypes.CDLL(lib_path)
        print("Azure Speech SDK library loaded successfully")
    except Exception as lib_error:
        print(f"Library Loading Error: {str(lib_error)}")
        print(f"Error Type: {type(lib_error).__name__}")
        import traceback
        print("Full Traceback:")
        traceback.print_exc()
    
    # Additional system library checks
    try:
        print("\nSystem Library Diagnostics:")
        print("-" * 50)
        # Check for required system libraries with multiple potential paths
        required_libs = [
            'libssl.so', 
            'libcrypto.so', 
            'libffi.so', 
            'libc.so'
        ]
        
        # Potential library paths
        lib_paths = [
            '/lib/x86_64-linux-gnu/',
            '/usr/lib/x86_64-linux-gnu/',
            '/lib64/',
            '/usr/lib64/'
        ]
        
        for lib in required_libs:
            lib_loaded = False
            for path in lib_paths:
                try:
                    full_path = os.path.join(path, lib)
                    if os.path.exists(full_path):
                        print(f"Attempting to load {full_path}")
                        ctypes.CDLL(full_path)
                        print(f"{lib} loaded successfully from {full_path}")
                        lib_loaded = True
                        break
                except Exception as e:
                    print(f"Could not load {lib} from {path}: {str(e)}")
            
            if not lib_loaded:
                print(f"WARNING: Could not load {lib} from any known path")
    except Exception as sys_lib_error:
        print(f"System Library Check Error: {str(sys_lib_error)}")
        import traceback
        traceback.print_exc()

def get_speech_config():
    """Get Azure speech config with API key and region"""
    try:
        # Perform comprehensive diagnostics
        diagnose_azure_speech_sdk()
        
        # Retrieve environment variables
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        service_region = os.getenv("AZURE_SPEECH_REGION", "eastus")
        service_endpoint = os.getenv("AZURE_SPEECH_ENDPOINT", "")
        
        if not speech_key:
            raise ValueError("Azure Speech API key is missing. Please set AZURE_SPEECH_KEY.")
        
        if not service_region:
            raise ValueError("Azure Speech service region is missing. Please set AZURE_SPEECH_REGION.")
        
        # Attempt to create speech configuration with additional error handling
        try:
            # Create speech configuration with explicit error handling
            print(f"Initializing Speech Config with Region: {service_region}")
            
            # Use a more robust configuration method
            speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=service_region
            )
            
            # Set endpoint if provided, with error handling
            if service_endpoint:
                try:
                    speech_config.endpoint_id = service_endpoint
                except Exception as endpoint_error:
                    print(f"Warning: Could not set endpoint: {str(endpoint_error)}")
            
            # Remove problematic property setting
            # Explicitly set speech synthesis language if needed
            speech_config.speech_synthesis_language = service_region
            
            # Additional configuration with error handling
            try:
                # Some SDKs might have different property names
                speech_config.set_property(
                    "SpeechServiceConnection_Host", 
                    f"{service_region}.tts.speech.microsoft.com"
                )
            except Exception as prop_error:
                print(f"Warning: Could not set host property: {str(prop_error)}")
            
            return speech_config
        except Exception as config_error:
            print(f"Detailed Speech Config Creation Error: {str(config_error)}")
            print(f"Error Type: {type(config_error).__name__}")
            print(f"Full Traceback: {traceback.format_exc()}")
            raise
    except Exception as e:
        print(f"Comprehensive Speech Service Configuration Error: {str(e)}")
        print(f"Full Traceback: {traceback.format_exc()}")
        raise

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
        speech_config = get_speech_config()
        if not speech_config:
            return ""
        
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
        # Validate inputs
        if not text or not text.strip():
            print("No text provided for speech generation")
            return None
        
        # Get speech configuration
        speech_config = get_speech_config()
        if not speech_config:
            print("Failed to get speech configuration")
            return None
        
        # Set voice name
        speech_config.speech_synthesis_voice_name = voice_name
        
        # Create a more persistent temporary file for audio output
        temp_file_path = os.path.join(tempfile.gettempdir(), f"speech_{os.getpid()}_{id(text)}.wav")
        
        # Create audio output config with temporary file
        audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_file_path)
        
        # Create speech synthesizer
        try:
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
        except Exception as synth_init_error:
            print(f"Error initializing speech synthesizer: {str(synth_init_error)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None
        
        print(f'Starting speech synthesis for text: {text[:100]}...')
        print(f'Using voice: {voice_name}')
        
        # Synthesize speech to file
        try:
            result = speech_synthesizer.speak_text_async(text).get()
        except Exception as speak_error:
            print(f"Error during speak_text_async: {str(speak_error)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None
        
        # Detailed result handling
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
                    os.unlink(temp_file_path)
            else:
                print('Audio file was not created')
            
            return None
        else:
            # Clean up the temporary file if synthesis fails
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            # Detailed error logging
            error_details = result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonErrorDetails)
            print(f"Speech synthesis failed: {result.reason}")
            if error_details:
                print(f"Error details: {error_details}")
            
            return None
            
    except Exception as e:
        print(f"Comprehensive speech generation error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return None
