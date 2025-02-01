import os
import sys
import platform
import traceback
import ctypes
import subprocess

def check_system_libraries():
    """Check for required system libraries."""
    libraries_to_check = [
        'libssl.so',
        'libasound.so',
        'libpulse.so',
        'libffi.so',
        'libMicrosoft.CognitiveServices.Speech.core.so'
    ]
    
    library_status = {}
    for lib in libraries_to_check:
        try:
            ctypes.CDLL(lib)
            library_status[lib] = "Found"
        except Exception as e:
            library_status[lib] = f"Not found: {e}"
    
    return library_status

def run_system_checks():
    """Run additional system diagnostics."""
    checks = {
        'ldd_microsoft_core': None,
        'ldconfig_output': None
    }
    
    try:
        # Check Microsoft Speech Core library
        ldd_output = subprocess.check_output(['ldd', '/opt/render/project/src/.venv/lib/python3.11/site-packages/azure/cognitiveservices/speech/libMicrosoft.CognitiveServices.Speech.core.so'], stderr=subprocess.STDOUT, text=True)
        checks['ldd_microsoft_core'] = ldd_output
    except Exception as e:
        checks['ldd_microsoft_core'] = str(e)
    
    try:
        # Check system library configuration
        ldconfig_output = subprocess.check_output(['ldconfig', '-p'], stderr=subprocess.STDOUT, text=True)
        checks['ldconfig_output'] = ldconfig_output
    except Exception as e:
        checks['ldconfig_output'] = str(e)
    
    return checks

def check_azure_speech_sdk():
    try:
        import azure.cognitiveservices.speech as speech_sdk
        print("Azure Speech SDK successfully imported!")
        
        # Detailed system information
        print("\nSystem Details:")
        print(f"Python Version: {sys.version}")
        print(f"Platform: {platform.platform()}")
        print(f"Machine: {platform.machine()}")
        print(f"Processor: {platform.processor()}")
        
        # Check environment variables
        print("\nRelevant Environment Variables:")
        speech_key = os.environ.get('SPEECH_KEY')
        speech_region = os.environ.get('SPEECH_REGION')
        print(f"SPEECH_KEY: {'Set' if speech_key else 'Not Set'}")
        print(f"SPEECH_REGION: {'Set' if speech_region else 'Not Set'}")
        
        # System Library Checks
        print("\nSystem Library Diagnostics:")
        library_status = check_system_libraries()
        for lib, status in library_status.items():
            print(f"{lib}: {status}")
        
        # Additional System Checks
        print("\nAdditional System Diagnostics:")
        system_checks = run_system_checks()
        for check, output in system_checks.items():
            print(f"{check}:\n{output}\n---")
        
        # Attempt to create a speech configuration
        try:
            speech_config = speech_sdk.SpeechConfig(
                subscription=speech_key or 'dummy_key', 
                region=speech_region or 'eastus'
            )
            print("\nSpeech Configuration Creation: Successful")
        except Exception as config_error:
            print(f"\nSpeech Configuration Error: {config_error}")
            print(traceback.format_exc())
            
        # SDK Version and Detailed Diagnostics
        print(f"\nSDK Version: {speech_sdk.__version__}")
        
    except ImportError as e:
        print(f"Failed to import Azure Speech SDK: {e}")
        print(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    check_azure_speech_sdk()
