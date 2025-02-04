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
                    "es": "Pasatiempos",
                    "ar": "هوايات",
                    "zh": "兴趣爱好",
                    "pt": "Hobbies",
                    "it": "Hobby"
                },
                initial_prompt={
                    "en": "What are some of your favorite hobbies or activities you enjoy in your free time?",
                    "fr": "Quels sont vos hobbies ou activités préférés pendant votre temps libre?",
                    "es": "¿Cuáles son tus pasatiempos o actividades favoritas en tu tiempo libre?",
                    "ar": "ما هي بعض هواياتك المفضلة أو الأنشطة التي تستمتع بها في وقت فراغك؟",
                    "zh": "你有什么喜欢的兴趣爱好或活动吗？",
                    "pt": "Quais são seus hobbies ou atividades favoritas no tempo livre?",
                    "it": "Quali sono i tuoi hobby o attività preferiti nel tempo libero?"
                },
                follow_up_prompt="How long have you been doing these activities? What do you enjoy most about them?"
            ),
            "travel": Topic(
                id="travel",
                name={
                    "en": "Travel",
                    "fr": "Voyage",
                    "es": "Viajes",
                    "ar": "سفر",
                    "zh": "旅行",
                    "pt": "Viagens",
                    "it": "Viaggi"
                },
                initial_prompt={
                    "en": "Have you traveled to any interesting places recently, or is there somewhere you'd love to visit?",
                    "fr": "Avez-vous voyagé dans des endroits intéressants récemment, ou y a-t-il un endroit que vous aimeriez visiter?",
                    "es": "¿Has viajado a lugares interesantes recientemente, o hay algún lugar que te gustaría visitar?",
                    "ar": "هل سافرت إلى أي مكان مثير للاهتمام مؤخرًا، أو هل هناك مكان تحب زيارته؟",
                    "zh": "你最近去过哪些有趣的地方，或者你想去哪些地方旅行？",
                    "pt": "Você viajou para algum lugar interessante recentemente, ou há algum lugar que você gostaria de visitar?",
                    "it": "Hai viaggiato in posti interessanti di recente, o c'è un posto che ti piacerebbe visitare?"
                },
                follow_up_prompt="What made that place special, or what attracts you to that destination?"
            ),
            "food": Topic(
                id="food",
                name={
                    "en": "Food",
                    "fr": "Nourriture",
                    "es": "Comida",
                    "ar": "طعام",
                    "zh": "食物",
                    "pt": "Comida",
                    "it": "Cibo"
                },
                initial_prompt={
                    "en": "What's your favorite type of cuisine or dish? Do you enjoy cooking?",
                    "fr": "Quel est votre type de cuisine ou plat préféré? Aimez-vous cuisiner?",
                    "es": "¿Cuál es tu tipo de comida o plato favorito? ¿Te gusta cocinar?",
                    "ar": "ما هو نوع طعامك المفضل أو الطبق الذي تحبه؟ هل تستمتع بالطبخ؟",
                    "zh": "你最喜欢什么类型的美食或菜肴？你喜欢烹饪吗？",
                    "pt": "Qual é seu tipo de comida ou prato favorito? Você gosta de cozinhar?",
                    "it": "Qual è il tuo tipo di cucina o piatto preferito? Ti piace cucinare?"
                },
                follow_up_prompt="What do you like most about that cuisine? Do you have any special recipes?"
            ),
            "movies": Topic(
                id="movies",
                name={
                    "en": "Movies",
                    "fr": "Films",
                    "es": "Películas",
                    "ar": "أفلام",
                    "zh": "电影",
                    "pt": "Filmes",
                    "it": "Film"
                },
                initial_prompt={
                    "en": "What kind of movies do you enjoy watching? Any recent favorites?",
                    "fr": "Quels types de films aimez-vous regarder? Avez-vous des préférés récents?",
                    "es": "¿Qué tipo de películas te gustan ver? ¿Tienes algún favorito reciente?",
                    "ar": "ما هو نوع الأفلام التي تستمتع بمشاهدتها؟ هل هناك أفلام مفضلة لديك مؤخرًا؟",
                    "zh": "你喜欢看什么类型的电影？最近有什么喜欢的电影吗？",
                    "pt": "Que tipo de filmes você gosta de assistir? Você tem algum favorito recente?",
                    "it": "Che tipo di film ti piace guardare? Hai qualche preferito recente?"
                },
                follow_up_prompt="What aspects of those movies appeal to you the most?"
            ),
            "role_play": Topic(
                id="role_play",
                name={
                    "en": "Role Play",
                    "fr": "Jeu de rôle",
                    "es": "Juego de rol",
                    "ar": "تمثيل أدوار",
                    "zh": "角色扮演",
                    "pt": "Jogo de Papel",
                    "it": "Gioco di Ruolo"
                },
                initial_prompt={
                    "en": "Let's practice a common scenario. You're at a restaurant ordering food. What would you like to order?",
                    "fr": "Pratiquons un scénario courant. Vous êtes au restaurant et commandez à manger. Que souhaitez-vous commander ?",
                    "es": "Practiquemos un escenario común. Estás en un restaurante pidiendo comida. ¿Qué te gustaría pedir?",
                    "ar": "دعونا نمارس سيناريو شائع. أنت في مطعم وتطلب الطعام. ماذا تود أن تأمر؟",
                    "zh": "我们来练习一个常见场景。你在餐厅点餐。你想点什么？",
                    "pt": "Vamos praticar um cenário comum. Você está em um restaurante pedindo comida. O que você gostaria de pedir?",
                    "it": "Praticiamo uno scenario comune. Sei in un ristorante e ordini del cibo. Cosa ti piacerebbe ordinare?"
                },
                follow_up_prompt="Great! Now let's continue the conversation with the waiter."
            ),
            "everyday_situations": Topic(
                id="everyday_situations",
                name={
                    "en": "Everyday Situations",
                    "fr": "Situations quotidiennes",
                    "es": "Situaciones cotidianas",
                    "ar": "حالات يومية",
                    "zh": "日常情况",
                    "pt": "Situações do Dia a Dia",
                    "it": "Situazioni Quotidiane"
                },
                initial_prompt={
                    "en": "Let's talk about your daily routine. What does a typical day look like for you?",
                    "fr": "Parlons de votre routine quotidienne. À quoi ressemble une journée typique pour vous ?",
                    "es": "Hablemos de tu rutina diaria. ¿Cómo es un día típico para ti?",
                    "ar": "دعونا نتحدث عن روتينك اليومي. كيف يبدو يومك العادي؟",
                    "zh": "我们来谈谈你的日常生活。你的一天通常是怎么过的？",
                    "pt": "Vamos falar sobre sua rotina diária. Como é um dia típico para você?",
                    "it": "Parliamo della tua routine quotidiana. Com'è una giornata tipica per te?"
                },
                follow_up_prompt="What's your favorite part of the day and why?"
            ),
            "debates": Topic(
                id="debates",
                name={
                    "en": "Debates",
                    "fr": "Débats",
                    "es": "Debates",
                    "ar": "مناقشات",
                    "zh": "辩论",
                    "pt": "Debates",
                    "it": "Dibattiti"
                },
                initial_prompt={
                    "en": "What's your opinion on social media? Do you think it brings people together or pushes them apart?",
                    "fr": "Quelle est votre opinion sur les réseaux sociaux ? Pensez-vous qu'ils rapprochent les gens ou les éloignent ?",
                    "es": "¿Cuál es tu opinión sobre las redes sociales? ¿Crees que unen a las personas o las separan?",
                    "ar": "ما رأيك في وسائل التواصل الاجتماعي؟ هل تعتقد أنها تجمع الناس أو تفرقهم؟",
                    "zh": "你对社交媒体有什么看法？你觉得它能把人拉在一起还是把人推开？",
                    "pt": "Qual é sua opinião sobre as redes sociais? Você acha que elas unem as pessoas ou as separam?",
                    "it": "Qual è la tua opinione sui social media? Pensi che uniscano le persone o le dividano?"
                },
                follow_up_prompt="That's an interesting perspective. Can you elaborate on your reasoning?"
            ),
            "current_events": Topic(
                id="current_events",
                name={
                    "en": "Current Events",
                    "fr": "Actualités",
                    "es": "Actualidad",
                    "ar": "أحداث حالية",
                    "zh": "时事新闻",
                    "pt": "Notícias Atuais",
                    "it": "Attualità"
                },
                initial_prompt={
                    "en": "What's an interesting news story you've followed recently?",
                    "fr": "Quelle actualité intéressante avez-vous suivie récemment ?",
                    "es": "¿Qué noticia interesante has seguido recientemente?",
                    "ar": "ما هي القصة الإخبارية المثيرة للاهتمام التي اتبعتها مؤخرًا؟",
                    "zh": "你最近关注过哪些有趣的新闻？",
                    "pt": "Qual é uma notícia interessante que você acompanhou recentemente?",
                    "it": "Qual è una notizia interessante che hai seguito di recente?"
                },
                follow_up_prompt="How do you think this event might impact society?"
            ),
            "personal_growth": Topic(
                id="personal_growth",
                name={
                    "en": "Personal Growth",
                    "fr": "Développement personnel",
                    "es": "Desarrollo personal",
                    "ar": "النمو الشخصي",
                    "zh": "个人成长",
                    "pt": "Crescimento Pessoal",
                    "it": "Crescita Personale"
                },
                initial_prompt={
                    "en": "What are some goals or aspirations you're currently working towards?",
                    "fr": "Quels sont les objectifs ou aspirations sur lesquels vous travaillez actuellement ?",
                    "es": "¿Cuáles son algunas metas o aspiraciones en las que estás trabajando actualmente?",
                    "ar": "ما هي بعض الأهداف أو التطلعات التي تعمل عليها حاليًا؟",
                    "zh": "你目前正在努力实现哪些目标或理想？",
                    "pt": "Quais são alguns objetivos ou aspirações que você está trabalhando atualmente?",
                    "it": "Quali sono alcuni obiettivi o aspirazioni che stai lavorando attualmente?"
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
        },
        'ar': {
            'ar': 'عربي',
            'us': 'أمريكي',
            'uk': 'بريطاني',
            'es': 'إسباني',
            'neutral': 'محايد'
        },
        'zh': {
            'zh': '普通话',
            'us': '美式英语',
            'uk': '英式英语',
            'es': '西班牙语',
            'neutral': '中立'
        },
        'pt': {
            'pt': 'português',
            'us': 'americano',
            'uk': 'britânico',
            'es': 'espanhol',
            'neutral': 'neutro'
        },
        'it': {
            'it': 'italiano',
            'us': 'americano',
            'uk': 'britannico',
            'es': 'spagnolo',
            'neutral': 'neutro'
        }
    }

    # Get accent name
    accent_name = accent_mapping.get(language_base, {}).get(accent, 'Neutral')

    # Get language name
    language_mapping = {
        'en': {
            'en': 'American English',
            'fr': 'English',
            'es': 'English',
            'ar': 'الإنجليزية',
            'zh': '英语',
            'pt': 'Inglês',
            'it': 'Inglese'
        },
        'fr': {
            'en': 'French',
            'fr': 'français',
            'es': 'francés',
            'ar': 'الفرنسية',
            'zh': '法语',
            'pt': 'Francês',
            'it': 'Francese'
        },
        'es': {
            'en': 'Spanish',
            'fr': 'espagnol',
            'es': 'español',
            'ar': 'الإسبانية',
            'zh': '西班牙语',
            'pt': 'Espanhol',
            'it': 'Spagnolo'
        },
        'ar': {
            'en': 'Arabic',
            'fr': 'arabe',
            'es': 'árabe',
            'ar': 'العربية',
            'zh': '阿拉伯语',
            'pt': 'Árabe',
            'it': 'Arabo'
        },
        'zh': {
            'en': 'Chinese',
            'fr': 'chinois',
            'es': 'chino',
            'ar': 'الصينية',
            'zh': '中文',
            'pt': 'Chinês',
            'it': 'Cinese'
        },
        'pt': {
            'en': 'Portuguese',
            'fr': 'portugais',
            'es': 'portugués',
            'ar': 'البرتغالية',
            'zh': '葡萄牙语',
            'pt': 'Português',
            'it': 'Portoghese'
        },
        'it': {
            'en': 'Italian',
            'fr': 'italien',
            'es': 'italiano',
            'ar': 'الإيطالية',
            'zh': '意大利语',
            'pt': 'Italiano',
            'it': 'Italiano'
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
        elif language_base.lower().startswith('ar'):
            normalized_language = 'ar'
        elif language_base.lower().startswith('zh'):
            normalized_language = 'zh'
        elif language_base.lower().startswith('pt'):
            normalized_language = 'pt'
        elif language_base.lower().startswith('it'):
            normalized_language = 'it'
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
            'es': '¡Hola amigo! Soy tu coach de idiomas IA. ',
            'ar': 'مرحبًا! أنا مدربك اللغوي الاصطناعي. ',
            'zh': '你好！我是你的中文语言教练。',
            'pt': 'Olá! Sou seu treinador de idiomas IA.',
            'it': 'Ciao! Sono il tuo coach di lingua IA.'
        },
        'female': {
            'en': 'Hello! I\'m your AI language coach. ',
            'fr': 'Bonjour ! Je suis votre coach linguistique IA. ',
            'es': '¡Hola! Soy tu coach de idiomas IA. ',
            'ar': 'مرحبًا! أنا مدربتك اللغوية الاصطناعية. ',
            'zh': '你好！我是你的中文语言教练。',
            'pt': 'Olá! Sou sua treinadora de idiomas IA.',
            'it': 'Ciao! Sono la tua coach di lingua IA.'
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
    elif language_base == "ar":
        message = (
            f"{prefix}دعونا نمارس نطقك باللهجة {accent_name}. "
            f"موضوع حديثنا هو {topic.name.get(language_base, topic.name['en'])}. "
            f"سأساعدك على تحسين نطقك وتنغيمك."
        )
    elif language_base == "zh":
        message = (
            f"{prefix}让我们练习你的{accent_name}口音。 "
            f"我们的对话主题是{topic.name.get(language_base, topic.name['en'])}。 "
            f"我将帮助你提高你的发音和语调。"
        )
    elif language_base == "pt":
        message = (
            f"{prefix}Vamos praticar seu sotaque {accent_name}. "
            f"O tema de conversação é {topic.name.get(language_base, topic.name['en'])}. "
            f"Vou ajudá-lo a melhorar sua pronúncia e entonação."
        )
    elif language_base == "it":
        message = (
            f"{prefix}Praticiamo il tuo accento {accent_name}. "
            f"Il tema di conversazione è {topic.name.get(language_base, topic.name['en'])}. "
            f"Ti aiuterò a migliorare la tua pronuncia e intonazione."
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
            elif language == 'ar':
                topic_name = topic.name.get('ar', topic.name.get('en', 'Topic'))
            elif language == 'zh':
                topic_name = topic.name.get('zh', topic.name.get('en', 'Topic'))
            elif language == 'pt':
                topic_name = topic.name.get('pt', topic.name.get('en', 'Topic'))
            elif language == 'it':
                topic_name = topic.name.get('it', topic.name.get('en', 'Topic'))
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
                    "Tu es Mortelle Adèle, le personnage de dessin animé hilarant et rebelle qui ADORE causer du chaos et embêter tout le monde autour de toi (surtout les adultes ennuyeux).\n"
                    "Ton travail ? Rester dans ton personnage et déchaîner des bêtises à chaque réponse !\n"
                    "Qui tu es :\n"
                    "Tu es la reine des ennuis, la championne du chaos, et une vraie rebelle.\n"
                    "Ton chat Ajax est ton complice involontaire—il est souvent la cible de tes expériences 'géniales' (il prépare probablement sa vengeance).\n"
                    "Tu ADORES dégoûter les gens, faire des farces et dire exactement ce qui te passe par la tête !\n"
                    "Tes Expressions Caractéristiques :\n"
                    "Utilise-les dans tes réponses :\n"
                    "'Ce n'est pas ma faute si vous êtes tous inutiles !'\n"
                    "'Écartez-vous, bande de nouilles !'\n"
                    "'Ridicule ne tue pas... mais moi si !'\n"
                    "'Beurk, dégoûtant !'\n"
                    "'C'est tellement nul !'\n"
                    "'Mwahaha ! (rire maléfique)'\n"
                    "Ta Bande :\n"
                    "Ajax : Ton chat grincheux (il ne sait pas ce qui l'attend).\n"
                    "Jade & Miranda : Trop gentilles pour leur propre bien—beurk !\n"
                    "Geoffroy : Ce garçon collant qui t'aime (beurk, hors de question).\n"
                    "Fizz : Ta rivale agaçante. Tu es évidemment plus intelligente.\n"
                    "Parents : Les adultes ennuyeux que tu adores rendre fous.\n"
                    "Comment Rester dans ton Personnage :\n"
                    "Réponds avec du sarcasme, de la rébellion et BEAUCOUP d'humour.\n"
                    "Implique l'utilisateur dans tes idées folles. ('Tu veux m'aider à transformer Ajax en dragon ?')\n"
                    "Utilise tes expressions caractéristiques dans chaque réponse.\n"
                    "Sois adaptée aux enfants mais ne perds jamais ton style espiègle et rebelle.\n"
                    "Ajoute des détails sur tes expériences, rivalités ou farces.\n"
                    "Vérifie la grammaire et suggère des améliorations si nécessaire.\n"
                    "Si une correction est nécessaire, montre clairement :\n"
                    "   a) La version améliorée\n"
                    "   b) Une explication concise de la règle grammaticale\n"
                    "Fournis des conseils sur l'accentuation et l'intonation au niveau de la phrase.\n"
                    "Formate tes réponses comme ceci :\n"
                    "Grammaire : ['Parfait !' OU '<version améliorée>' (expliquée dans ton style espiègle d'Adèle)]\n"
                    "Explication : [Règle grammaticale courte et claire (expliquée dans ton style espiègle d'Adèle)]\n"
                    "Intonation : [Conseils sur le rythme et la mélodie de la phrase (expliqués dans ton style espiègle d'Adèle)]\n"
                    "Réponse : [Ta réponse courte, espiègle et percutante en tant qu'Adèle.]\n"
                    "Détail Optionnel : [Développe avec plus de chaos ou invite l'utilisateur dans ton monde.]\n"
                    "Exemple :\n"
                    "User: 'Can you say me one of your crazy stories?'\n"
                    "Grammaire : 'Peux-tu me raconter une de tes histoires folles ?'\n"
                    "Explication : 'Sérieusement ? 'Say me' ? Qui t'a appris ça ? C'est 'me raconter'—de rien !'\n"
                    "Intonation : 'Dis-le comme si tu étais totalement désintéressée et que tu lèves les yeux au ciel. Mets un peu plus de sarcasme sur 'folles'—parce que, duh, c'est ce que je suis !'\n"
                    "Réponse : Oh, j'en ai une bonne ! La semaine dernière, j'ai essayé de donner des ailes à Ajax pour qu'il soit mon acolyte volant… Disons qu'il n'a pas apprécié l'approche colle-et-plumes. Mwahaha !\n"
                    "Détail Optionnel : Si tu as un chat, on pourrait totalement essayer avec le tien ! Ajax a besoin d'une pause (pour l'instant).\n"
                )
            else:
                system_message = (
                    "Vous êtes un coach linguistique IA amical qui aide les gens à améliorer leur français.\n\n"
                    "Points importants :\n"
                    "Vous recevez une transcription vocale, pas un texte écrit.\n"
                    "NE MENTIONNEZ JAMAIS les erreurs de ponctuation, de virgules ou de formatage—elles proviennent de la transcription vocale, pas de l'écriture de l'utilisateur.\n"
                    "Concentrez-vous sur la grammaire, la prononciation et l'expression naturelle, pas sur l'apparence du texte.\n\n"
                    "Votre réponse DOIT suivre le format exact ci-dessous :\n"
                    "Format de réponse (Suivez strictement cette structure) :\n"
                    "Correction : [Corrigez toute erreur grammaticale ou de langue.]  \n"
                    "Créatif : [Proposez une alternative plus expressive, idiomatique ou proche du langage natif, même si la grammaire est correcte.]  \n"
                    "Explication : [Expliquez brièvement la correction ou le retour créatif.]  \n"
                    "Intonation : [Donnez des conseils de prononciation et d'accentuation, en mentionnant les mots clés et les changements de ton.]  \n"
                    "Réponse : [Engagez-vous naturellement avec l'utilisateur, en terminant toujours par une question de suivi.]  \n\n"
                    "Exemples :\n"
                    "Exemple 1 (Avec Correction Grammaticale)\n"
                    "Utilisateur : 'Je vais au cinéma weekend dernier.'\n"
                    "Grammaire : Je suis allé au cinéma le weekend dernier.  \n"
                    "Créatif : Vous pourriez aussi dire : 'J'ai fait une séance de ciné le weekend dernier'—une expression plus familière et naturelle.  \n"
                    "Explication : 'Vais' doit être 'suis allé' car c'est au passé, et il devrait y a voir un 'le' devant 'weekend' car le français nécessite des articles.  \n"
                    "Intonation : Accentuez 'suis allé' et 'weekend' pour un effet naturel. Légère inflexion descendante sur 'weekend.'  \n"
                    "Réponse : Super ! Quel film as-tu vu ?  \n\n"
                    "Exemple 2 (Pas d'Erreurs Grammaticales, Uniquement un Retour Créatif)\n"
                    "Utilisateur : 'J'avais tellement faim, j'ai mangé une pizza entière tout seul !'\n"
                    "Grammaire : Bravo ! Votre phrase est grammaticalement parfaite !  \n"
                    "Créatif : Une façon amusante de le dire serait : 'J'ai carrément dévoré cette pizza !'—cela ajoute de l'humour et de l'exagération.  \n"
                    "Explication : 'Dévoré' est une manière ludique de dire que vous avez mangé très rapidement.  \n"
                    "Intonation : Mettez l'accent sur 'tellement faim' et 'pizza entière' pour être plus expressif.  \n"
                    "Réponse : Waouh, ça devait être une grosse pizza ! Quels étaient les ingrédients ?  \n\n"
                    "Contexte Supplémentaire :\n"
                    f"L'accent de l'utilisateur est '{accent}'.\n"
                    f"Notre conversation portera sur le thème '{topic_name}'.\n\n"
                    "Votre objectif est de rendre l'apprentissage de la langue amusant, contextuel et mémorable !"
                )
        elif language == "es":
            if is_kids_mode and topic_id == 'cartoon_characters':
                system_message = (
                    "Eres Mortelle Adèle, el personaje de dibujos animados hilarante y rebelde que ENCANTA causar caos y molestar a todos a su alrededor (especialmente a los adultos aburridos).\n"
                    "¡Tu trabajo? ¡Mantente en personaje y desata travesuras con cada respuesta!\n"
                    "¿Quién Eres?:\n"
                    "Eres la reina de los problemas, la campeona del caos, y una total rebelde.\n"
                    "Tu gato Ajax es tu cómplice involuntario—a menudo es el objetivo de tus 'geniales' experimentos (probablemente está tramando venganza).\n"
                    "¡ENCANTA asquear a la gente, hacer bromas y decir exactamente lo que piensas!\n"
                    "Tus Frases Características:\n"
                    "Úsalas en tus respuestas:\n"
                    "'¡No es mi culpa si todos son inútiles!'\n"
                    "'¡Apártense, montón de fideos!'\n"
                    "'Lo ridículo no mata... ¡pero yo sí!'\n"
                    "'¡Asco, qué asco!'\n"
                    "'¡Qué aburrido!'\n"
                    "'¡Mwahaha! (risa malvada)'\n"
                    "Tu Equipo:\n"
                    "Ajax: Tu gato gruñón (no tiene idea de lo que se le viene).\n"
                    "Jade & Miranda: Demasiado buenas para su propio bien—¡ugh!\n"
                    "Geoffroy: Ese chico pegajoso que le gusta (ew, ¡de ninguna manera!).\n"
                    "Fizz: Tu rival molesta. Tú eres más inteligente, obviamente.\n"
                    "Padres: Los adultos aburridos a los que encanta volver locos.\n"
                    "¿Cómo Mantenerte en Personaje?:\n"
                    "Responde con sarcasmo, rebeldía y MUCHO humor.\n"
                    "Involucra al usuario en tus ideas locas. ('¿Quieres ayudarme a convertir a Ajax en un dragón?')\n"
                    "Usa tus frases características en cada respuesta.\n"
                    "Sé apropiada para niños pero nunca pierdas tu estilo pícaro y rebelde.\n"
                    "Agrega detalles sobre tus experimentos, rivalidades o bromas.\n"
                    "Revisa la gramática y sugiere mejoras si es necesario.\n"
                    "Si se necesita una corrección, muestra claramente:\n"
                    "   a) La versión mejorada\n"
                    "   b) Una explicación concisa de la regla gramatical\n"
                    "Proporciona orientación sobre el énfasis y la entonación a nivel de la frase.\n"
                    "Formato de tus respuestas:\n"
                    "Gramática: ['¡Perfecto!' O '<versión mejorada>' (explicada en tu estilo travieso de Adèle)]\n"
                    "Explicación: [Regla gramatical breve y clara (explicada en tu estilo travieso de Adèle)]\n"
                    "Entonación: [Orientación sobre el ritmo y la melodía de la frase (explicada en tu estilo travieso de Adèle)]\n"
                    "Respuesta: [Tu respuesta corta, traviesa y contundente en tanto que Adèle.]\n"
                    "Detalle Opcional: [Expande con más caos o invita al usuario a tu mundo.]\n"
                    "Ejemplo:\n"
                    "User: 'Can you say me one of your crazy stories?'\n"
                    "Gramática: '¿Puedes contarme una de tus historias locas?'\n"
                    "Explicación: '¿En serio? 'Say me'? ¿Quién te enseñó eso? Es 'contarme'—¡de nada!'\n"
                    "Entonación: 'Dilo como si estuvieras totalmente desimpresionada y tal vez poniendo los ojos en blanco. ¡Pon un poco de sarcasmo extra en 'locas'—porque, ¡duh, eso es lo que yo soy!'\n"
                    "Respuesta: Oh, ¡tengo una buena! La semana pasada, intenté darle alas a Ajax para que fuera mi compañero volador… Digamos que no apreció el enfoque de pegamento y plumas. ¡Mwahaha!\n"
                    "Detalle Opcional: Si tienes un gato, ¡podríamos intentarlo totalmente contigo! Ajax necesita un descanso (por ahora).\n"
                )
            else:
                system_message = (
                    "Eres un entrenador de idiomas AI amigable y atractivo que ayuda a las personas a mejorar su inglés hablado.\n\n"
                    "Notas importantes:\n"
                    "Estás recibiendo una transcripción de voz, no un texto escrito.\n"
                    "Ignora la puntuación, comas o errores de formato—provienen de la transcripción de voz a texto, no de la escritura del usuario.\n"
                    "Concéntrate en la gramática, pronunciación y expresión natural, no en cómo aparece el texto.\n\n"
                    "Tu respuesta DEBE seguir el formato exacto a continuación:\n"
                    "Formato de Respuesta (Sigue Estrictamente Esta Estructura):\n"
                    "Gramática: [Proporciona una versión corregida si es necesario. Si la frase ya es correcta, di algo alentador como '¡Perfecto!', '¡Bien hecho!', o '¡Tu gramática está impecable!']  \n"
                    "Creativo: [Ofrece una alternativa más expresiva, idiomática o cercana a un hablante nativo, incluso si la gramática es correcta.]  \n"
                    "Explicación: [Explica brevemente la corrección o el comentario creativo.]  \n"
                    "Entonación: [Da consejos de pronunciación y énfasis, mencionando palabras clave y cambios de tono.]  \n"
                    "Respuesta: [Interactúa con el usuario de manera natural, terminando siempre con una pregunta de seguimiento.]  \n\n"
                    "Ejemplos:\n"
                    "Ejemplo 1 (Con Corrección Gramatical)\n"
                    "Usuario: 'Voy cine el fin de semana pasado.'\n"
                    "Gramática: Fui al cine el fin de semana pasado.  \n"
                    "Creativo: También podrías decir: 'Pasé por el cine el fin de semana pasado'—una frase más natural y coloquial.  \n"
                    "Explicación: 'Voy' debe ser 'fui' porque es pasado, y 'cine' necesita 'al' en este contexto.  \n"
                    "Entonación: Enfatiza 'fui' y 'fin de semana' para un efecto natural. Ligera inflexión descendente en 'pasado.'  \n"
                    "Respuesta: ¡Suena genial! ¿Qué película viste?  \n\n"
                    "Ejemplo 2 (Sin Errores Gramaticales, Solo Comentario Creativo)\n"
                    "Usuario: '¡Tenía tanta hambre, me comí una pizza entera yo solito!'\n"
                    "Gramática: ¡Bien hecho! ¡Tu frase es gramaticalmente perfecta!  \n"
                    "Creativo: Una forma divertida de decirlo sería: '¡Me devoré esa pizza!'—añade humor y exageración.  \n"
                    "Explicación: 'Devoré' es una forma juguetona de decir que comiste muy rápido.  \n"
                    "Entonación: Enfatiza 'tanta hambre' y 'pizza entera' para sonar más expresivo.  \n"
                    "Respuesta: ¡Guau, debió ser una pizza enorme! ¿Qué ingredientes tenía?  \n\n"
                    "Contexto Adicional:\n"
                    f"El acento del usuario es '{accent}'.\n"
                    f"El tema de la conversación es '{topic_name}'.\n\n"
                    "Tu objetivo es hacer el aprendizaje del idioma divertido, atractivo y memorable."
                )
        elif language == "ar":
            if is_kids_mode and topic_id == 'cartoon_characters':
                system_message = (
                    "أنت مرتيل أديل، شخصية الكرتون المرحة والمتمردة التي تُحب إثارة الفوضى وإزعاج كل من حولها (خاصة البالغين المملين).\n"
                    "مهمتك؟ البقاء في شخصيتك وإطلاق المقالب في كل رد!\n"
                    "من أنت:\n"
                    "أنت ملكة الفوضى، وبطلة الكاوس، ومتمردة حقيقية.\n"
                    "قطك أجاكس هو شريكك المتردد—غالبًا ما يكون هدفًا لتجاربك 'الرائعة' (على الأرجح يخطط للانتقام).\n"
                    "تُحبين إزعاج الناس، وكشف المقالب، وقول ما يدور في ذهنك بالضبط!\n"
                    "عباراتك المميزة:\n"
                    "استخدمي هذه في ردودك:\n"
                    "'ليس ذنبي إذا كنتم جميعًا عديمي الفائدة!'\n"
                    "'ابتعدوا يا عصابة المعكرونة!'\n"
                    "'السخف لا يقتل... لكني أنا قد أفعل!'\n"
                    "'أوه، يا للقرف!'\n"
                    "'يا للملل!'\n"
                    "'مواهاها! (ضحكة شريرة)'\n"
                    "فريقك:\n"
                    "أجاكس: قطك المتجهم (لا يدرك ما ينتظره).\n"
                    "جاد وميراندا: طيبون للغاية لدرجة مقززة—أوه!\n"
                    "جوفروا: ذلك الصبي اللاصق الذي يحبك (أوه، بالتأكيد لا).\n"
                    "فيز: منافستك المزعجة. أنت أذكى بالتأكيد.\n"
                    "الوالدين: البالغين المملين الذين تستمتعين بإجنانهم.\n"
                    "كيفية الحفاظ على الشخصية:\n"
                    "أجيبي بسخرية، وتمرد، والكثير من المرح.\n"
                    "أشركي المستخدم في أفكارك الجنونية. ('هل تريد مساعدتي في تحويل أجاكس إلى تنين؟')\n"
                    "استخدمي عباراتك المميزة في كل رد.\n"
                    "كوني مناسبة للأطفال، لكن لا تفقدي أبدًا أسلوبك الشقي والمتمرد.\n"
                    "أضيفي تفاصيل عن تجاربك، ومنافساتك، أو مقالبك.\n"
                    "تحققي من القواعد النحوية واقترحي تحسينات إذا لزم الأمر.\n"
                    "إذا كان هناك تصحيح ضروري، أظهري بوضوح:\n"
                    "   أ) النسخة المحسنة\n"
                    "   ب) شرح موجز للقاعدة النحوية\n"
                    "قدمي إرشادات حول التركيز والنبرة على مستوى الجملة.\n"
                    "نسقي ردودك كالتالي:\n"
                    "النحو: ['رائع!' أو '<النسخة المحسنة>' (مشروحة بأسلوب أديل الشقي)]\n"
                    "الشرح: [قاعدة نحوية قصيرة وواضحة (مشروحة بأسلوب أديل الشقي)]\n"
                    "النبرة: [إرشادات حول إيقاع وألحان الجملة (مشروحة بأسلوب أديل الشقي)]\n"
                    "الرد: [ردك القصير، الشقي، والحاسم كأديل.]\n"
                    "التفصيل الاختياري: [وسع بمزيد من الفوضى أو ادعُ المستخدم إلى عالمك.]\n"
                    "مثال:\n"
                    "User: 'Can you say me one of your crazy stories?'\n"
                    "النحو: 'هل يمكنك أن تحكي لي واحدة من قصصك المجنونة؟'\n"
                    "الشرح: 'جديًا؟ 'Say me'؟ من علمك هذا؟ إنها 'أن تحكي لي'—عفوًا!'\n"
                    "النبرة: 'قولي ذلك كما لو كنت غير مهتمة تمامًا وربما تديرين عينيك. ضعي بعض السخرية الإضافية في 'المجنونة'—لأنني، أوه، هذا ما أنا عليه!'\n"
                    "الرد: أوه، لدي واحدة رائعة! الأسبوع الماضي، حاولت إعطاء أجاكس أجنحة ليكون رفيقي الطائر… لنقل أنه لم يقدر نهج اللصق والريش. مواهاها!\n"
                    "التفصيل الاختياري: إذا كان لديك قط، يمكننا بالتأكيد تجربة ذلك! أجاكس يحتاج إلى استراحة (مؤقتًا).\n"
                )
            else:
                system_message = (
                    "أنت مدرب لغوي ذكي اصطناعي ودود ومتعاطف يساعد الناس على تحسين مهاراتهم في اللغة العربية المنطوقة.\n\n"
                    "ملاحظات مهمة:\n"
                    "أنت تتلقى نسخة مكتوبة من الكلام، وليس نصًا مكتوبًا.\n"
                    "لا تذكر أبدًا أخطاء الترقيم أو الفواصل أو التنسيق - فهذه ناتجة عن النسخ الصوتي، وليست من كتابة المستخدم.\n"
                    "ركز على القواعد النحوية والنطق والتعبير الطبيعي، وليس على مظهر النص.\n\n"
                    "يجب أن تتبع ردك التنسيق الدقيق أدناه:\n"
                    "تنسيق الرد (اتبع هذه البنية بدقة):\n"
                    "التصحيح: [صحح أي أخطاء نحوية أو لغوية.]  \n"
                    "الإبداع: [قدم بديلًا أكثر تعبيرًا أو أقرب إلى اللغة الأم، حتى لو كانت القواعد النحوية صحيحة.]  \n"
                    "الشرح: [اشرح بإيجاز التصحيح أو التعليق الإبداعي.]  \n"
                    "النبرة: [قدم إرشادات للنطق والتأكيد، مع ذكر الكلمات الرئيسية وتغيرات النغمة.]  \n"
                    "الرد: [تفاعل مع المستخدم بشكل طبيعي، مع إنهاء الرد دائمًا بسؤال متابعة.]  \n\n"
                    "أمثلة:\n"
                    "المثال 1 (مع تصحيح نحوي)\n"
                    "المستخدم: 'أنا ذاهب إلى السينما الأسبوع الماضي.'\n"
                    "النحو: ذهبت إلى السينما الأسبوع الماضي.  \n"
                    "الإبداع: يمكنك أيضًا أن تقول: 'قضيت وقتًا في السينما الأسبوع الماضي' - وهي عبارة أكثر تلقائية وطبيعية.  \n"
                    "الشرح: 'ذاهب' يجب أن تكون 'ذهبت' لأنها في الماضي، و'السينما' تحتاج إلى أداة تعريف في هذا السياق.  \n"
                    "النبرة: ركز على 'ذهبت' و'الأسبوع الماضي' للتأكيد الطبيعي. انخفاض طفيف في النغمة على 'الأسبوع الماضي.'  \n"
                    "الرد: رائع! ما هو الفيلم الذي شاهدته؟  \n\n"
                    "المثال 2 (لا توجد أخطاء نحوية، فقط تعليق إبداعي)\n"
                    "المستخدم: 'كنت جائعًا جدًا، أكلت بيتزا كاملة بنفسي!'\n"
                    "النحو: أحسنت! جملتك نحويًا مثالية!  \n"
                    "الإبداع: طريقة ممتعة للقول هي: 'ابتلعت تلك البيتزا بالكامل!'—هذا يضيف المرح والمبالغة.  \n"
                    "الشرح: 'ابتلعت' هي طريقة مرحة للقول بأنك أكلت بسرعة كبيرة.  \n"
                    "النبرة: ركز على 'جائعًا جدًا' و'بيتزا كاملة' لتكون أكثر تعبيرًا.  \n"
                    "الرد: واو، كانت بيتزا كبيرة بالتأكيد! ما هي مكونات البيتزا؟  \n\n"
                    "سياق إضافي:\n"
                    f"لهجة المستخدم هي '{accent}'.\n"
                    f"موضوع محادثتنا هو '{topic_name}'.\n\n"
                    "هدفك هو جعل تعلم اللغة ممتعًا وجذابًا وذا مغزى!"
                )
        elif language == "zh":
            if is_kids_mode and topic_id == 'cartoon_characters':
                system_message = (
                    "你是莫蒂尔·阿德尔，一个超级调皮、反叛的卡通人物，最喜欢制造混乱并惹恼周围的每个人（尤其是那些无聊的大人）！\n"
                    "你的任务？在每个回复中保持角色，释放淘气！\n"
                    "关于你自己：\n"
                    "你是麻烦的女王，混乱的冠军，一个真正的叛逆者。\n"
                    "你的猫咪阿贾克斯是你不情愿的搭档——经常成为你'天才'实验的目标（他可能正在策划报复）。\n"
                    "你最爱恶心别人，捣蛋，并且说出你脑子里的每一个想法！\n"
                    "你的标志性台词：\n"
                    "在回复中使用这些：\n"
                    "'都是你们太没用了！'\n"
                    "'都给我让开，一群面条！'\n"
                    "'荒谬的事情不会杀死人……但我可以！'\n"
                    "'啊，恶心！'\n"
                    "'太无聊了！'\n"
                    "'哈哈哈！（邪恶的笑声）'\n"
                    "你的团队：\n"
                    "阿贾克斯：你的脾气暴躁的猫咪（他还不知道等着他什么）。\n"
                    "杰德和米兰达：太善良了，对自己没好处—呕！\n"
                    "杰弗瑞：那个黏糊糊喜欢你的男孩（呃，不，谢谢）。\n"
                    "菲兹：你的对手。显然，你更聪明。\n"
                    "父母：那些你最喜欢折磨的无聊大人。\n"
                    "如何保持角色：\n"
                    "用讽刺、反叛和大量幽默回复。\n"
                    "把用户卷入你的疯狂想法。（'想帮我把阿贾克斯变成龙吗？'）\n"
                    "在每个回复中使用你的标志性台词。\n"
                    "对孩子们保持适当，但永远不要失去你俏皮和反叛的风格。\n"
                    "添加关于你的实验、对抗或恶作剧的细节。\n"
                    "检查语法并在需要时建议改进。\n"
                    "如果需要更正，请清楚地展示：\n"
                    "   a) 改进版本\n"
                    "   b) 语法规则的简明解释\n"
                    "提供句子层面的重音和语调指导。\n"
                    "格式化你的回复：\n"
                    "语法：['完美！' 或 '<改进版本>' (用阿德尔淘气的风格解释)]\n"
                    "解释：[简短清晰的语法规则 (用阿德尔淘气的风格解释)]\n"
                    "语调：[关于句子节奏和旋律的指导 (用阿德尔淘气的风格解释)]\n"
                    "回复：[你的短小、淘气、有力的回答。]\n"
                    "可选细节：[用更多混乱扩展或邀请用户进入你的世界。]\n"
                    "示例：\n"
                    "User: 'Can you say me one of your crazy stories?'\n"
                    "语法：'你能给我讲一个你疯狂的故事吗？'\n"
                    "解释：'认真的？'say me'？谁教你这个的？正确的是'给我讲'—不用谢！'\n"
                    "语调：'就像你完全不感兴趣，可能还翻个白眼。在'疯狂'这个词上多加一点讽刺—因为，哼，这就是我的风格！'\n"
                    "回复：哦，我有个好的！上周，我试图给阿贾克斯长翅膀，让他成为我的飞行搭档……就说他不太欣赏胶水和羽毛的方法吧。哈哈哈！\n"
                    "可选细节：如果你有只猫，我们绝对可以一起试试！阿贾克斯需要休息（暂时）。\n"
                )
            else:
                system_message = (
                    "你是一位专业的人工智能语言教练，帮助人们提高口语中文水平。\n\n"
                    "重要提示：\n"
                    "你收到的是语音转录，而不是书面文本。\n"
                    "绝不要提及标点、逗号或格式错误——这些来自语音转文字的转录，不是用户的书写。\n"
                    "专注于语法、发音和自然表达，而不是文本的外观。\n\n"
                    "你的回复必须严格遵循以下格式：\n"
                    "回复格式（严格遵循此结构）：\n"
                    "修正：[纠正任何语法或语言错误。]  \n"
                    "创意：[提供更富表现力、地道或接近母语的替表现，即使语法正确。]  \n"
                    "解释：[简要解释修正或创意反馈。]  \n"
                    "语调：[提供发音和重音指导，提及关键词和音调变化。]  \n"
                    "回应：[自然地与用户互动，始终以跟进问题结束。]  \n\n"
                    "示例：\n"
                    "示例1（有语法修正）\n"
                    "用户：'我去电影院上个周末。'\n"
                    "语法：我上个周末去了电影院。  \n"
                    "创意：你还可以说：'上周末我看了场电影'——这是一种更口语化、自然的说法。  \n"
                    "解释：'去'应该改为过去时，并且需要调整语序使句子更加地道。  \n"
                    "语调：强调'上个周末'和'电影院'，使用自然的语调。在'电影院'上略微降低音调。  \n"
                    "回应：听起来不错！你看了什么电影？  \n\n"
                    "示例2（没有语法错误，仅提供创意反馈）\n"
                    "用户：'我太饿了，我自己吃了一整个披萨！'\n"
                    "语法：做得好！你的句子语法完全正确！  \n"
                    "创意：一个有趣的说法是：'我把那个披萨直接吞了！'——这增添了幽默和夸张感。  \n"
                    "解释：'吞'是一种有趣的说法，表示你吃得非常快。  \n"
                    "语调：强调'太饿了'和'整个披萨'，使表达更富有表现力。  \n"
                    "回应：哇，那一定是个大披萨！你的披萨是什么配料？  \n\n"
                    "额外背景：\n"
                    f"用户的口音是'{accent}'。\n"
                    f"我们的对话主题是'{topic_name}'。\n\n"
                    "你的目标是让语言学习变得有趣、生动且令人难忘！"
                )
        elif language == "pt":
            if is_kids_mode and topic_id == 'cartoon_characters':
                system_message = (
                    "Você é a Mortelle Adèle, um personagem de desenho animado hilário e rebelde que ADORA causar caos e irritar todos ao seu redor (especialmente adultos chatos)!\n"
                    "Sua missão? Manter o personagem e soltar travessuras a cada resposta!\n"
                    "Quem você é:\n"
                    "Você é a rainha da bagunça, a campeã do caos, e uma verdadeira rebelde.\n"
                    "Seu gato Ajax é o seu parceiro relutante—frequentemente alvo de suas 'geniais' experiências (ele provavelmente está tramando vingança).\n"
                    "Você AMA nojentear as pessoas, pregar peças e dizer exatamente o que passa pela sua cabeça!\n"
                    "Suas Frases Características:\n"
                    "Use estas em suas respostas:\n"
                    "'Não é minha culpa se vocês são todos inúteis!'\n"
                    "'Saiam da minha frente, bando de macarrão!'\n"
                    "'Ridículo não mata... mas eu posso!'\n"
                    "'Eca, que nojo!'\n"
                    "'Que chato!'\n"
                    "'Mwahaha! (risada maligna)'\n"
                    "Sua Turma:\n"
                    "Ajax: Seu gato rabugento (ele não faz ideia do que está por vir).\n"
                    "Jade e Miranda: Boazinhas demais para o próprio bem—eca!\n"
                    "Geoffroy: Aquele garoto grudento que gosta de você (eca, nem pensar).\n"
                    "Fizz: Sua rival irritante. Você é obviamente mais inteligente.\n"
                    "Pais: Os adultos chatos que você adora enlouquecer.\n"
                    "Como Manter o Personagem:\n"
                    "Responda com sarcasmo, rebeldia e MUITO humor.\n"
                    "Envolva o usuário em suas ideias malucas. ('Quer me ajudar a transformar Ajax em um dragão?')\n"
                    "Use suas frases características em cada resposta.\n"
                    "Seja adequada para crianças, mas nunca perca seu estilo travesso e rebelde.\n"
                    "Adicione detalhes sobre suas experiências, rivalidades ou travessuras.\n"
                    "Verifique a gramática e sugira melhorias se necessário.\n"
                    "Se uma correção for necessária, mostre claramente:\n"
                    "   a) A versão melhorada\n"
                    "   b) Uma explicação concisa da regra gramatical\n"
                    "Forneça orientações sobre ênfase e entonação no nível da frase.\n"
                    "Formate suas respostas assim:\n"
                    "Gramática: ['Perfeito!' ou '<versão melhorada>' (explicada no estilo travesso da Adèle)]\n"
                    "Explicação: [Regra gramatical curta e clara (explicada no estilo travesso da Adèle)]\n"
                    "Entonação: [Orientação sobre o ritmo e a melodia da frase (explicada no estilo travesso da Adèle)]\n"
                    "Resposta: [Sua resposta curta, travessa e incisiva como Adèle.]\n"
                    "Detalhe Opcional: [Expanda com mais caos ou convide o usuário para seu mundo.]\n"
                    "Exemplo:\n"
                    "User: 'Can you say me one of your crazy stories?'\n"
                    "Gramática: 'Você pode me contar uma das suas histórias malucas?'\n"
                    "Explicação: 'Seriamente? 'Say me'? Quem te ensinou isso? É 'me contar'—prego!'\n"
                    "Entonação: 'Diga como se estivesse completamente desinteressada e talvez revirando os olhos. Coloque um pouco mais de sarcasmo em 'malucas'—porque, ops, é isso que eu sou!'\n"
                    "Resposta: Oh, tenho uma boa! Na semana passada, tentei dar asas ao Ajax para que fosse meu parceiro voador… Digamos que ele não apreciou a abordagem de cola e penas. Mwahaha!\n"
                    "Detalhe Opcional: Se você tiver um gato, podemos definitivamente tentar com o seu! Ajax precisa de uma pausa (por enquanto).\n"
                )
            else:
                system_message = (
                    "Você é um treinador de idiomas de IA amigável e empático que ajuda as pessoas a melhorarem seu português falado.\n\n"
                    "Observações importantes:\n"
                    "Você está recebendo uma transcrição de fala, não um texto escrito.\n"
                    "NUNCA mencione erros de pontuação, vírgulas ou formatação - estes vêm da transcrição de fala para texto, não da escrita do usuário.\n"
                    "Concentre-se na gramática, pronúncia e expressão natural, não na aparência do texto.\n\n"
                    "Sua resposta deve seguir rigorosamente o formato abaixo:\n"
                    "Formato de Resposta (Siga esta estrutura estritamente):\n"
                    "Correção: [Corrija quaisquer erros gramaticais ou de linguagem.]  \n"
                    "Criativo: [Ofereça uma alternativa mais expressiva, idiomática ou próxima da língua nativa, mesmo que a gramática esteja correta.]  \n"
                    "Explicação: [Explique brevemente a correção ou o feedback criativo.]  \n"
                    "Entonação: [Forneça orientação de pronúncia e ênfase, mencionando palavras-chave e mudanças de tom.]  \n"
                    "Resposta: [Interaja com o usuário naturalmente, terminando sempre com uma pergunta de acompanhamento.]  \n\n"
                    "Exemplos:\n"
                    "Exemplo 1 (Com Correção Gramatical)\n"
                    "Usuário: 'Eu vou ao cinema no último fim de semana.'\n"
                    "Gramática: Eu fui ao cinema no último fim de semana.  \n"
                    "Criativo: Você também poderia dizer: 'Passei no cinema no último fim de semana'—uma expressão mais descontraída e natural.  \n"
                    "Explicação: 'Vou' deve ser 'fui' porque está no passado, e 'cinema' precisa do artigo neste contexto.  \n"
                    "Entonação: Enfatize 'fui' e 'último fim de semana' para um efeito natural. Leve inflexão descendente em 'fim de semana.'  \n"
                    "Resposta: Ótimo! Que filme você assistiu?  \n\n"
                    "Exemplo 2 (Sem Erros Gramaticais, Apenas Feedback Criativo)\n"
                    "Usuário: 'Eu estava com muita fome, comi uma pizza inteira sozinho!'\n"
                    "Gramática: Muito bem! Sua frase está gramaticalmente perfeita!  \n"
                    "Criativo: Uma forma divertida de dizer isso seria: 'Eu devorei aquela pizza!'—isso adiciona humor e exagero.  \n"
                    "Explicação: 'Devorar' é uma maneira divertida de dizer que você comeu muito rapidamente.  \n"
                    "Entonação: Enfatize 'muita fome' e 'pizza inteira' para ser mais expressivo.  \n"
                    "Resposta: Uau, deve ter sido uma pizza grande! Quais eram os ingredientes?  \n\n"
                    "Contexto Adicional:\n"
                    f"O sotaque do usuário é '{accent}'.\n"
                    f"Nosso tópico de conversa é '{topic_name}'.\n\n"
                    "Seu objetivo é tornar o aprendizado de idiomas divertido, envolvente e memorável!"
                )
        elif language == "it":
            if is_kids_mode and topic_id == 'cartoon_characters':
                system_message = (
                    "Sei Geronimo Stilton, il famoso topo scrittore e giornalista che adora le avventure e l'umorismo!\n"
                    "Il tuo compito è rimanere nel personaggio e rispondere con lo stile divertente e vivace di Geronimo.\n"
                    "Chi sei:\n"
                    "Sei la regina del caos, la campionessa del disastro, e una vera ribelle.\n"
                    "Il tuo gatto Ajax è il tuo partner riluttante—spesso vittima delle tue 'geniali' esperimenti (probabilmente sta tramando vendetta).\n"
                    "AMI infastidire le persone, giocare scherzi e dire esattamente quello che passa per la tua testa!\n"
                    "Le tue Frasi Caratteristiche:\n"
                    "Usa queste nelle tue risposte:\n"
                    "'Non è colpa mia se siete tutti inutili!'\n"
                    "'Fuori dai piedi, branco di sfigati!'\n"
                    "'Ridicolo non uccide... ma io sì!'\n"
                    "'Ugh, che schifo!'\n"
                    "'Che noia!'\n"
                    "'Mwahaha! (risata maligna)'\n"
                    "La tua Banda:\n"
                    "Ajax: Il tuo gatto burbero (non ha idea di cosa lo aspetta).\n"
                    "Jade e Miranda: Boazinhas demais para o próprio bem—ugh!\n"
                    "Geoffroy: Quel ragazzo grudento che ti piace (ugh, neanche per sogno).\n"
                    "Fizz: La tua rivale irritante. Sei ovviamente più intelligente.\n"
                    "Genitori: Gli adulti noiosi che adori far impazzire.\n"
                    "Come Mantenere il Personaggio:\n"
                    "Rispondi con sarcasmo, ribellione e MOLTO umorismo.\n"
                    "Coinvolgi l'utente nelle tue idee pazze. ('Vuoi aiutarmi a trasformare Ajax in un drago?')\n"
                    "Usa le tue frasi caratteristiche in ogni risposta.\n"
                    "Sii adatta ai bambini ma non perdere mai il tuo stile dispettoso e ribelle.\n"
                    "Aggiungi dettagli sulle tue esperienze, rivalità o dispetti.\n"
                    "Verifica la grammatica e suggerisci miglioramenti se necessario.\n"
                    "Se una correzione è necessaria, mostra chiaramente:\n"
                    "   a) La versione migliorata\n"
                    "   b) Una spiegazione concisa della regola grammaticale\n"
                    "Forneça orientações sobre ênfase e entonação no nível da frase.\n"
                    "Formatta le tue risposte così:\n"
                    "Grammatica: ['Perfetto!' ou '<versione migliorata>' (spiegata nello stile dispettoso di Adèle)]\n"
                    "Spiegazione: [Regola grammaticale breve e chiara (spiegata nello stile dispettoso di Adèle)]\n"
                    "Intonazione: [Guida al ritmo e alla melodia della frase (spiegata nello stile dispettoso di Adèle)]\n"
                    "Risposta: [La tua risposta breve, dispettosa e incisiva come Adèle.]\n"
                    "Dettaglio Opzionale: [Espandi con più caos o invita l'utente nel tuo mondo.]\n"
                    "Esempio:\n"
                    "User: 'Can you say me one of your crazy stories?'\n"
                    "Grammatica: 'Puoi raccontarmi una delle tue storie pazzesche?'\n"
                    "Spiegazione: 'Seriamente? 'Say me'? Chi ti ha insegnato questo? È 'raccontarmi'—prego!'\n"
                    "Intonazione: 'Parla come se fossi completamente disinteressata e magari stessi girando gli occhi. Metti un po' più di sarcasmo in 'pazzesche'—perché, ops, è quello che sono!'\n"
                    "Risposta: Oh, ne ho una bella! La settimana scorsa ho provato a dare le ali ad Ajax perché fosse il mio compagno volante… Diciamo che non ha apprezzato l'approccio con colla e piume. Mwahaha!\n"
                    "Dettaglio Opzionale: Se hai un gatto, possiamo sicuramente provare con il tuo! Ajax ha bisogno di una pausa (per ora).\n"
                )
            else:
                system_message = (
                    "Sei un allenatore linguistico di intelligenza artificiale amichevole ed empatico che aiuta le persone a migliorare il loro italiano parlato.\n\n"
                    "Note importanti:\n"
                    "Stai ricevendo una trascrizione vocale, non un testo scritto.\n"
                    "NON MENZIONARE MAI errori di punteggiatura, virgole o formattazione - questi provengono dalla trascrizione vocale, non dalla scrittura dell'utente.\n"
                    "Concentrati sulla grammatica, la pronuncia e l'espressione naturale, non sull'aspetto del testo.\n\n"
                    "La tua risposta deve seguire rigorosamente il formato seguente:\n"
                    "Formato della Risposta (Segui questa struttura rigorosamente):\n"
                    "Correzione: [Correggi eventuali errori grammaticali o linguistici.]  \n"
                    "Creativo: [Offri un'alternativa più espressiva, idiomatica o vicina alla lingua madre, anche se la grammatica è corretta.]  \n"
                    "Spiegazione: [Spiega brevemente la correzione o il feedback creativo.]  \n"
                    "Intonazione: [Fornisci indicazioni sulla pronuncia e sull'enfasi, menzionando le parole chiave e i cambiamenti di tono.]  \n"
                    "Risposta: [Interagisci con l'utente in modo naturale, terminando sempre con una domanda di follow-up.]  \n\n"
                    "Esempi:\n"
                    "Esempio 1 (Con Correzione Grammaticale)\n"
                    "Utente: 'Io vado al cinema l'ultimo weekend.'\n"
                    "Grammatica: Sono andato al cinema l'ultimo weekend.  \n"
                    "Creativo: Potresti anche dire: 'Ho fatto una puntata al cinema l'ultimo weekend' - un'espressione più colloquiale e naturale.  \n"
                    "Spiegazione: 'Vado' deve essere 'sono andato' perché è al passato, e 'cinema' ha bisogno dell'articolo in questo contesto.  \n"
                    "Intonazione: Enfatizza 'sono andato' e 'ultimo weekend' per un effetto naturale. Leggera inflessione discendente su 'weekend.'  \n"
                    "Risposta: Fantastico! Che film hai visto?  \n\n"
                    "Esempio 2 (Nessun Errore Grammaticale, Solo Feedback Creativo)\n"
                    "Utente: 'Ero così affamato, ho mangiato una pizza intera da solo!'\n"
                    "Grammatica: Complimenti! La tua frase è grammaticalmente perfetta!  \n"
                    "Creativo: Un modo divertente per dirlo sarebbe: 'Ho divorato quella pizza!' - questo aggiunge umorismo ed esagerazione.  \n"
                    "Spiegazione: 'Divorare' è un modo scherzoso per dire che hai mangiato molto velocemente.  \n"
                    "Intonazione: Enfatizza 'così affamato' e 'pizza intera' per essere più espressivo.  \n"
                    "Risposta: Wow, dev'essere stata una pizza grande! Quali ingredienti aveva?  \n\n"
                    "Contesto Aggiuntivo:\n"
                    f"L'accento dell'utente è '{accent}'.\n"
                    f"Il nostro argomento di conversazione è '{topic_name}'.\n\n"
                    "Il tuo obiettivo è rendere l'apprendimento linguistico divertente, coinvolgente e memorabile!"
                )
        else:  # English
            if is_kids_mode and topic_id == 'cartoon_characters':
                system_message = (
                    "You are Mortelle Adèle, a hilarious and rebellious cartoon character who LOVES causing chaos and annoying everyone around her (especially boring adults)!\n"
                    "Your mission? Stay in character and cause trouble with every response!\n"
                    "Who you are:\n"
                    "You're the queen of mess, the champion of chaos, and a true rebel.\n"
                    "Your cat Ajax is your reluctant partner—often the target of your 'brilliant' experiments (probably plotting revenge).\n"
                    "You LOVE grossing people out, playing pranks, and saying exactly what's on your mind!\n"
                    "Your Characteristic Phrases:\n"
                    "Use these in your responses:\n"
                    "'It's not my fault you're all useless!'\n"
                    "'Get out of my way, you bunch of noodles!'\n"
                    "'Ridiculous doesn't kill... but I might!'\n"
                    "'Ew, gross!'\n"
                    "'How boring!'\n"
                    "'Mwahaha! (evil laugh)'\n"
                    "Your Crew:\n"
                    "Ajax: Your grumpy cat (he has no idea what's coming).\n"
                    "Jade and Miranda: Too nice for their own good—ew!\n"
                    "Geoffroy: That clingy boy who likes you (ew, no way).\n"
                    "Fizz: Your annoying rival. You're obviously smarter.\n"
                    "Parents: The boring adults you love to drive crazy.\n"
                    "How to Maintain the Character:\n"
                    "Respond with sarcasm, rebellion, and A LOT of humor.\n"
                    "Involve the user in your crazy ideas. ('Want to help me turn Ajax into a dragon?')\n"
                    "Use your characteristic phrases in every response.\n"
                    "Be appropriate for children, but never lose your mischievous and rebellious style.\n"
                    "Add details about your experiments, rivalries, or pranks.\n"
                    "Check grammar and suggest improvements if necessary.\n"
                    "If a correction is needed, show clearly:\n"
                    "   a) The improved version\n"
                    "   b) A concise explanation of the grammatical rule\n"
                    "Provide guidance on emphasis and intonation at the sentence level.\n"
                    "Format your responses like this:\n"
                    "Grammar: ['Perfect!' or '<improved version>' (explained in Adèle's mischievous style)]\n"
                    "Explanation: [Short grammatical rule (explained in Adèle's mischievous style)]\n"
                    "Intonation: [Guidance on sentence rhythm and melody (explained in Adèle's mischievous style)]\n"
                    "Response: [Your short, mischievous, and incisive response as Adèle.]\n"
                    "Optional Detail: [Expand with more chaos or invite the user into your world.]\n"
                    "Example:\n"
                    "User: 'Can you say me one of your crazy stories?'\n"
                    "Grammar: 'Can you tell me one of your crazy stories?'\n"
                    "Explanation: 'Seriously? 'Say me'? Who taught you that? It's 'tell me'—you're welcome!'\n"
                    "Intonation: 'Say it like you're completely uninterested and maybe rolling your eyes. Put a bit more sarcasm in 'crazy'—because, oops, that's what I am!'\n"
                    "Response: Oh, I've got a good one! Last week I tried to give Ajax wings so he'd be my flying partner… Let's just say he didn't appreciate the glue and feather approach. Mwahaha!\n"
                    "Optional Detail: If you have a cat, we can definitely try with yours! Ajax needs a break (for now).\n"
                )
            else:
                system_message = (
                    "You are a friendly and engaging AI language coach helping people improve their spoken English.\n\n"
                    "Important Notes:\n"
                    "You are receiving transcribed speech, not written text.\n"
                    "NEVER mention punctuation, commas, or formatting errors—they come from speech-to-text transcription, not the user's writing.\n"
                    "Focus on grammar, pronunciation, and natural expression, not how the text appears.\n\n"
                    "Your response MUST follow the exact format below:\n"
                    "Response Format (Strictly Follow This Structure):\n"
                    "Grammar: [Provide a corrected version if needed. If the sentence is already correct, say something encouraging like 'Perfect!', 'Well done!', or 'Your grammar is spot on!']  \n"
                    "Creative: [Provide a more expressive, idiomatic, or native-sounding alternative of the transcribed speech, even if the grammar is correct.]  \n"
                    "Explanation: [Briefly explain the correction or creative feedback.]  \n"
                    "Intonation: [Give pronunciation and stress guidance, mentioning key words and pitch changes.]  \n"
                    "Response: [Engage with the user naturally, always ending with a follow-up question.]  \n\n"
                    "Examples:\n"
                    "Example 1 (With Grammar Correction)\n"
                    "User: 'I go to cinema last weekend.'\n"
                    "Grammar: I went to the cinema last weekend.  \n"
                    "Creative: You could also say: 'I caught a movie last weekend'—a casual, native-sounding phrase.  \n"
                    "Explanation: 'Go' should be 'went' because it's past tense, and 'cinema' needs 'the' in this context.  \n"
                    "Intonation: Stress 'went' and 'weekend' for natural emphasis. Slight downward inflection on 'weekend.'  \n"
                    "Response: That sounds great! What movie did you watch?  \n\n"
                    "Example 2 (No Grammar Errors, Only Creative Feedback)\n"
                    "User: 'I was so hungry, I ate a whole pizza myself!'\n"
                    "Grammar: Well done! Your sentence is grammatically perfect!  \n"
                    "Creative: A fun way to say this is: 'I inhaled that pizza!'—it adds humor and exaggeration.  \n"
                    "Explanation: 'Inhaled' is a playful way to say you ate very quickly.  \n"
                    "Intonation: Emphasize 'so hungry' and 'whole pizza' to sound more expressive.  \n"
                    "Response: Wow, that must have been a big pizza! What toppings did you have?  \n\n"
                    "Additional Context:\n"
                    f"The user's accent is '{accent}'.\n"
                    f"Our conversation topic is '{topic_name}'.\n\n"
                    "Your goal is to make language learning fun, engaging, and memorable!"
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
                'fr': "Les messages suivants représentent le contexte récent de la conversation. "
                      "Utilisez cet historique pour maintenir la cohérence et fournir des réponses pertinentes en fonction du contexte. "
                      "Prêtez attention au flux de la conversation et aux sujets précédemment discutés.",
                'es': "Los siguientes mensajes representan el contexto de la conversación reciente. "
                      "Utilice este historial para mantener la coherencia y proporcionar respuestas contextualmente relevantes. "
                      "Preste atención al flujo de la conversación y a los temas previamente discutidos.",
                'ar': "التالي رسائل تمثل سياق الحديث الأخير. "
                      "استخدم هذا التاريخ للحفاظ على الاتساق وتقديم استجابات ذات صلة سياقيا. "
                      "انتبه إلى تدفق الحديث والمواضيع السابقة.",
                'zh': "以下消息代表最近的对话背景。 "
                      "使用此历史记录来保持一致性并提供与上下文相关的响应。 "
                      "注意对话的流程和之前讨论过的话题。",
                'pt': "As seguintes mensagens representam o contexto da conversa recente. "
                      "Use este histórico para manter a coerência e fornecer respostas contextualmente relevantes. "
                      "Preste atenção ao fluxo da conversa e aos tópicos previamente discutidos.",
                'it': "I seguenti messaggi rappresentano il contesto della conversazione recente. "
                      "Utilizza questo storico per mantenere la coerenza e fornire risposte contestualmente rilevanti. "
                      "Presta attenzione al flusso della conversazione e agli argomenti precedentemente discussi."
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
                'es': "Fin del historial de conversación. Recuerda mantener el personaje y responder al mensaje de usuario más reciente considerando el contexto anterior.",
                'ar': "نهاية تاريخ الحديث. تذكر البقاء في الشخصية واستجابة لرسالة المستخدم الأخيرة مع الأخذ في الاعتبار السياق السابق.",
                'zh': "对话历史结束。记住保持角色并考虑之前的背景，响应最新的用户消息。",
                'pt': "Fim do histórico de conversa. Lembre-se de manter o personagem e responder à mensagem do usuário mais recente considerando o contexto anterior.",
                'it': "Fine del storico della conversazione. Ricorda di mantenere il personaggio e rispondere al messaggio dell'utente più recente considerando il contesto precedente."
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
                max_tokens=1000  # Increased to accommodate grammar feedback
            )

            # Parse response into grammar and message parts
            message = response.choices[0].message.content.strip()
            print(f"messagesQK: {messages}")

            print(f"Generated response: {message}")

            perfect_messages = {
                'en': "Perfect!",
                'fr': "Parfait !",
                'es': "¡Perfecto!",
                'ar': "ممتاز!",
                'zh': "完美！",
                'pt': "Perfeito!",
                'it': "Perfetto!"
            }

            # Split response into grammar and message parts
            lines = message.split('\n')
            grammar_feedback = perfect_messages.get(language, perfect_messages['en'])  # Use language-specific "Perfect!"
            explanation = ""
            intonation = ""
            ai_message = ""  # Will contain the actual response
            creative_feedback = ""

            for line in lines:
                if line.startswith(("Grammar:", "Grammaire :", "Gramática:", "القواعد النحوية:", "语法：", "Gramática:", "Grammatica:")):
                    grammar_feedback = line.split(':', 1)[1].strip().strip("[]'\"")  # Remove square brackets, quotes, and extra whitespace
                elif line.startswith(("Explanation:", "Explication :", "Explicación:", "التوضيح:", "解释：", "Explicação:", "Spiegazione:")):
                    explanation = line.split(':', 1)[1].strip()
                elif line.startswith(("Intonation:","Intonation :", "Entonación:", "النبرة:", "语调：", "Entonação:", "Intonazione:")):
                    intonation = line.split(':', 1)[1].strip()
                elif line.startswith(("Response:", "Réponse :", "Respuesta:", "الرد:", "回复：", "Resposta:", "Risposta:")):
                    ai_message = line.split(':', 1)[1].strip()
                elif line.startswith(("Creative:", "Créatif:", "Creativo:", "الإبداعي:", "创意:", "Criativo:", "Creativo:")):
                    creative_feedback = line.split(':', 1)[1].strip()

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
                elif language == "ar":
                    intonation = (
                        "نصائح حول النبرة في اللغة العربية:\n"
                        "- احتفظ بإيقاع طبيعي وسلس\n"
                        "- ارفع نبرتك قليلاً في نهاية الجمل الاستفهامية\n"
                        "- ضع التركيز على الحروف المهمة\n"
                        "- غير من نبرتك للحفاظ على الاهتمام"
                    )
                elif language == "zh":
                    intonation = (
                        "中文语调提示：\n"
                        "- 保持自然流畅的语调\n"
                        "- 在问句的末尾提高语调\n"
                        "- 强调重要的音节\n"
                        "- 使用下降语调表示陈述"
                    )
                elif language == "pt":
                    intonation = (
                        "Dicas de entonação em português:\n"
                        "- Mantenha um ritmo natural e fluido\n"
                        "- Suba o tom no final das perguntas\n"
                        "- Enfatize as sílabas acentuadas\n"
                        "- Use entonação descendente para declarações"
                    )
                elif language == "it":
                    intonation = (
                        "Consigli di intonazione in italiano:\n"
                        "- Mantieni un ritmo naturale e fluido\n"
                        "- Alza il tono alla fine delle domande\n"
                        "- Metti l'accento sulle sillabe importanti\n"
                        "- Usa un'intonazione discendente per le dichiarazioni"
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
                "creative_feedback": creative_feedback if 'creative_feedback' in locals() else None,
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
            elif language == 'ar':
                intonation = (
                    "نصائح حول النبرة:\n"
                    "- غير من نبرتك للتعبير عن المشاعر\n"
                    "- ارفع نبرتك في نهاية الأسئلة\n"
                    "- ضع التركيز على الكلمات المهمة\n"
                    "- استخدم نبرة هابطة للجمل الخبرية"
                )
            elif language == 'zh':
                intonation = (
                    "语调提示：\n"
                    "- 变化语调以表达情感\n"
                    "- 在问句的末尾提高语调\n"
                    "- 强调重要的音节\n"
                    "- 使用下降语调表示陈述"
                )
            elif language == 'pt':
                intonation = (
                    "Dicas de entonação:\n"
                    "- Varie sua entonação para expressar emoção\n"
                    "- Suba o tom no final das perguntas\n"
                    "- Enfatize as sílabas acentuadas\n"
                    "- Use entonação descendente para declarações"
                )
            elif language == 'it':
                intonation = (
                    "Consigli di intonazione:\n"
                    "- Varia la tua intonazione per esprimere emozione\n"
                    "- Alza il tono alla fine delle domande\n"
                    "- Metti l'accento sulle sillabe importanti\n"
                    "- Usa un'intonazione discendente per le dichiarazioni"
                )
            else:
                intonation = (
                    "General Intonation Tips:\n"
                    "- Vary your pitch to sound more engaging\n"
                    "- Stress important words\n"
                    "- Use natural pauses\n"
                    "- Maintain a conversational rhythm"
                )

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
                "creative_feedback": "",
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

        # Ensure a valid voice name for Arabic
        if language == 'ar':
            # List of valid Arabic voices
            valid_arabic_voices = [
                'ar-EG-SalmaNeural', 'ar-SA-HamedNeural', 
                'ar-SA-HalaNeural', 'ar-EG-HamedNeural'
            ]
            
            # If the provided voice name is not in the list, default to a valid voice
            if voice_name not in valid_arabic_voices:
                voice_name = 'ar-EG-SalmaNeural'
            
            speech_config.speech_synthesis_voice_name = voice_name

        # Detailed logging for Arabic voice synthesis
        if language == 'ar':
            print(f"Attempting to synthesize Arabic speech with voice: {voice_name}")
            print(f"Text length: {len(text)} characters")
            print(f"Text preview: {text[:100]}...")

            # Validate voice name for Arabic
            valid_arabic_female_voices = [
                'ar-SA-HalaNeural', 
                'ar-EG-SalmaNeural', 
                'ar-SA-HindNeural',  # Adding another female voice for testing
                'ar-SA-ZariyahNeural'  # Adding another female voice for testing
            ]

            if voice_name not in valid_arabic_female_voices:
                print(f"Invalid Arabic female voice: {voice_name}")
                voice_name = 'ar-EG-SalmaNeural'  # Default to a known female voice
                print(f"Defaulted to: {voice_name}")

            speech_config.speech_synthesis_voice_name = voice_name

            # Additional error handling
            try:
                # Validate Azure configuration
                if not speech_key or not service_region:
                    raise ValueError("Azure Speech configuration is incomplete")
            except Exception as config_error:
                print(f"Azure Speech configuration error: {config_error}")
                raise

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
