import os
import io
import wave
import audioop
import logging
import azure.cognitiveservices.speech as speechsdk
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import asyncio
import json

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class WordAssessment:
    """Assessment results for a single word."""
    word: str
    accuracy_score: float
    error_type: Optional[str]
    phonemes: List[Dict]
    start_time: int
    duration: int
    syllable_count: int
    pronunciation_assessment: Dict

@dataclass
class PronunciationFeedback:
    """Complete pronunciation feedback for an utterance."""
    accuracy_score: float
    pronunciation_score: float
    completeness_score: float
    fluency_score: float
    words: List[Dict]
    phoneme_level_feedback: List[str]
    general_feedback: List[str]

class PronunciationAssessor:
    """Handles pronunciation assessment using Azure Speech Services."""

    def __init__(self):
        """Initialize the pronunciation assessor."""
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.service_region = os.getenv("AZURE_SPEECH_REGION")
        
        if not self.speech_key or not self.service_region:
            raise ValueError("Azure Speech credentials not found in environment variables")

    def _validate_wav(self, audio_data: bytes) -> bool:
        """Validate WAV file format."""
        try:
            # Check WAV header
            if len(audio_data) < 44:  # Minimum WAV header size
                logger.error("Audio data too short for WAV header")
                return False
            
            # Check RIFF header
            if audio_data[:4] != b'RIFF':
                logger.error(f"Invalid RIFF header: {audio_data[:4]}")
                return False
            
            # Check WAVE format
            if audio_data[8:12] != b'WAVE':
                logger.error(f"Invalid WAVE format: {audio_data[8:12]}")
                return False
            
            # Check fmt chunk
            if audio_data[12:16] != b'fmt ':
                logger.error(f"Invalid fmt chunk: {audio_data[12:16]}")
                return False

            # Create WAV file in memory to validate format
            with io.BytesIO(audio_data) as wav_buffer:
                with wave.open(wav_buffer, 'rb') as wav_file:
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    frame_rate = wav_file.getframerate()
                    logger.info(f"WAV format - Channels: {channels}, "
                              f"Sample width: {sample_width}, "
                              f"Frame rate: {frame_rate}")
                    
                    # Validate audio properties
                    if channels > 2:
                        logger.error(f"Unsupported number of channels: {channels}")
                        return False
                    if sample_width not in [1, 2, 4]:
                        logger.error(f"Unsupported sample width: {sample_width}")
                        return False
                    if frame_rate not in [8000, 16000, 32000, 44100, 48000]:
                        logger.error(f"Unsupported frame rate: {frame_rate}")
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating WAV format: {str(e)}")
            return False

    def _preprocess_audio(self, audio_data: bytes) -> Optional[bytes]:
        """Preprocess audio data for assessment."""
        try:
            logger.debug(f"Starting audio preprocessing, input size: {len(audio_data)} bytes")
            
            # Log input audio format
            logger.debug(f"Input audio data first 4 bytes: {audio_data[:4].hex()}")
            
            # Validate WAV format
            if not self._validate_wav(audio_data):
                logger.error("Invalid WAV format")
                return None
            
            # Create WAV from input data
            input_stream = io.BytesIO(audio_data)
            logger.debug("Created input stream")
            
            # Read WAV properties
            with wave.open(input_stream, 'rb') as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())

            logger.debug(f"Original audio properties - Channels: {channels}, "
                        f"Sample width: {sample_width}, Frame rate: {frame_rate}, "
                        f"Frames size: {len(frames)} bytes")

            # Convert to mono if needed
            if channels > 1:
                logger.debug(f"Converting {channels} channels to mono")
                frames = audioop.tomono(frames, sample_width, 1, 1)
                channels = 1
                logger.debug(f"Converted to mono, new frames size: {len(frames)} bytes")

            # Convert sample rate if needed
            if frame_rate != 16000:
                logger.debug(f"Converting sample rate from {frame_rate} to 16000")
                frames, _ = audioop.ratecv(frames, sample_width, channels, frame_rate, 16000, None)
                frame_rate = 16000
                logger.debug(f"Converted sample rate, new frames size: {len(frames)} bytes")

            # Create new WAV file
            output = io.BytesIO()
            with wave.open(output, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(frame_rate)
                wav_file.writeframes(frames)

            processed_data = output.getvalue()
            logger.debug(f"Processed audio size: {len(processed_data)} bytes")
            logger.debug(f"Processed audio first 4 bytes: {processed_data[:4].hex()}")

            return processed_data

        except Exception as e:
            logger.error(f"Error preprocessing audio: {str(e)}", exc_info=True)
            return None

    def _generate_feedback(self, word: Dict) -> List[str]:
        """Generate specific feedback for a word based on its assessment."""
        feedback = []
        
        # Check accuracy score
        if word['accuracy'] < 0.6:
            feedback.append(f"Work on pronouncing '{word['word']}' more clearly")
            
            # Add phoneme-specific feedback
            problem_phonemes = [p for p in word['phonemes'] if p['accuracy'] < 0.7]
            if problem_phonemes:
                for phoneme in problem_phonemes:
                    feedback.extend(self._get_phoneme_feedback(phoneme['phoneme'], word['word']))
        
        # Check syllable stress if available
        if 'syllables' in word:
            for syllable in word['syllables']:
                if syllable['accuracy'] < 0.7:
                    feedback.append(f"Pay attention to the stress pattern in '{word['word']}'")
        
        return feedback

    def _get_phoneme_feedback(self, phoneme: str, word: str) -> List[str]:
        """Get specific feedback for problematic phonemes."""
        phoneme_tips = {
            'ð': [f"Practice the 'th' sound in '{word}' by placing your tongue between your teeth"],
            'θ': [f"For the 'th' sound in '{word}', make sure your tongue touches your upper teeth"],
            'æ': [f"Open your mouth wider for the 'a' sound in '{word}'"],
            'ə': [f"Relax your mouth more for the schwa sound in '{word}'"],
            'ŋ': [f"For the 'ng' sound in '{word}', move the back of your tongue to the roof of your mouth"],
            'r': [f"Curl your tongue back slightly for the 'r' sound in '{word}'"],
            'l': [f"Touch the tip of your tongue to the roof of your mouth for the 'l' in '{word}'"],
            'w': [f"Round your lips more for the 'w' sound in '{word}'"],
            'v': [f"Use your bottom lip and upper teeth for the 'v' in '{word}'"],
            'z': [f"Add voice to the 's' sound for 'z' in '{word}'"],
        }
        
        return phoneme_tips.get(phoneme, [f"Pay attention to the '{phoneme}' sound in '{word}'"])

    async def assess_pronunciation(self, audio_data: bytes, reference_text: str) -> PronunciationFeedback:
        """Assess pronunciation using Azure Speech Services."""
        try:
            logger.info(f"Starting pronunciation assessment for text: {reference_text}")
            
            # Preprocess audio
            processed_audio = self._preprocess_audio(audio_data)
            if processed_audio is None:
                logger.error("Audio preprocessing failed")
                raise ValueError("Audio preprocessing failed")
            
            logger.info(f"Audio preprocessed successfully, size: {len(processed_audio)} bytes")

            # Create speech config
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key,
                region=self.service_region
            )
            speech_config.speech_recognition_language = "en-US"
            logger.info(f"Created speech config for region: {self.service_region}")

            # Create pronunciation assessment config
            pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text,
                grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme
            )
            logger.info("Created pronunciation assessment config")

            # Create audio stream
            audio_stream = speechsdk.audio.PushAudioInputStream()
            audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
            logger.info("Created audio stream configuration")

            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            pronunciation_config.apply_to(speech_recognizer)
            logger.info("Created speech recognizer with pronunciation assessment")

            # Write audio data to stream
            audio_stream.write(processed_audio)
            audio_stream.close()
            logger.info("Wrote audio data to stream")

            # Create a loop to handle the async recognition
            loop = asyncio.get_event_loop()
            future = loop.create_future()
            
            def handle_result(evt):
                try:
                    logger.info(f"Recognition result received: {evt}")
                    if not future.done():
                        future.set_result(evt)
                except Exception as e:
                    logger.error(f"Error in handle_result: {str(e)}")
                    if not future.done():
                        future.set_exception(e)

            def handle_canceled(evt):
                logger.error(f"Recognition canceled. Reason: {evt.reason}")
                if evt.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {evt.error_details}")
                if not future.done():
                    future.set_exception(ValueError(f"Recognition canceled: {evt.reason} - {evt.error_details if evt.reason == speechsdk.CancellationReason.Error else ''}"))

            # Subscribe to events
            speech_recognizer.recognized.connect(handle_result)
            speech_recognizer.canceled.connect(handle_canceled)

            # Start recognition
            speech_recognizer.start_continuous_recognition()
            
            try:
                # Wait for result with timeout
                result = await asyncio.wait_for(future, timeout=10.0)
                logger.info(f"Recognition completed: {result}")

                if result.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    logger.info(f"Recognized text: {result.result.text}")
                    
                    # Get pronunciation assessment
                    assessment = result.result.properties.get(
                        speechsdk.PropertyId.SpeechServiceResponse_JsonResult
                    )
                    logger.info(f"Assessment result: {assessment}")

                    if assessment:
                        try:
                            assessment_data = json.loads(assessment)
                            logger.info(f"Parsed assessment data: {assessment_data}")
                            
                            # Extract NBest results
                            if 'NBest' in assessment_data and len(assessment_data['NBest']) > 0:
                                nbest = assessment_data['NBest'][0]
                                pronunciation_assessment = nbest.get('PronunciationAssessment', {})
                                
                                # Get pronunciation assessment scores
                                scores = {
                                    'Accuracy': pronunciation_assessment.get('AccuracyScore', 0),
                                    'Pronunciation': pronunciation_assessment.get('PronScore', 0),
                                    'Completeness': pronunciation_assessment.get('CompletenessScore', 0),
                                    'Fluency': pronunciation_assessment.get('FluencyScore', 0)
                                }
                                logger.info(f"Extracted scores: {scores}")

                                # Get word-level details
                                words = nbest.get('Words', [])
                                word_details = []
                                for word in words:
                                    word_assessment = word.get('PronunciationAssessment', {})
                                    syllables = word.get('Syllables', [])
                                    phonemes = word.get('Phonemes', [])
                                    
                                    word_details.append({
                                        'word': word.get('Word', ''),
                                        'accuracy': word_assessment.get('AccuracyScore', 0),
                                        'error_type': word_assessment.get('ErrorType', 'None'),
                                        'syllables': [
                                            {
                                                'syllable': s.get('Syllable', ''),
                                                'accuracy': s.get('PronunciationAssessment', {}).get('AccuracyScore', 0)
                                            }
                                            for s in syllables
                                        ],
                                        'phonemes': [
                                            {
                                                'phoneme': p.get('Phoneme', ''),
                                                'accuracy': p.get('PronunciationAssessment', {}).get('AccuracyScore', 0)
                                            }
                                            for p in phonemes
                                        ]
                                    })

                                # Generate feedback based on scores and details
                                general_feedback = []
                                if scores['Accuracy'] < 70:
                                    general_feedback.append("Work on overall pronunciation accuracy")
                                if scores['Fluency'] < 70:
                                    general_feedback.append("Try to speak more smoothly and naturally")
                                if scores['Completeness'] < 70:
                                    general_feedback.append("Make sure to pronounce all parts of each word")

                                # Generate phoneme-level feedback
                                phoneme_feedback = []
                                for word_detail in word_details:
                                    for phoneme in word_detail['phonemes']:
                                        if phoneme['accuracy'] < 70:
                                            phoneme_feedback.append(
                                                f"The sound '{phoneme['phoneme']}' in '{word_detail['word']}' needs improvement"
                                            )

                                feedback = PronunciationFeedback(
                                    accuracy_score=float(scores['Accuracy']),
                                    pronunciation_score=float(scores['Pronunciation']),
                                    completeness_score=float(scores['Completeness']),
                                    fluency_score=float(scores['Fluency']),
                                    words=word_details,
                                    phoneme_level_feedback=phoneme_feedback,
                                    general_feedback=general_feedback
                                )

                                logger.info(f"Created feedback: {feedback}")
                                return feedback
                            else:
                                raise ValueError("No pronunciation assessment results found")
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse assessment result: {e}")
                            raise ValueError("Failed to parse pronunciation assessment result")
                    else:
                        raise ValueError("No pronunciation assessment result available")
                else:
                    raise ValueError(f"Recognition failed: {result.result.reason}")

            except asyncio.TimeoutError:
                logger.error("Recognition timed out after 10 seconds")
                raise ValueError("Recognition timed out")
            finally:
                # Stop recognition
                speech_recognizer.stop_continuous_recognition()
                logger.info("Stopped recognition")

        except Exception as e:
            logger.error(f"Error in pronunciation assessment: {str(e)}", exc_info=True)
            raise
