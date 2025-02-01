import os
import azure.cognitiveservices.speech as speechsdk
import numpy as np
from typing import Dict, Optional, Tuple, List
from dotenv import load_dotenv
import logging
import io
import wave
import json
from pathlib import Path
import asyncio
import sys
import audioop
import time
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

load_dotenv()

class AccentDetector:
    def __init__(self):
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.service_region = os.getenv("AZURE_SPEECH_REGION")
        logger.info(f"Initializing AccentDetector with region: {self.service_region}")
        
        if not self.speech_key or not self.service_region:
            logger.error("Azure Speech credentials not found in environment variables")
            raise ValueError("Azure Speech credentials not found in environment variables")
        
        self.accent_configs = {
            "American": {
                "lang": "en-US",
                "weight": 1.2
            },
            "British": {
                "lang": "en-GB",
                "weight": 1.0
            },
            "Australian": {
                "lang": "en-AU",
                "weight": 1.0
            },
            "Indian": {
                "lang": "en-IN",
                "weight": 1.0
            }
        }

    def _trim_silence(self, frames: bytes, sampwidth: int, threshold: int = 500) -> bytes:
        """Trim silence from the beginning and end of the audio."""
        try:
            # Convert bytes to array of samples
            sample_size = sampwidth
            total_samples = len(frames) // sample_size
            
            # Find start of speech
            start_pos = 0
            for i in range(0, len(frames), sample_size * 100):  # Process in blocks
                chunk = frames[i:i + sample_size * 100]
                if len(chunk) >= sample_size and audioop.rms(chunk, sample_size) > threshold:
                    start_pos = i
                    break
            
            # Find end of speech
            end_pos = len(frames)
            for i in range(len(frames) - sample_size * 100, 0, -sample_size * -100):
                chunk = frames[i:i + sample_size * 100]
                if len(chunk) >= sample_size and audioop.rms(chunk, sample_size) > threshold:
                    end_pos = i + sample_size * 100
                    break
            
            # Ensure we don't trim too much
            if end_pos - start_pos < sample_size * 100:  # At least 100 samples
                logger.warning("Audio too short after trimming, using original")
                return frames
            
            trimmed = frames[start_pos:end_pos]
            logger.debug(f"Trimmed audio from {len(frames)} to {len(trimmed)} bytes")
            return trimmed
            
        except Exception as e:
            logger.error(f"Error trimming silence: {str(e)}", exc_info=True)
            return frames

    def _validate_audio(self, audio_data: bytes) -> bool:
        """Validate audio data."""
        try:
            if audio_data is None or len(audio_data) < 44:  # WAV header is 44 bytes
                logger.error("Invalid audio data (too short or None)")
                return False
            
            try:
                with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
                    # Check channels (should be mono)
                    channels = wav_file.getnchannels()
                    if channels > 2:
                        logger.error(f"Unsupported number of channels: {channels}")
                        return False
                    
                    # Check sample width (should be 16-bit)
                    sample_width = wav_file.getsampwidth()
                    if sample_width not in [1, 2, 4]:  # 8-bit, 16-bit, or 32-bit
                        logger.error(f"Unsupported sample width: {sample_width}")
                        return False
                    
                    # Check frame rate (should be close to 16kHz)
                    frame_rate = wav_file.getframerate()
                    if not (8000 <= frame_rate <= 48000):
                        logger.error(f"Unsupported frame rate: {frame_rate}")
                        return False
                    
                    # Read a small chunk to verify data
                    chunk = wav_file.readframes(1024)
                    if not chunk:
                        logger.error("No audio data found")
                        return False
                    
                    # Check volume levels
                    rms = audioop.rms(chunk, sample_width)
                    if rms < 1:
                        logger.error("Audio too quiet")
                        return False
                    
                    return True
                    
            except Exception as e:
                logger.error(f"WAV validation error: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Audio validation error: {str(e)}")
            return False

    def _preprocess_audio(self, audio_data: bytes) -> Optional[bytes]:
        """Preprocess audio data for recognition."""
        try:
            # Convert to WAV format if needed
            wav_data = self._ensure_wav_format(audio_data)
            if not wav_data:
                return None

            # Read WAV properties
            with wave.open(io.BytesIO(wav_data), 'rb') as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())

            logger.debug(f"Original audio properties - Channels: {channels}, "
                        f"Sample width: {sample_width}, Frame rate: {frame_rate}")

            # Convert to mono if needed
            if channels > 1:
                frames = audioop.tomono(frames, sample_width, 1, 1)

            # Ensure 16-bit PCM
            if sample_width != 2:
                frames = audioop.lin2lin(frames, sample_width, 2)
                sample_width = 2

            # Resample to 16kHz if needed
            if frame_rate != 16000:
                frames = audioop.ratecv(frames, sample_width, 1, frame_rate, 16000, None)[0]
                frame_rate = 16000

            # Trim silence from start and end
            start_pos = 0
            end_pos = len(frames)
            
            # Find start (skip initial silence)
            rms_threshold = 500  # Adjusted threshold for silence detection
            chunk_size = 1024
            for i in range(0, len(frames) - chunk_size, chunk_size):
                chunk = frames[i:i + chunk_size]
                rms = audioop.rms(chunk, sample_width)
                if rms > rms_threshold:
                    start_pos = max(0, i - chunk_size)  # Include a bit before speech
                    break

            # Find end (skip trailing silence)
            for i in range(len(frames) - chunk_size, start_pos, -chunk_size):
                chunk = frames[i:i + chunk_size]
                rms = audioop.rms(chunk, sample_width)
                if rms > rms_threshold:
                    end_pos = min(len(frames), i + chunk_size * 2)  # Include a bit after speech
                    break

            # Skip if too much silence
            if end_pos - start_pos < chunk_size * 2:
                logger.warning("Audio contains mostly silence")
                return None

            # Trim the audio
            frames = frames[start_pos:end_pos]

            # Normalize volume
            max_vol = audioop.max(frames, sample_width)
            if max_vol > 0:
                target_vol = 32000  # Target volume (16-bit audio)
                frames = audioop.mul(frames, sample_width, min(target_vol / max_vol, 2.0))

            # Get final RMS value
            final_rms = audioop.rms(frames, sample_width)
            logger.debug(f"Final RMS value: {final_rms}")

            # Create new WAV file
            output = io.BytesIO()
            with wave.open(output, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(frame_rate)
                wav_file.writeframes(frames)

            processed_data = output.getvalue()
            logger.debug(f"Processed audio size: {len(processed_data)} bytes")

            if len(processed_data) < 1000:
                logger.warning("Processed audio is too short")
                return None

            return processed_data

        except Exception as e:
            logger.error(f"Error preprocessing audio: {str(e)}", exc_info=True)
            return None

    def _ensure_wav_format(self, audio_data: bytes) -> Optional[bytes]:
        """Ensure audio is in WAV format."""
        try:
            if audio_data is None or len(audio_data) < 44:  # WAV header is 44 bytes
                logger.error("Invalid audio data (too short or None)")
                return None
                
            logger.debug(f"Checking WAV format for {len(audio_data)} bytes")
            
            # Check if already WAV format
            try:
                with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    frame_rate = wav_file.getframerate()
                    logger.debug(f"Valid WAV format detected: {channels} channels, "
                               f"{sample_width} bytes/sample, {frame_rate} Hz")
                    return audio_data
            except Exception as e:
                logger.debug(f"Not a valid WAV file: {str(e)}")
            
            # Try to convert using ffmpeg
            try:
                process = subprocess.Popen(
                    ['ffmpeg', '-i', 'pipe:0', 
                     '-acodec', 'pcm_s16le',  # 16-bit PCM
                     '-ac', '1',              # Mono
                     '-ar', '16000',          # 16kHz
                     '-f', 'wav',
                     'pipe:1'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = process.communicate(input=audio_data)
                
                if process.returncode != 0:
                    logger.error(f"FFmpeg conversion failed: {stderr.decode()}")
                    return None
                
                # Verify converted WAV
                try:
                    with wave.open(io.BytesIO(stdout), 'rb') as wav_file:
                        channels = wav_file.getnchannels()
                        sample_width = wav_file.getsampwidth()
                        frame_rate = wav_file.getframerate()
                        logger.debug(f"Converted to WAV: {channels} channels, "
                                   f"{sample_width} bytes/sample, {frame_rate} Hz")
                        return stdout
                except Exception as e:
                    logger.error(f"Invalid converted WAV: {str(e)}")
                    return None
                    
            except Exception as e:
                logger.error(f"FFmpeg conversion error: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Error converting to WAV: {str(e)}", exc_info=True)
            return None

    def _calculate_score(self, text: str, recognition_time: float, confidence: float, language: str) -> float:
        """Calculate recognition score based on various factors."""
        try:
            # Split into words and calculate basic metrics
            words = [w.strip('.,!?').lower() for w in text.split()]
            word_count = len(words)
            if word_count == 0:
                return 0.0
            
            # Calculate average word length
            avg_word_length = sum(len(w) for w in words) / word_count
            
            # Base score from word count and length
            base_score = word_count * (avg_word_length / 4.0)  # Normalize by average English word length
            
            # Analyze word patterns for each accent
            accent_patterns = {
                'en-US': {
                    'strong': ['gonna', 'wanna', 'y\'all'],
                    'medium': ['yeah', 'awesome', 'totally', 'dude'],
                    'weak': ['hey', 'cool', 'like', 'guys']
                },
                'en-GB': {
                    'strong': ['mate', 'bloody', 'proper'],
                    'medium': ['cheers', 'brilliant', 'quite'],
                    'weak': ['rather', 'indeed', 'fancy']
                },
                'en-AU': {
                    'strong': ['g\'day', 'crikey', 'strewth'],
                    'medium': ['mate', 'reckon', 'fair'],
                    'weak': ['bloody', 'beauty', 'bonza']
                },
                'en-IN': {
                    'strong': ['kindly', 'itself', 'needful'],
                    'medium': ['actually', 'basically', 'only'],
                    'weak': ['please', 'doing', 'tell']
                }
            }
            
            # Count matching patterns with weights
            text_lower = ' '.join(words)
            pattern_score = 0.0
            
            if language in accent_patterns:
                patterns = accent_patterns[language]
                # Strong patterns (30% boost each)
                pattern_score += sum(0.3 for p in patterns['strong'] if p in text_lower)
                # Medium patterns (20% boost each)
                pattern_score += sum(0.2 for p in patterns['medium'] if p in text_lower)
                # Weak patterns (10% boost each)
                pattern_score += sum(0.1 for p in patterns['weak'] if p in text_lower)
            
            # Pattern bonus (cap at 100% boost)
            pattern_bonus = min(2.0, 1.0 + pattern_score)
            
            # Penalize very short or incomplete sentences
            if word_count < 3:
                base_score *= 0.7  # Stronger penalty for very short phrases
            elif word_count < 5:
                base_score *= 0.9  # Mild penalty for short phrases
            
            # Time factor (faster is better, but cap at reasonable limits)
            time_factor = min(2.0, max(0.5, 1.0 / max(recognition_time, 0.5)))
            
            # Language-specific base weights
            lang_weights = {
                'en-US': 1.15,  # American English
                'en-GB': 1.25,  # British English (stronger preference)
                'en-AU': 1.2,   # Australian English
                'en-IN': 1.2    # Indian English
            }
            
            # Calculate final score
            final_score = (
                base_score * 
                time_factor * 
                lang_weights.get(language, 1.0) * 
                confidence *
                pattern_bonus
            )
            
            # Log detailed scoring information
            logger.debug(
                f"Score details for {language}:\n"
                f"- Word count: {word_count}\n"
                f"- Avg word length: {avg_word_length:.2f}\n"
                f"- Base score: {base_score:.2f}\n"
                f"- Time factor: {time_factor:.2f}\n"
                f"- Language weight: {lang_weights.get(language, 1.0):.2f}\n"
                f"- Pattern score: {pattern_score:.2f}\n"
                f"- Pattern bonus: {pattern_bonus:.2f}\n"
                f"- Confidence: {confidence:.2f}\n"
                f"- Final score: {final_score:.2f}"
            )
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating score: {str(e)}")
            return 0.0

    async def _get_recognition_results(self, audio_data: bytes, language: str) -> Tuple[List[str], float]:
        """Get recognition results using speech recognition."""
        logger.debug(f"Starting recognition for {language}")
        
        try:
            # Preprocess audio
            processed_audio = self._preprocess_audio(audio_data)
            if processed_audio is None:
                logger.error("Audio preprocessing failed")
                return [], 0.0
            
            # Create speech config with custom settings
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key,
                region=self.service_region
            )
            speech_config.speech_recognition_language = language
            
            # Configure recognition settings
            speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
                "3000"  # 3 second initial silence timeout
            )
            speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
                "800"  # 800ms end silence timeout
            )
            speech_config.set_property(
                speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
                "200"  # 200ms segmentation silence timeout
            )
            speech_config.enable_audio_logging()
            
            # Create audio stream and config
            audio_stream = None
            recognizer = None
            
            try:
                # Create a new memory stream from the processed audio
                audio_stream = speechsdk.audio.PushAudioInputStream()
                audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
                
                # Create recognizer
                recognizer = speechsdk.SpeechRecognizer(
                    speech_config=speech_config,
                    audio_config=audio_config
                )
                
                # Write all audio data at once
                audio_stream.write(processed_audio)
                audio_stream.close()
                
                # Start recognition
                start_time = time.time()
                try:
                    result_future = asyncio.create_task(
                        asyncio.to_thread(recognizer.recognize_once_async().get)
                    )
                    
                    result = await asyncio.wait_for(result_future, timeout=5.0)
                    recognition_time = time.time() - start_time
                    
                    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                        text = result.text.strip()
                        if text:
                            logger.info(f"Recognized text for {language}: {text}")
                            
                            # Get confidence and detailed results
                            confidence = 1.0
                            try:
                                json_result = json.loads(result.properties.get(
                                    speechsdk.PropertyId.SpeechServiceResponse_JsonResult
                                ))
                                confidence = json_result.get('NBest', [{}])[0].get('Confidence', 1.0)
                                logger.debug(f"Recognition confidence: {confidence}")
                                
                                # Get alternative results if available
                                alternatives = json_result.get('NBest', [])[1:]
                                if alternatives:
                                    alt_texts = [alt.get('Lexical', '') for alt in alternatives[:2]]
                                    logger.debug(f"Alternative results: {alt_texts}")
                            except Exception as e:
                                logger.warning(f"Could not get detailed results: {str(e)}")
                            
                            # Calculate score
                            final_score = self._calculate_score(text, recognition_time, confidence, language)
                            
                            return [text], final_score
                    
                    elif result.reason == speechsdk.ResultReason.NoMatch:
                        no_match_reason = result.no_match_details.reason
                        logger.warning(f"No match for {language}: {no_match_reason}")
                        if no_match_reason == speechsdk.NoMatchReason.InitialSilenceTimeout:
                            logger.debug("Initial silence detected")
                        elif no_match_reason == speechsdk.NoMatchReason.InitialBabbleTimeout:
                            logger.debug("Initial babble detected")
                    
                    elif result.reason == speechsdk.ResultReason.Canceled:
                        cancellation = speechsdk.CancellationDetails(result)
                        logger.warning(f"Recognition canceled: {cancellation.reason}")
                        if cancellation.reason == speechsdk.CancellationReason.Error:
                            logger.error(f"Error details: {cancellation.error_details}")
                    
                    else:
                        logger.warning(f"Unexpected recognition result: {result.reason}")
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Recognition timeout for {language}")
                
                return [], 0.0
                
            finally:
                # Clean up resources
                if audio_stream:
                    try:
                        audio_stream.close()
                    except:
                        pass
            
        except Exception as e:
            logger.error(f"Error in recognition: {str(e)}", exc_info=True)
            return [], 0.0

    async def detect_accent(self, audio_data: bytes) -> Dict[str, float]:
        """Detect accent by comparing recognition across different language models."""
        try:
            logger.info(f"Starting accent detection with {len(audio_data)} bytes of audio")
            
            # Ensure audio is in WAV format
            audio_data = self._ensure_wav_format(audio_data)
            
            # Process each accent
            scores = {}
            texts = {}
            total_score = 0.0
            
            for accent, config in self.accent_configs.items():
                logger.info(f"Processing {accent} accent")
                texts_list, score = await self._get_recognition_results(
                    audio_data,
                    config["lang"]
                )
                weighted_score = score * config["weight"]
                scores[accent] = weighted_score
                texts[accent] = texts_list
                total_score += weighted_score
            
            logger.info(f"Raw scores: {scores}")
            logger.info(f"Recognition texts: {texts}")
            
            # Calculate percentages
            if total_score > 0:
                accent_probabilities = {
                    accent: (score / total_score) * 100
                    for accent, score in scores.items()
                }
            else:
                logger.warning("No recognition results, using weighted distribution")
                total_weight = sum(config["weight"] for config in self.accent_configs.values())
                accent_probabilities = {
                    accent: (config["weight"] / total_weight) * 100
                    for accent, config in self.accent_configs.items()
                }
            
            logger.info(f"Final probabilities: {accent_probabilities}")
            
            return dict(sorted(
                accent_probabilities.items(),
                key=lambda x: x[1],
                reverse=True
            ))
            
        except Exception as e:
            logger.error(f"Error in accent detection: {str(e)}", exc_info=True)
            raise Exception(f"Error in accent detection: {str(e)}")
