from deep_translator import GoogleTranslator
from typing import Optional, Dict, Union
import logging
import traceback

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        try:
            self.translator = GoogleTranslator()
            logger.info("Translator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize translator: {e}")
            logger.error(traceback.format_exc())
            raise

    def translate_text(self, text: str, target_language: Optional[str] = 'en', native_language: Optional[str] = None) -> Union[str, Dict[str, str]]:
        """
        Translate text to the specified target language.
        
        Args:
            text (str): Text to translate
            target_language (str, optional): Learning language code. Defaults to 'en' (English).
            native_language (str, optional): Native language of the user. Defaults to None.
        
        Returns:
            Union[str, Dict[str, str]]: Translated text or a message about language selection
        """
        logger.info(f"Translation request: text='{text}', target_language='{target_language}', native_language='{native_language}'")
        
        # Validate inputs
        if not text:
            logger.warning("Empty text provided for translation")
            return ""
        
        if not target_language:
            logger.warning("No target language provided, defaulting to English")
            target_language = 'en'
        
        # Validate native language
        if not native_language:
            logger.warning("No native language provided, cannot translate")
            return {
                "message": "No native language specified. Please select your native language first."
            }
        
        try:
            # Only translate if source and target languages are different
            if native_language.lower() != target_language.lower():
                translated_text = GoogleTranslator(source=target_language, target=native_language).translate(text)
                
                # Log translation details
                logger.info(f"Translation Details:")
                logger.info(f"  Original Text: '{text}'")
                logger.info(f"  Source Language (Native): '{native_language}'")
                logger.info(f"  Target Language (Learning): '{target_language}'")
                logger.info(f"  Translated Text: '{translated_text}'")
                
                return translated_text
            else:
                # Return a helpful message when languages are the same
                logger.info("Source and target languages are the same. No translation needed.")
                return  "No translation needed. You've selected the same language for native and learning. Go back to the language selection menu to choose a different native or learning language."
                
        except Exception as e:
            # Comprehensive error logging
            logger.error(f"Translation error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return original text with an error marker
            return f"[Translation Error] {text}"

translation_service = TranslationService()
