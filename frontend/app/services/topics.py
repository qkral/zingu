from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
import secrets

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
        # Use a more robust randomization method
        topic_ids = list(self.topics.keys())
        random_topic_id = secrets.choice(topic_ids)
        return self.topics[random_topic_id]
    
    def get_topic(self, topic_id: str) -> Optional[Topic]:
        """Get a specific topic by ID"""
        return self.topics.get(topic_id)
