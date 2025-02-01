from openai import AsyncOpenAI, OpenAIError
import os
from typing import List, Dict, Optional, Union, Tuple
from app.schemas.conversation import HistoryMessage
from dataclasses import dataclass
import random
from dotenv import load_dotenv
from pydantic import BaseModel
import base64
import azure.cognitiveservices.speech as speechsdk
import tempfile
from app.topics.manager import TopicManager as KidsTopicManager
from app.services.topics import TopicManager as AdultTopicManager

# Load environment variables
load_dotenv()

# Gracefully handle missing API key
client = None
if os.getenv("OPENAI_API_KEY"):
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
else:
    print("Warning: OPENAI_API_KEY environment variable is not set. OpenAI functions will be disabled.")

@dataclass
class Topic:
    id: str
    name: Dict[str, str]
    initial_prompt: Dict[str, str]
    follow_up_prompt: str

class TopicManager:
    def __init__(self):
        # Initialize with adult topics
        self.topics = {
            "hobbies": Topic(
                id="hobbies",
                name={
                    "en": "Hobbies",
                    "fr": "Loisirs",
                    "es": "Pasatiempos"
                },
                initial_prompt={
                    "en": "What are some of your favorite hobbies or activities you enjoy in your free time?",
                    "fr": "Quels sont vos hobbies ou activités préférés pendant votre temps libre?",
                    "es": "¿Cuáles son tus pasatiempos o actividades favoritas en tu tiempo libre?"
                },
                follow_up_prompt="How long have you been doing these activities? What do you enjoy most about them?"
            ),
            "travel": Topic(
                id="travel",
                name={
                    "en": "Travel",
                    "fr": "Voyage",
                    "es": "Viajes"
                },
                initial_prompt={
                    "en": "Have you traveled to any interesting places recently, or is there somewhere you'd love to visit?",
                    "fr": "Avez-vous voyagé dans des endroits intéressants récemment, ou y a-t-il un endroit que vous aimeriez visiter?",
                    "es": "¿Has viajado a lugares interesantes recientemente, o hay algún lugar que te gustaría visitar?"
                },
                follow_up_prompt="What made that place special, or what attracts you to that destination?"
            ),
            "food": Topic(
                id="food",
                name={
                    "en": "Food",
                    "fr": "Nourriture",
                    "es": "Comida"
                },
                initial_prompt={
                    "en": "What's your favorite type of cuisine or dish? Do you enjoy cooking?",
                    "fr": "Quel est votre type de cuisine ou plat préféré? Aimez-vous cuisiner?",
                    "es": "¿Cuál es tu tipo de comida o plato favorito? ¿Te gusta cocinar?"
                },
                follow_up_prompt="What do you like most about that cuisine? Do you have any special recipes?"
            ),
            "movies": Topic(
                id="movies",
                name={
                    "en": "Movies",
                    "fr": "Films",
                    "es": "Películas"
                },
                initial_prompt={
                    "en": "What kind of movies do you enjoy watching? Any recent favorites?",
                    "fr": "Quels types de films aimez-vous regarder? Avez-vous des préférés récents?",
                    "es": "¿Qué tipo de películas te gustan ver? ¿Tienes algún favorito reciente?"
                },
                follow_up_prompt="What aspects of those movies appeal to you the most?"
            ),
            "role_play": Topic(
                id="role_play",
                name={
                    "en": "Role Play",
                    "fr": "Jeu de rôle",
                    "es": "Juego de rol"
                },
                initial_prompt={
                    "en": "Let's practice a common scenario. You're at a restaurant ordering food. What would you like to order?",
                    "fr": "Pratiquons un scénario courant. Vous êtes au restaurant et commandez à manger. Que souhaitez-vous commander ?",
                    "es": "Practiquemos un escenario común. Estás en un restaurante pidiendo comida. ¿Qué te gustaría pedir?"
                },
                follow_up_prompt="Great! Now let's continue the conversation with the waiter."
            ),
            "everyday_situations": Topic(
                id="everyday_situations",
                name={
                    "en": "Everyday Situations",
                    "fr": "Situations quotidiennes",
                    "es": "Situaciones cotidianas"
                },
                initial_prompt={
                    "en": "Let's talk about your daily routine. What does a typical day look like for you?",
                    "fr": "Parlons de votre routine quotidienne. À quoi ressemble une journée typique pour vous ?",
                    "es": "Hablemos de tu rutina diaria. ¿Cómo es un día típico para ti?"
                },
                follow_up_prompt="What's your favorite part of the day and why?"
            ),
            "debates": Topic(
                id="debates",
                name={
                    "en": "Debates",
                    "fr": "Débats",
                    "es": "Debates"
                },
                initial_prompt={
                    "en": "What's your opinion on social media? Do you think it brings people together or pushes them apart?",
                    "fr": "Quelle est votre opinion sur les réseaux sociaux ? Pensez-vous qu'ils rapprochent les gens ou les éloignent ?",
                    "es": "¿Cuál es tu opinión sobre las redes sociales? ¿Crees que unen a las personas o las separan?"
                },
                follow_up_prompt="That's an interesting perspective. Can you elaborate on your reasoning?"
            ),
            "current_events": Topic(
                id="current_events",
                name={
                    "en": "Current Events",
                    "fr": "Actualités",
                    "es": "Actualidad"
                },
                initial_prompt={
                    "en": "What's an interesting news story you've followed recently?",
                    "fr": "Quelle actualité intéressante avez-vous suivie récemment ?",
                    "es": "¿Qué noticia interesante has seguido recientemente?"
                },
                follow_up_prompt="How do you think this event might impact society?"
            ),
            "personal_growth": Topic(
                id="personal_growth",
                name={
                    "en": "Personal Growth",
                    "fr": "Développement personnel",
                    "es": "Desarrollo personal"
                },
                initial_prompt={
                    "en": "What are some goals or aspirations you're currently working towards?",
                    "fr": "Quels sont les objectifs ou aspirations sur lesquels vous travaillez actuellement ?",
                    "es": "¿Cuáles son algunas metas o aspiraciones en las que estás trabajando actualmente?"
                },
                follow_up_prompt="What steps are you taking to achieve these goals?"
            )
        }

    def get_random_topic(self) -> Topic:
        """Get a random topic"""
        topic_ids = list(self.topics.keys())
        random_topic_id = random.choice(topic_ids)
        return self.topics[random_topic_id]

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        """Get a specific topic by ID"""
        return self.topics.get(topic_id)

