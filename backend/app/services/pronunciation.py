import azure.cognitiveservices.speech as speechsdk
import os
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import tempfile
import json
import traceback
from openai import OpenAI
import asyncio
import string

# Load environment variables
load_dotenv()

# Define phoneme guidance
PHONEME_GUIDE = {
    # English phonemes
    "θ": "Place your tongue between your teeth and blow air out gently (like in 'think')",
    "ð": "Place your tongue between your teeth and make a voiced sound (like in 'this')",
    "ʃ": "Position your tongue near the roof of your mouth and make a 'sh' sound (like in 'ship')",
    "ʒ": "Like 'sh' but with voice added (like in 'measure')",
    "ŋ": "Touch the back of your tongue to the soft palate (like in 'sing')",
    "ɹ": "Curl your tongue back slightly without touching the roof of your mouth (American 'r')",
    
    # French phonemes
    "ʁ": "Make a soft friction sound at the back of your throat (French 'r')",
    "y": "Make an 'ee' sound while rounding your lips (French 'u')",
    "ø": "Make an 'ay' sound while rounding your lips (French 'eu')",
    "œ": "Make an 'eh' sound while rounding your lips (French 'œuf')",
    "ɛ̃": "Make an 'eh' sound while letting air flow through your nose (French 'in')",
    "ɑ̃": "Make an 'ah' sound while letting air flow through your nose (French 'an')",
    "ɔ̃": "Make an 'oh' sound while letting air flow through your nose (French 'on')",
    
    # Spanish phonemes
    "β": "Like 'b' but very soft, barely touching your lips (Spanish 'b/v')",
    "ð̞": "Like 'th' in 'this' but softer (Spanish soft 'd')",
    "ɣ": "Like 'g' but softer, with less contact (Spanish soft 'g')",
    "χ": "Make a strong friction sound at the back of your throat (Spanish 'j')",
    "ɲ": "Press the middle of your tongue against the roof of your mouth (Spanish 'ñ')",
    "r": "Tap your tongue quickly against the ridge behind your upper teeth (Spanish tap 'r')",
    "rr": "Vibrate your tongue against the ridge behind your upper teeth (Spanish trill 'rr')",
    
    # Common stress patterns
    "ˈ": "This syllable should be stressed - make it longer and slightly louder",
    "ˌ": "This syllable should have secondary stress - slightly emphasized but less than primary stress",
}

def get_full_language_name(language_code):
    """
    Convert language codes to full language names
    
    Args:
        language_code (str): Language code like 'en-US', 'fr-FR', etc.
    
    Returns:
        str: Full language name
    """
    language_mapping = {
        # English variants
        'en-US': 'American English',
        'en-GB': 'British English',
        'en-AU': 'Australian English',
        'en-CA': 'Canadian English',
        'en-IN': 'Indian English',
        
        # French variants
        'fr-FR': 'Standard French',
        'fr-CA': 'Canadian French',
        'fr-BE': 'Belgian French',
        'fr-CH': 'Swiss French',
        
        # Spanish variants
        'es-ES': 'Castilian Spanish',
        'es-MX': 'Mexican Spanish',
        'es-AR': 'Argentine Spanish',
        
        # German variants
        'de-DE': 'Standard German',
        'de-AT': 'Austrian German',
        'de-CH': 'Swiss German',
        
        # Italian variants
        'it-IT': 'Standard Italian',
        
        # Portuguese variants
        'pt-BR': 'Brazilian Portuguese',
        'pt-PT': 'European Portuguese',
        
        # Other languages
        'zh-CN': 'Mandarin Chinese',
        'ja-JP': 'Japanese',
        'ko-KR': 'Korean',
        'ru-RU': 'Russian',
        'ar-SA': 'Arabic',
    }
    
    # Return full language name or default to the input code
    return language_mapping.get(language_code, language_code)

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

