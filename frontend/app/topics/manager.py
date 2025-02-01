from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
import secrets

@dataclass
class Topic:
    id: str
    name: Dict[str, str]
    initial_prompt: Union[str, Dict[str, str]]
    follow_up_prompt: Union[str, Dict[str, str]]

class TopicManager:
    def __init__(self):
        # Initialize with kid-friendly topics
        self.topics = {
            "animals": Topic(
                id="animals",
                name={
                    "en": "Animals",
                    "fr": "Animaux",
                    "es": "Animales"
                },
                initial_prompt={
                    "en": "What's your favorite animal? Do you have any pets at home?",
                    "fr": "Quel est ton animal préféré ? As-tu des animaux à la maison ?",
                    "es": "¿Cuál es tu animal favorito? ¿Tienes mascotas en casa?"
                },
                follow_up_prompt={
                    "en": "What do you like most about that animal? What sounds do they make?",
                    "fr": "Qu'est-ce que tu aimes le plus chez cet animal ? Quels sons font-ils ?",
                    "es": "¿Qué es lo que más te gusta de ese animal? ¿Qué sonidos hacen?"
                }
            ),
            "superheroes": Topic(
                id="superheroes",
                name={
                    "en": "Superheroes",
                    "fr": "Super-héros",
                    "es": "Superhéroes"
                },
                initial_prompt={
                    "en": "If you could have any superpower, what would it be? Who's your favorite superhero?",
                    "fr": "Si tu pouvais avoir un super-pouvoir, lequel choisirais-tu ? Qui est ton super-héros préféré ?",
                    "es": "Si pudieras tener un superpoder, ¿cuál sería? ¿Quién es tu superhéroe favorito?"
                },
                follow_up_prompt={
                    "en": "What would you do with your superpower? How would you help people?",
                    "fr": "Que ferais-tu avec ton super-pouvoir ? Comment aiderais-tu les gens ?",
                    "es": "¿Qué harías con tu superpoder? ¿Cómo ayudarías a la gente?"
                }
            ),
            "fairy_tales": Topic(
                id="fairy_tales",
                name={
                    "en": "Fairy Tales",
                    "fr": "Contes de fées",
                    "es": "Cuentos de hadas"
                },
                initial_prompt={
                    "en": "What's your favorite fairy tale? Who's your favorite character?",
                    "fr": "Quel est ton conte de fées préféré ? Qui est ton personnage préféré ?",
                    "es": "¿Cuál es tu cuento de hadas favorito? ¿Quién es tu personaje favorito?"
                },
                follow_up_prompt={
                    "en": "If you could be in a fairy tale, what would your adventure be like?",
                    "fr": "Si tu pouvais être dans un conte de fées, comment serait ton aventure ?",
                    "es": "Si pudieras estar en un cuento de hadas, ¿cómo sería tu aventura?"
                }
            ),
            "space_adventure": Topic(
                id="space_adventure",
                name={
                    "en": "Space Adventure",
                    "fr": "Aventure spatiale",
                    "es": "Aventura espacial"
                },
                initial_prompt={
                    "en": "Let's go on a space adventure! What planet would you like to visit?",
                    "fr": "Partons pour une aventure spatiale ! Quelle planète aimerais-tu visiter ?",
                    "es": "¡Vamos a una aventura espacial! ¿Qué planeta te gustaría visitar?"
                },
                follow_up_prompt={
                    "en": "What do you think you would find on that planet? What would you bring with you?",
                    "fr": "Que penses-tu trouver sur cette planète ? Qu'est-ce que tu prendrais avec toi ?",
                    "es": "¿Qué crees que encontrarías en ese planeta? ¿Qué llevarías contigo?"
                }
            ),
            "dinosaurs": Topic(
                id="dinosaurs",
                name={
                    "en": "Dinosaurs",
                    "fr": "Dinosaures",
                    "es": "Dinosaurios"
                },
                initial_prompt={
                    "en": "What's your favorite dinosaur? Do you know what they ate?",
                    "fr": "Quel est ton dinosaure préféré ? Sais-tu ce qu'ils mangeaient ?",
                    "es": "¿Cuál es tu dinosaurio favorito? ¿Sabes qué comían?"
                },
                follow_up_prompt={
                    "en": "If you could meet a dinosaur, what would you do? Would you be scared?",
                    "fr": "Si tu pouvais rencontrer un dinosaure, que ferais-tu ? Aurais-tu peur ?",
                    "es": "Si pudieras conocer un dinosaurio, ¿qué harías? ¿Tendrías miedo?"
                }
            ),
            "magic_school": Topic(
                id="magic_school",
                name={
                    "en": "Magic School",
                    "fr": "École de magie",
                    "es": "Escuela de magia"
                },
                initial_prompt={
                    "en": "Welcome to magic school! What kind of magic would you like to learn?",
                    "fr": "Bienvenue à l'école de magie ! Quel type de magie aimerais-tu apprendre ?",
                    "es": "¡Bienvenido a la escuela de magia! ¿Qué tipo de magia te gustaría aprender?"
                },
                follow_up_prompt={
                    "en": "What magical spells would you create? What's your magical pet?",
                    "fr": "Quels sorts magiques créerais-tu ? Quel est ton animal magique ?",
                    "es": "¿Qué hechizos mágicos crearías? ¿Cuál es tu mascota mágica?"
                }
            ),
            "pirates": Topic(
                id="pirates",
                name={
                    "en": "Pirates",
                    "fr": "Pirates",
                    "es": "Piratas"
                },
                initial_prompt={
                    "en": "Ahoy! Let's go on a pirate adventure! What would you name your pirate ship?",
                    "fr": "Ohé ! Partons pour une aventure de pirates ! Comment appellerais-tu ton bateau pirate ?",
                    "es": "¡Ahoy! ¡Vamos a una aventura pirata! ¿Cómo llamarías a tu barco pirata?"
                },
                follow_up_prompt={
                    "en": "Where would you sail your ship? What treasure would you look for?",
                    "fr": "Où naviguerais-tu avec ton bateau ? Quel trésor chercherais-tu ?",
                    "es": "¿Dónde navegarías con tu barco? ¿Qué tesoro buscarías?"
                }
            ),
            "jungle_safari": Topic(
                id="jungle_safari",
                name={
                    "en": "Jungle Safari",
                    "fr": "Safari dans la jungle",
                    "es": "Safari en la selva"
                },
                initial_prompt={
                    "en": "We're going on a jungle safari! What animals do you hope to see?",
                    "fr": "Nous partons en safari dans la jungle ! Quels animaux espères-tu voir ?",
                    "es": "¡Nos vamos de safari por la selva! ¿Qué animales esperas ver?"
                },
                follow_up_prompt={
                    "en": "What sounds do you hear in the jungle? What's the most exciting thing you've spotted?",
                    "fr": "Quels sons entends-tu dans la jungle ? Quelle est la chose la plus excitante que tu as repérée ?",
                    "es": "¿Qué sonidos escuchas en la selva? ¿Qué es lo más emocionante que has visto?"
                }
            ),
            "underwater_world": Topic(
                id="underwater_world",
                name={
                    "en": "Underwater World",
                    "fr": "Monde Sous-marin",
                    "es": "Mundo Submarino"
                },
                initial_prompt={
                    "en": "Let's explore the ocean! What sea creatures would you like to meet?",
                    "fr": "Explorons l'océan ! Quelles créatures marines aimerais-tu rencontrer ?",
                    "es": "¡Exploremos el océano! ¿Qué criaturas marinas te gustaría conocer?"
                },
                follow_up_prompt={
                    "en": "Have you ever been to an aquarium? What was your favorite thing there?",
                    "fr": "Es-tu déjà allé à l'aquarium ? Qu'est-ce que tu as préféré ?",
                    "es": "¿Has estado alguna vez en un acuario? ¿Qué fue lo que más te gustó?"
                }
            ),
            "cartoon_characters": Topic(
                id="cartoon_characters",
                name={
                    "en": "Cartoon Characters",
                    "fr": "Personnages de Dessins Animés",
                    "es": "Personajes de Dibujos Animados"
                },
                initial_prompt={
                    "en": "Hi! I'm Mortelle Adele, your favorite cartoon character! I love making jokes and having fun adventures with my cat Ajax. What would you like to talk about? We can chat about my funny stories or anything else you'd like!",
                    "fr": "Salut ! Je suis Mortelle Adèle, ton personnage de dessin animé préféré ! J'adore faire des blagues et vivre des aventures amusantes avec mon chat Ajax. De quoi veux-tu parler ? On peut discuter de mes histoires drôles ou de ce que tu veux !",
                    "es": "¡Hola! ¡Soy Mortelle Adele, tu personaje de dibujos animados favorito! Me encanta hacer bromas y vivir aventuras divertidas con mi gato Ajax. ¿De qué te gustaría hablar? ¡Podemos charlar sobre mis historias divertidas o cualquier otra cosa que quieras!"
                },
                follow_up_prompt={
                    "en": "Would you like to hear about one of my funny adventures with Ajax? Or maybe you can tell me about your favorite cartoon character?",
                    "fr": "Tu veux que je te raconte une de mes aventures drôles avec Ajax ? Ou peut-être que tu peux me parler de ton personnage de dessin animé préféré ?",
                    "es": "¿Te gustaría escuchar sobre una de mis divertidas aventuras con Ajax? ¿O tal vez puedes contarme sobre tu personaje de dibujos animados favorito?"
                }
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