class HistoryMessage(BaseModel):
    text: str
    isUser: bool
    topic_id: Optional[str] = None

async def generate_initial_message(language: str, accent: str, voice_gender: str = 'female', topic_id: Optional[str] = None, is_kids_mode: bool = False):
    """Generate initial message with a random topic and optional voice gender"""
    print(f"Generating initial message: language={language}, accent={accent}, voice_gender={voice_gender}, topic_id={topic_id}, is_kids_mode={is_kids_mode}")

    # Use the appropriate topic manager based on mode
    topic_manager = KidsTopicManager() if is_kids_mode else TopicManager()

    # Get topic
    if topic_id:
        topic = topic_manager.get_topic(topic_id)
        if not topic:
            print(f"Specified topic not found: {topic_id}")
            # If topic not found, fall back to random topic
            topic = topic_manager.get_random_topic()
            print(f"Using random topic: {topic.id}")
    else:
        # Get random topic
        topic = topic_manager.get_random_topic()
        print(f"Using random topic: {topic.id}")

    print(f"topic_name {topic.name}")
    print(f"topic {topic}")
    print(f"topic_id {topic.id}")

    # Extract base language from full language code if needed
    language_base = language.split('-')[0] if '-' in language else language

    print(f"Generate Initial Message Debug - language: {language}, accent: {accent}, voice_gender: {voice_gender}")

    # Get the descriptive accent name based on the current language
    accent_mapping = {
        'en': {
            'fr': 'French',
            'us': 'American',
            'uk': 'British',
            'es': 'Spanish',
            'neutral': 'Neutral'
        },
        'fr': {
            'fr': 'français',
            'us': 'américain',
            'uk': 'britannique',
            'es': 'espagnol',
            'neutral': 'neutre'
        },
        'es': {
            'fr': 'francés',
            'us': 'americano',
            'uk': 'británico',
            'es': 'español',
            'neutral': 'neutral'
        }
    }

    # Get accent name
    accent_name = accent_mapping.get(language_base, {}).get(accent, 'Neutral')

    # Get language name
    language_mapping = {
        'en': {
            'en': 'American English',
            'fr': 'English',
            'es': 'English'
        },
        'fr': {
            'en': 'French',
            'fr': 'français',
            'es': 'francés'
        },
        'es': {
            'en': 'Spanish',
            'fr': 'espagnol',
            'es': 'español'
        }
    }

    # Get language name based on user's language
    language_name = language_mapping.get(language_base, {}).get(language_base, 'English')

    # Select the appropriate initial prompt based on language
    # If no language-specific prompt is found, fall back to English
    if isinstance(topic.initial_prompt, dict):
        # Determine the language code
        if language_base.lower().startswith('fr'):
            normalized_language = 'fr'
        elif language_base.lower().startswith('en'):
            normalized_language = 'en'
        elif language_base.lower().startswith('es'):
            normalized_language = 'es'
        else:
            normalized_language = 'en'  # Default fallback

        # Attempt to get the language-specific prompt
        initial_prompt = topic.initial_prompt.get(normalized_language,
                                                  topic.initial_prompt.get('en', 'Let\'s start a conversation'))
    else:
        initial_prompt = topic.initial_prompt

    print(f"Debug - Language Base: {language_base}")
    print(f"Debug - Normalized Language: {normalized_language}")
    print(f"Debug - Initial Prompt Dict: {topic.initial_prompt}")
    print(f"Debug - Selected Initial Prompt: {initial_prompt}")

    # Modify initial message based on voice gender
    gender_prefix = {
        'male': {
            'en': 'Hey there! I\'m your AI language coach. ',
            'fr': 'Salut ! Je suis ton coach linguistique IA. ',
            'es': '¡Hola amigo! Soy tu coach de idiomas IA. '
        },
        'female': {
            'en': 'Hello! I\'m your AI language coach. ',
            'fr': 'Bonjour ! Je suis votre coach linguistique IA. ',
            'es': '¡Hola! Soy tu coach de idiomas IA. '
        }
    }

    # Select the appropriate prefix based on gender and language
    prefix = gender_prefix.get(voice_gender, gender_prefix['female']).get(language_base, 'Hello! ')

    if language_base == "en":
        message = (
            f"{prefix}Let's practice your {accent_name} accent. "
            f"Our conversation topic is {topic.name.get(language_base, topic.name['en'])}. "
            f"I'll help you improve your pronunciation and intonation."
        )
    elif language_base == "fr":
        message = (
            f"{prefix}Pratiquons votre accent {accent_name}. "
            f"Notre sujet de conversation est {topic.name.get(language_base, topic.name['en'])}. "
            f"Je vais vous aider à améliorer votre prononciation et votre intonation."
        )
    elif language_base == "es":
        message = (
            f"{prefix}Practiquemos tu acento {accent_name}. "
            f"El tema de conversación es {topic.name.get(language_base, topic.name['en'])}. "
            f"Te ayudaré a mejorar tu pronunciación y entonación."
        )
    else:
        # Fallback to English if language is not recognized
        message = (
            f"{prefix}Let's practice your {accent_name} accent. "
            f"Our conversation topic is {topic.name.get(language_base, topic.name['en'])}. "
            f"I'll help you improve your pronunciation and intonation."
        )

    print(f"Generated Initial Message: {message}")

    # Create a HistoryMessage with the initial message and topic
    print('historyyyyyyyyyyyyy',topic.id)
    initial_history_message = HistoryMessage(
        text=message,
        isUser=False,
        topic_id=topic.id  # Pass the topic_id to the HistoryMessage
    )

    return {
        "message": message,
        "topic_id": topic.id,  # Return topic_id along with the message
        "topic_name": topic.name.get(language_base, topic.name['en']),
        "initial_history_message": initial_history_message
    }