async def analyze_pronunciation(audio_data: bytes, reference_text: str, language: str = "en-US", is_word_practice: str = "false") -> Optional[Dict]:
    """Analyze pronunciation using Azure Speech SDK with a reference text
    
    Args:
        audio_data (bytes): Audio data to analyze
        reference_text (str): Reference text to compare against
        language (str): Language code (default: "en-US")
        is_word_practice (str): String "true" or "false" indicating if this is word practice mode
    """
    try:
        # Convert string to boolean
        is_word_practice = is_word_practice.lower() == "true"
        
        print(f"Pronunciation Analysis Debug:")
        print(f"  Language Code: {language}")
        print(f"  Reference Text: {reference_text}")
        print(f"  Mode: {'Word Practice' if is_word_practice else 'Sentence Analysis'}")

        # Create temporary WAV file for pronunciation assessment
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        speech_config = get_speech_config()
        if not speech_config:
            print("  Failed to get speech configuration")
            return {"error": "Failed to get speech configuration"}

        # First, do speech recognition to get what was actually said
        audio_config = speechsdk.audio.AudioConfig(filename=temp_file_path)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
            language=language
        )
        
        recognition_result = speech_recognizer.recognize_once_async().get()
        
        if recognition_result.reason == speechsdk.ResultReason.NoMatch:
            try:
                error_details = recognition_result.no_match_details
                error_message = f"No speech could be recognized: {error_details.reason if error_details else 'Unknown reason'}"
            except Exception as e:
                error_message = "No speech could be recognized. Please try speaking more clearly."
            print(f"  {error_message}")
            return {"error": error_message}
        elif recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speechsdk.CancellationDetails(recognition_result)
            error_message = f"Speech recognition canceled: {cancellation_details.reason}"
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                error_message += f"\nError details: {cancellation_details.error_details}"
            print(f"  {error_message}")
            return {"error": error_message}

        actual_text = recognition_result.text.strip()
        print(f"\nSpeech Recognition Result:")
        print(f"  Recognized text: '{actual_text}'")

        # For word practice mode, do strict text comparison
        if is_word_practice:
            print(f"  Expected word: '{reference_text}'")
            
            # Clean and compare texts
            def clean_text(text: str) -> str:
                """Clean text by removing punctuation and converting to lowercase"""
                text = text.lower()
                text = text.translate(str.maketrans("", "", string.punctuation))
                return " ".join(text.split())

            cleaned_actual = clean_text(actual_text)
            cleaned_reference = clean_text(reference_text)
            
            print(f"  Cleaned actual: '{cleaned_actual}'")
            print(f"  Cleaned reference: '{cleaned_reference}'")

            # Check if the words are different
            if cleaned_actual != cleaned_reference:
                print(f"  Wrong word detected!")
                return {
                    "error": f"Incorrect word. You said '{actual_text}' but should have said '{reference_text}'. Please try again."
                }

        # Create pronunciation assessment configuration
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True
        )

        # Create new audio config and recognizer for pronunciation assessment
        audio_config = speechsdk.audio.AudioConfig(filename=temp_file_path)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
            language=language
        )
        
        pronunciation_config.apply_to(speech_recognizer)
        result = speech_recognizer.recognize_once_async().get()
        
        # Clean up temp file
        os.unlink(temp_file_path)

        if result.reason == speechsdk.ResultReason.NoMatch:
            try:
                error_details = result.no_match_details
                error_message = f"Pronunciation assessment failed: {error_details.reason if error_details else 'Unknown reason'}"
            except Exception as e:
                error_message = "Pronunciation assessment failed. Please try speaking more clearly."
            print(f"  {error_message}")
            return {"error": error_message}
            
        pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
        
        # Process word-level results
        poor_words = []
        print("\nPronunciation Assessment:")
        for word in pronunciation_result.words:
            print(f"  Word: {word.word}")
            print(f"    Accuracy Score: {word.accuracy_score}")
            print(f"    Error Type: {word.error_type}")
            
            if word.accuracy_score < 80:  # Only include words that need improvement
                poor_words.append({
                    "word": word.word,
                    "accuracy": word.accuracy_score,
                    "error_type": word.error_type
                })
        
        feedback_messages = []
        if pronunciation_result.pronunciation_score < 80:
            feedback_messages.append(f"Your pronunciation needs improvement. Try to pronounce '{reference_text}' more clearly.")
        else:
            feedback_messages.append(f"Good job! Your pronunciation of '{reference_text}' is clear.")

        return {
            "pronunciation_score": pronunciation_result.pronunciation_score,
            "fluency_score": pronunciation_result.fluency_score,
            "feedback_messages": feedback_messages,
            "poor_words": poor_words,
            "transcribed_text": actual_text
        }
            
    except Exception as e:
        print(f"Error in pronunciation analysis: {str(e)}")
        traceback.print_exc()
        return {"error": f"Failed to analyze pronunciation: {str(e)}"}