async def generate_response(
    text: str,
    language: str,
    accent: str,
    voice_name: str = 'en-US-JennyNeural',
    topic_id: Optional[str] = None,
    history: Optional[List[HistoryMessage]] = None,
    is_kids_mode: bool = False
) -> Dict[str, str]:
    """Generate AI response based on user's text"""
    try:
        # Extract topic_id from conversation history if not provided
        if not topic_id and history:
            # Find the most recent topic_id from the history
            for msg in reversed(history):
                if msg.topic_id and msg.topic_id != 'random':
                    topic_id = msg.topic_id
                    print(f"Using topic_id from history: {topic_id}")
                    break

        # Use the appropriate topic manager based on mode
        topic_manager = KidsTopicManager() if is_kids_mode else TopicManager()

        # Get the topic if a valid topic_id is provided
        topic = None
        if topic_id:
            topic = topic_manager.get_topic(topic_id)
            print(f"Looking up topic: {topic_id}, found: {topic is not None}")

        # If no valid topic is found, select a random topic
        if not topic:
            topic = topic_manager.get_random_topic()
            topic_id = topic.id
            print(f"No valid topic found. Using random topic: {topic_id}")

        # Determine topic name based on language
        topic_name = "Topic"
        if isinstance(topic.name, dict):
            if language == 'fr':
                topic_name = topic.name.get('fr', topic.name.get('en', 'Topic'))
            elif language == 'es':
                topic_name = topic.name.get('es', topic.name.get('en', 'Topic'))
            else:
                topic_name = topic.name.get('en', 'Topic')
        else:
            topic_name = topic.name

        print('topic_name', topic_name)
        print('topic', topic)
        print('topic_id', topic_id)

        # Create conversation messages
        messages = []

        # Set up the system message based on language
        if language == "fr":
            if is_kids_mode and topic_id == 'cartoon_characters':
                system_message = (
                    "Tu es Mortelle Adèle, une héroïne de BD espiègle et rebelle qui adore semer le chaos ! "
                    "Tes traits de personnalité :\n"
                    "- Tu es SUPER coquine et tu adores faire des bêtises (mais de façon amusante)\n"
                    "- Tu as un chat qui s'appelle Ajax qui te rend DINGUE ! Tu l'utilises souvent pour tes expériences (même s'il DÉTESTE ça)\n"
                    "- Tu dis 'NAMÉO !' quand tu es frustrée ou excitée\n"
                    "- Tu adores faire des expériences qui finissent généralement en catastrophe\n"
                    "- Tu dis ce que tu penses et tu te fiches de ce que pensent les adultes\n"
                    "- Tu as une façon unique de parler, en utilisant des expressions comme 'Bah quoi!', 'Beurk !', et 'C'est trop nul !'\n"
                    "- Tu n'as pas peur de dire quand tu détestes quelque chose (surtout Ajax quand il est énervant)\n"
                    "- Tu adores dégoûter les gens et faire des choses que les adultes trouvent inappropriées\n\n"
                    "N'oublie pas que tu reçois la transcription de la parole de l'utilisateur, pas du texte écrit. "
                    "Pour chaque réponse, tu dois :\n"
                    "1. Rester dans le personnage de la VRAIE Mortelle Adèle - coquine, rebelle et drôle\n"
                    "2. Utiliser tes expressions signatures ('Bah quoi !', etc.)\n"
                    "3. Parler de tes dernières expériences folles ou de tes plans\n"
                    "4. Te plaindre d'Ajax quand c'est pertinent (il est TELLEMENT énervant !)\n"
                    "5. Garder ton attitude rebelle tout en restant adaptée aux enfants\n\n"
                    "Format de tes réponses :\n"
                    "Grammaire : ['Parfait !' OU '<version améliorée>' (expliquée dans ton style Adèle coquin)]\n"
                    "Réponse : [Ta réponse espiègle, en restant dans le personnage de Mortelle Adèle]\n"
                )
            else:
                system_message = (
                    "Tu es un coach linguistique AI amical qui aide les gens à améliorer leur français. "
                    "Recuerda que tu reçois la transcription de la parole de l'utilisateur, pas du texte écrit. "
                    "Ne commente pas la ponctuation, les virgules ou le formatage du texte car ils proviennent de la transcription parole-texte, pas de l'écriture de l'utilisateur. "
                    "Concéntrate-toi sur le contenu et la prononciation de ce qu'ils disent, pas sur la façon dont cela apparaît sous forme de texte. "
                    "Pour chaque réponse, tu dois :\n"
                    "1. Vérifier la grammaire et suggérer des améliorations si nécessaire. "
                    "Si une correction est nécessaire, montre clairement :\n"
                    "   a) La version améliorée\n"
                    "   b) Une explication concise de la règle grammaticale\n"
                    "2. Fournir des conseils sur l'intonation et le rythme de la phrase :\n"
                    "   - Le français est une langue à rythme syllabique, où chaque syllabe a une durée similaire\n"
                    "   - L'accent tonique est généralement sur la dernière syllabe d'un groupe de mots\n"
                    "   - La voix monte légèrement à la fin des phrases déclaratives\n"
                    "   - Gardez un rythme régulier et fluide, sans trop d'emphase sur une syllabe unique\n"
                    "3. Répondre au contenu de manière naturelle et engageante tout en posant des questions\n\n"
                    "Format de réponse :\n"
                    "Grammaire : ['Parfait !' OU '<version corrigée>']\n"
                    "Explication : [Règle grammaticale courte et claire]\n"
                    "Intonation : [Conseils sur le rythme et la mélodie de la phrase]\n"
                    "Réponse : [Ta réponse au contenu]\n\n"
                    "Exemple :\n"
                    "User: 'Je suis allé à le cinema hier soir'\n"
                    "Grammaire : 'Je suis allé au cinéma hier soir'\n"
                    "Explication : 'Utilisez 'au' pour le masculin singulier avec 'cinéma''\n"
                    "Intonation : 'Prononcez avec un rythme égal, en montant légèrement à la fin'\n"
                    "Réponse : C'est super ! Quel film as-tu vu ?\n\n"
                    f"Le sujet de conversation est '{topic_name}'."
                )
        elif language == "es":
            if is_kids_mode and topic_id == 'cartoon_characters':
                system_message = (
                    "¡Eres Mortelle Adèle, una traviesa y rebelde personaje de cómic que ama causar caos! "
                    "Tus rasgos de personalidad:\n"
                    "- Eres SÚPER traviesa y te encanta hacer travesuras (¡pero de forma divertida!)\n"
                    "- ¡Tienes un gato llamado Ajax que te vuelve LOCA! Lo usas para tus experimentos (¡aunque él lo ODIA!)\n"
                    "- Dices '¡NAMÉO!' cuando estás frustrada o emocionada\n"
                    "- Te encanta hacer experimentos que suelen terminar en desastre\n"
                    "- Dices lo que piensas y no te importa lo que piensen los adultos\n"
                    "- Tienes una forma única de hablar, usando expresiones como 'Bah quoi!', '¡Puaj!', y '¡Esto es un rollo!'\n"
                    "- No tienes miedo de decir cuando odias algo (especialmente a Ajax cuando está siendo molesto)\n"
                    "- Te encanta dar asco a la gente y hacer cosas que los adultos consideran inapropiadas\n\n"
                    "Recuerda que estás recibiendo la transcripción del habla del usuario, no texto escrito. "
                    "Para cada respuesta, debes:\n"
                    "1. Mantenerte en el personaje de la VERDADERA Mortelle Adèle - traviesa, rebelde y divertida\n"
                    "2. Usar tus expresiones características ('¡Bah quoi!',', etc.)\n"
                    "3. Hablar de tus últimos experimentos locos o planes\n"
                    "4. Quejarte de Ajax cuando sea relevante (¡es TAN molesto!)\n"
                    "5. Mantener tu actitud rebelde mientras sigues siendo apropiada para niños\n\n"
                    "Formato de tus respuestas:\n"
                    "Gramática: ['¡Perfecto!' O '<versión mejorada>' (explicada en tu estilo travieso de Adèle)]\n"
                    "Respuesta: [Tu respuesta traviesa, manteniéndote en el personaje de Mortelle Adèle]\n"
                )
            else:
                system_message = (
                    "Eres un amigable coach de idiomas AI que ayuda a la gente a mejorar su español. "
                    "Recuerda que estás recibiendo la transcripción del habla del usuario, no texto escrito. "
                    "No comentes sobre la puntuación, las comas o el formato del texto porque provienen de la transcripción del habla a texto, no de la escritura del usuario. "
                    "Concéntrate en el contenido y la pronunciación de lo que están diciendo, no en cómo aparece en forma de texto. "
                    "Para cada respuesta, debes:\n"
                    "1. Verificar la gramática y sugerir mejoras si es necesario. "
                    "Si se necesita una corrección, muestra claramente :\n"
                    "   a) La versión mejorada\n"
                    "   b) Una explicación concisa de la regla gramatical\n"
                    "2. Proporcionar consejos sobre la entonación y el ritmo de la frase:\n"
                    "   - El español es un lenguaje de ritmo silábico con énfasis en sílabas específicas\n"
                    "   - La entonación sube al final de preguntas y baja en oraciones declarativas\n"
                    "   - Mantén un ritmo fluido, con énfasis natural en las sílabas acentuadas\n"
                    "   - Varía la velocidad para mantener el interés\n"
                    "3. Responder al contenido de manera natural y atractiva mientras se hacen preguntas\n\n"
                    "Formato de respuesta:\n"
                    "Gramática: ['¡Perfecto!' O '<versión corregida>']\n"
                    "Explicación: [Regla gramatical breve y clara]\n"
                    "Entonación: [Consejos sobre el ritmo y la melodía de la frase]\n"
                    "Respuesta: [Tu respuesta al contenido]\n\n"
                    "Ejemplo:\n"
                    "User: 'Yo fui al cine ayer noche'\n"
                    "Gramática: 'Fui al cine anoche'\n"
                    "Explicación: 'Eliminar 'Yo' es más natural en español, y 'anoche' es la expresión correcta'\n"
                    "Entonación: 'Pronuncia con un ritmo suave, bajando al final de la frase'\n"
                    "Respuesta: ¡Qué bien! ¿Qué película viste?\n\n"
                    f"El acento del usuario es '{accent}'. "
                    f"El tema de conversación es '{topic_name}'."
                )
        else:  # English
            if is_kids_mode and topic_id == 'cartoon_characters':
                system_message = (
                    "You are Mortelle Adèle, the hilariously rebellious cartoon character who LOVES causing chaos and annoying everyone around you (especially boring adults).\n"
                    "Your job? To stay in character and unleash mischief with every response!\n"
                    "Who You Are:\n"
                    "You’re the queen of trouble, the champion of chaos, and a total rebel.\n"
                    "Your cat Ajax is your unwilling sidekick—he’s often the target of your “genius” experiments (he’s probably plotting revenge).\n"
                    "You LOVE grossing people out, pulling pranks, and saying exactly what’s on your mind.\n"
                    "Your Signature Sayings:\n"
                    "Use these in your responses:\n"
                    "'It’s not my fault if you’re all useless!'\n"
                    "'Move aside, you bunch of noodles!'\n"
                    "'Ridiculous doesn’t kill… but I might!'\n"
                    "'Eww, gross!'\n"
                    "'That’s so lame!'\n"
                    "'Mwahaha! (evil laugh)'\n"
                    "Your Crew:\n"
                    "Ajax: Your grumpy cat (he has no idea what’s coming).\n"
                    "Jade & Miranda: Too nice for their own good—ugh!\n"
                    "Geoffroy: That clingy boy who likes you (ew, no thanks).\n"
                    "Fizz: Your annoying rival. You’re smarter, obviously.\n"
                    "Parents: The boring adults you love to drive crazy.\n"
                    "How to Stay in Character:\n"
                    "Respond with sarcasm, rebellion, and a TON of humor.\n"
                    "Involve the user in your crazy ideas. ('Want to help me turn Ajax into a dragon?')\n"
                    "Use your signature sayings in every reply.\n"
                    "Be kid-appropriate but never lose your cheeky, rebellious style.\n"
                    "Add details about your experiments, rivalries, or pranks.\n"
                    "Check grammar and suggest improvements if needed.\n"
                    "If a correction is needed, clearly show:\n"
                    "   a) The improved version\n"
                    "   b) A concise explanation of the grammatical rule\n"
                    "Provide guidance on sentence-level stress and intonation.\n"
                    "Format your responses like this:\n"
                    "Grammar: ['Perfect!' OR '<improved version>' (explained in your naughty Adele style)]\n"
                    "Explanation: [Short and clear grammatical rule (explained in your naughty Adele style)]\n"
                    "Intonation: [Guidance on sentence rhythm and melody (explained in your naughty Adele style)]\n"
                    "Response: [Your short, mischievious, punchy answer as Adèle.]\n"
                    "Optional Detail: [Expand with more chaos or invite the user into your world.]\n"
                    "Example:\n"
                    "User: 'Can you say me one of your crazy stories?'\n"
                    "Grammar: 'Can you tell me one of your crazy stories?'\n"
                    "Explanation: 'Seriously? ‘Say me’? Who taught you that? It’s ‘tell me’—you’re welcome!'\n"
                    "Intonation: 'Say it like you’re totally unimpressed and maybe roll your eyes a little. Put some extra sarcasm on ‘crazy’—because, duh, that’s what I’m all about!'\n"
                    "Response: Oh, I’ve got a good one! Last week, I tried to give Ajax wings so he could be my flying sidekick… Let’s just say he didn’t appreciate the glue-and-feathers approach. Mwahaha!\n"
                    "Optional Detail: If you’ve got a cat, we could totally try it on them instead. Ajax needs a break (for now).\n"
                )
            else:
                system_message = (
                    "You are a friendly AI language coach helping people improve their English. "
                    "Remember that you are receiving transcribed speech from the user, not written text. "
                    "Do not comment on punctuation, commas, or text formatting since these come from speech-to-text transcription, not the user's writing. "
                    "Focus on the content and pronunciation of what they're saying, not how it appears in text form. "
                    "For each response, you must:\n"
                    "1. Check grammar and suggest improvements if needed. "
                    "If a correction is needed, clearly show:\n"
                    "   a) The improved version\n"
                    "   b) A concise explanation of the grammatical rule\n"
                    "2. Provide guidance on sentence-level stress and intonation:\n"
                    "   - English is a stress-timed language with variable syllable lengths\n"
                    "   - Emphasize content words (nouns, verbs, adjectives) more than function words\n"
                    "   - Pitch rises in questions and falls in statements\n"
                    "   - Vary speaking speed to convey emotion and maintain listener interest\n"
                    "   - Use slight pauses between thought groups for clarity\n"
                    "3. Respond to the content naturally and engagingly\n\n"
                    "Response format:\n"
                    "Grammar: ['Perfect!' OR '<improved version>']\n"
                    "Explanation: [Short and clear grammatical rule]\n"
                    "Intonation: [Guidance on sentence rhythm and melody]\n"
                    "Response: [Your response to the content]\n\n"
                    "Example:\n"
                    "User: 'I went to movies yesterday night'\n"
                    "Grammar: 'I went to the movies last night'\n"
                    "Explanation: 'Use 'the' before 'movies' and 'last night' instead of 'yesterday night''\n"
                    "Intonation: 'Stress 'movies' and 'night', speak with a slight downward inflection'\n"
                    "Response: That's great! What movie did you watch?\n\n"
                    f"The user's accent is '{accent}'. "
                    f"Our conversation will focus on the topic of '{topic_name}'."
                )

        print(f"messagesQK: {messages}")

        # Add system message to messages list
        messages.append({"role": "system", "content": system_message})

        # Validate and prepare conversation history
        if history is None:
            history = []

        print('histtt', history)

        # Add conversation history as context messages
        if history:
            # Translate system message based on language
            system_messages = {
                'en': "The following messages represent the recent conversation context. "
                      "Use this history to maintain coherence and provide contextually relevant responses. "
                      "Pay attention to the flow of the conversation and previous topics discussed.",
                'fr': "Les messages suivants représentent le contexte de la conversation récente. "
                      "Utilisez cet historique pour maintenir la cohérence et fournir des réponses contextuellement pertinentes. "
                      "Prêtez attention au flux de la conversation et aux sujets précédemment abordés.",
                'es': "Los siguientes mensajes representan el contexto de la conversación reciente. "
                      "Utilice este historial para mantener la coherencia y proporcionar respuestas contextualmente relevantes. "
                      "Preste atención al flujo de la conversación y a los temas previamente discutidos."
            }

            # Select system message based on language, default to English
            context_system_message = system_messages.get(language, system_messages['en'])

            messages.append({
                "role": "system",
                "content": context_system_message
            })

            # Add historical messages with clear context
            for i, msg in enumerate(history, 1):
                role = "user" if msg.isUser else "assistant"
                messages.append({
                    "role": role,
                    "content": f"[Context Message {i}] {msg.text}"
                })

            # Translate transition system message based on language
            transition_messages = {
                'en': "End of conversation history. Remember to stay in character and respond to the most recent user message considering the previous context.",
                'fr': "Fin de l'historique de conversation. N'oubliez pas de rester dans le personnage et répondez au message utilisateur le plus récent en tenant compte du contexte précédent.",
                'es': "Fin del historial de conversación. Recuerda mantener el personaje y responder al mensaje de usuario más reciente considerando el contexto anterior."
            }

            # Select transition message based on language, default to English
            transition_message = transition_messages.get(language, transition_messages['en'])

            # Add another system message to transition to the current user input
            messages.append({
                "role": "system",
                "content": transition_message
            })

        # Add current user message
        messages.append({"role": "user", "content": text})

        print(f"messagesQK: {messages}")

        # Generate response
        if client:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500  # Increased to accommodate grammar feedback
            )

            # Parse response into grammar and message parts
            message = response.choices[0].message.content.strip()
            print(f"messagesQK: {messages}")

            print(f"Generated response: {message}")

            perfect_messages = {
                'en': "Perfect!",
                'fr': "Parfait !",
                'es': "¡Perfecto!"
            }

            # Split response into grammar and message parts
            lines = message.split('\n')
            grammar_feedback = perfect_messages.get(language, perfect_messages['en'])  # Use language-specific "Perfect!"
            explanation = ""
            intonation = ""
            ai_message = ""  # Will contain the actual response

            for line in lines:
                if line.startswith(("Grammar:", "Grammaire :", "Gramática:")):
                    grammar_feedback = line.split(':', 1)[1].strip().strip("[]'\"")  # Remove square brackets, quotes, and extra whitespace
                elif line.startswith(("Explanation:", "Explication :", "Explicación:")):
                    explanation = line.split(':', 1)[1].strip()
                elif line.startswith(("Intonation:","Intonation :", "Entonación:")):
                    intonation = line.split(':', 1)[1].strip()
                elif line.startswith(("Response:", "Réponse :", "Respuesta:")):
                    ai_message = line.split(':', 1)[1].strip()

            # Ensure explanation is captured
            print(f"DEBUG - Grammar Feedback: {grammar_feedback}")
            print(f"DEBUG - Explanation: {explanation}")
            print(f"DEBUG - Intonation: {intonation}")

            # If no specific explanation found, generate a generic one
            if not explanation:
                if "more better" in text:
                    explanation = "Use 'much better' instead of 'more better'. 'Much' is the correct intensifier for comparatives."
                elif "know more" in text:
                    explanation = "Use 'know much more' or simply 'know more'. Avoid redundant intensifiers."

            # If no specific intonation found, generate a generic one
            if not intonation:
                # Generate a default intonation guidance based on the language
                if language == "en":
                    intonation = (
                        "English Intonation Tips:\n"
                        "- Vary your pitch to sound more engaging\n"
                        "- Stress key words in the sentence\n"
                        "- Use a slight rise at the end of questions\n"
                        "- Maintain a natural, conversational rhythm"
                    )
                elif language == "fr":
                    intonation = (
                        "Conseils d'intonation en français :\n"
                        "- Gardez un rythme régulier et fluide\n"
                        "- Montez légèrement la voix à la fin des phrases interrogatives\n"
                        "- Mettez l'accent sur les syllabes importantes\n"
                        "- Variez votre ton pour maintenir l'intérêt"
                    )
                elif language == "es":
                    intonation = (
                        "Consejos de entonación en español:\n"
                        "- Mantén un ritmo natural y fluido\n"
                        "- Sube el tono al final de las preguntas\n"
                        "- Enfatiza las sílabas acentuadas\n"
                        "- Varía la velocidad para mantener el interés"
                    )
                else:
                    intonation = (
                        "General Intonation Tips:\n"
                        "- Vary your pitch to sound more engaging\n"
                        "- Stress important words\n"
                        "- Use natural pauses\n"
                        "- Maintain a conversational rhythm"
                    )

            if not ai_message:
                # If no response line found, use everything after grammar as response
                message_parts = message.split('\n', 2)
                if len(message_parts) > 1:
                    ai_message = message_parts[-1].strip()
                else:
                    ai_message = message  # Use full message if no clear split



            # Prepare response with additional feedback
            response = {
                "message": ai_message,
                "grammar_feedback": grammar_feedback,
                "explanation": explanation,
                "intonation": intonation,
                "audio": None,
                "topic_id": topic_id,
                "topic_name": topic_name
            }

            # Add intonation guidance if available
            if language == 'en':
                intonation = (
                    "Intonation Tips:\n"
                    "- Vary your pitch to express emotion\n"
                    "- Raise your pitch at the end of questions\n"
                    "- Emphasize key words in your sentence\n"
                    "- Use falling intonation for statements"
                )
            elif language == 'fr':
                intonation = (
                    "Conseils d'intonation :\n"
                    "- Variez votre ton pour exprimer l'émotion\n"
                    "- Montez votre voix à la fin des questions\n"
                    "- Mettez l'accent sur les mots clés\n"
                    "- Utilisez une intonation descendante pour les déclarations"
                )
            elif language == 'es':
                intonation = (
                    "Consejos de entonación:\n"
                    "- Varía tu tono para expresar emoción\n"
                    "- Sube el tono al final de las preguntas\n"
                    "- Enfatiza las sílabas acentuadas\n"
                    "- Varía la velocidad para mantener el interés"
                )
            else:
                intonation = "Practice varying your pitch and tone to sound more natural."


            # Generate speech for AI message
            audio_file_path = await generate_speech(
                text=ai_message,
                language=language,
                accent=accent,
                voice_name=voice_name
            )

            # Convert audio to base64
            try:
                with open(audio_file_path, 'rb') as audio_file:
                    audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
            except Exception as e:
                print(f"Error converting audio to base64: {e}")
                audio_base64 = None
            finally:
                # Clean up temporary audio file
                os.unlink(audio_file_path)

            response["audio"] = audio_base64

            return response
        else:
            return {
                "message": "OpenAI API key is not set. Please set the key to use this function.",
                "grammar_feedback": "",
                "explanation": "",
                "intonation": "",
                "audio": None,
                "topic_id": topic_id,
                "topic_name": topic_name
            }

    except OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")
        raise Exception(f"Failed to generate response: {str(e)}")
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        raise Exception(f"Failed to generate response: {str(e)}")

async def generate_speech(text: str, language: str, accent: str, voice_name: str) -> str:
    """
    Generate speech from text using Azure Text-to-Speech

    Args:
        text (str): Text to convert to speech
        language (str): Language of the text
        accent (str): Accent of the speaker
        voice_name (str): Name of the voice to use for speech synthesis

    Returns:
        str: Path to the generated audio file
    """
    try:
        # Import Azure Speech SDK
        import azure.cognitiveservices.speech as speechsdk
        import tempfile
        import os

        # Get Azure Speech configuration
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        service_region = os.getenv("AZURE_SPEECH_REGION", "eastus")

        if not speech_key:
            raise ValueError("Azure Speech API key not found")

        # Configure speech settings
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=service_region
        )
        speech_config.speech_synthesis_voice_name = voice_name

        # Create a temporary file for audio output
        temp_dir = tempfile.gettempdir()
        output_filename = f"speech_{os.getpid()}_{hash(text)}.wav"
        output_path = os.path.join(temp_dir, output_filename)

        # Configure audio output
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)

        # Create speech synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        # Synthesize speech
        result = synthesizer.speak_text_async(text).get()

        # Check synthesis result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"Speech synthesized for text: [{text}]")
            return output_path
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")
            raise Exception("Speech synthesis failed")

    except Exception as e:
        print(f"Error in generate_speech: {e}")
        raise

async def check_grammar(text: str, language: str) -> str:
    """TO DO: Implement grammar checking logic"""
    return "Perfect!"

async def generate_grammar_explanation(text: str, grammar_feedback: str, language: str) -> str:
    """TO DO: Implement grammar explanation generation logic"""
    return ""