async def transcribe_audio(audio_data: bytes, language: str = "en-US") -> Dict[str, str]:
    """
    Transcribe audio using Azure Speech to Text
    
    Args:
        audio_data (bytes): Raw audio data
        language (str, optional): Language code. Defaults to "en-US".
    
    Returns:
        Dict[str, str]: Transcription result with text and confidence
    """
    try:
        speech_config = get_speech_config()
        if not speech_config:
            return {"error": "Failed to get speech configuration"}

        # Set recognition language
        speech_config.speech_recognition_language = language
        
        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        # Use file config instead of stream for more reliable recognition
        audio_config = speechsdk.audio.AudioConfig(filename=temp_file_path)

        # Create speech recognizer with specific configuration
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        # Use single shot recognition for more reliable results with short audio
        result = speech_recognizer.recognize_once_async().get()
        
        # Clean up temp file
        os.unlink(temp_file_path)

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return {"text": result.text}
        elif result.reason == speechsdk.ResultReason.NoMatch:
            try:
                error_details = result.no_match_details
                error_message = f"No speech could be recognized: {error_details.reason if error_details else 'Unknown reason'}"
            except Exception as e:
                error_message = "No speech could be recognized. Please try speaking more clearly."
            print(error_message)
            return {"error": error_message}
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speechsdk.CancellationDetails(result)
            error_message = f"Speech recognition canceled: {cancellation_details.reason}"
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                error_message += f"\nError details: {cancellation_details.error_details}"
            print(error_message)
            return {"error": error_message}
        else:
            return {"error": f"Unexpected recognition result: {result.reason}"}

    except Exception as e:
        print(f"Error in transcribe_audio: {str(e)}")
        traceback.print_exc()
        return {"error": f"Failed to transcribe audio: {str(e)}"}

def generate_pronunciation_help(poor_words, language='en-US', accent='neutral'):
    """
    Generate detailed pronunciation help for words with poor pronunciation
    
    Args:
        poor_words (list): List of words with pronunciation issues
        language (str): Language code (e.g., 'en-US', 'en-GB')
        accent (str): Accent type (e.g., 'neutral', 'british', 'american')
    
    Returns:
        str: Detailed pronunciation guidance from GPT
    """
    try:
        # Initialize OpenAI client with API key from environment
        client = OpenAI()  # The API key will be automatically read from OPENAI_API_KEY environment variable
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        # Get full language name
        full_language_name = get_full_language_name(language)
        
        # Prepare the prompt with detailed word information
        word_details = []
        for word in poor_words:
            word_info = f"Word: {word['word']}"
            if 'mispronounced_phonemes' in word:
                phoneme_details = [
                    f"{phoneme['phoneme']} phoneme (accuracy: {phoneme['accuracy']}%)" 
                    for phoneme in word['mispronounced_phonemes']
                ]
                word_info += f". Problematic phonemes: {', '.join(phoneme_details)}"
            word_details.append(word_info)
        
        # Construct the prompt with language and accent context
        prompt = f"""
        Provide detailed pronunciation guidance for the following words with pronunciation challenges.
        
        Context:
        - Language: {full_language_name}
        - Accent: {accent}
        
        Words to improve:
        {chr(10).join(word_details)}
        
        Please provide guidance that is specific to the {full_language_name} language and {accent} accent, considering:
        1. Phonetic breakdown of each word
        2. Specific pronunciation nuances for this language and accent
        3. Detailed explanation of how to pronounce challenging phonemes
        4. Tongue placement and mouth positioning tips
        5. 2-3 example sentences to help practice pronunciation
        
        Emphasize the pronunciation differences that might exist in this specific accent.
        Make the explanation clear, friendly, and encouraging.
        """
        
        print('Sending prompt to OpenAI:', prompt)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful pronunciation coach specialized in language-specific pronunciation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.7
        )
        
        # Extract and return the response
        result = response.choices[0].message.content.strip()
        print('OpenAI response:', result)
        
        return result
        
    except Exception as e:
        print(f"Error in generate_pronunciation_help: {str(e)}")
        traceback.print_exc()
        raise e
