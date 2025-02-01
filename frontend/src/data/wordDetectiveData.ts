interface WordItem {
  word: string;
  category: string;
  difficulty: 'easy' | 'medium' | 'hard';
  isKidsMode: boolean;
  clues: string[];
  hints: {
    pronunciation: string;
    funFact?: string;
  };
}

export const wordDatabase: WordItem[] = [
  {
    word: 'elephant',
    category: 'animals',
    difficulty: 'easy',
    isKidsMode: true,
    clues: [
      "I'm very big and have a long nose",
      "I have big ears and gray skin",
      "I live in Africa or Asia and make a trumpet sound"
    ],
    hints: {
      pronunciation: "EL-uh-fuhnt",
      funFact: "Elephants are the largest land animals on Earth!"
    }
  },
  {
    word: 'banana',
    category: 'food',
    difficulty: 'easy',
    isKidsMode: true,
    clues: [
      "I'm yellow and curved",
      "Monkeys love to eat me",
      "You need to peel me before eating"
    ],
    hints: {
      pronunciation: "buh-NA-nuh",
      funFact: "I grow on tall plants that look like trees!"
    }
  },
  {
    word: 'butterfly',
    category: 'animals',
    difficulty: 'easy',
    isKidsMode: true,
    clues: [
      "I have beautiful colored wings",
      "I start life as a caterpillar",
      "I fly from flower to flower"
    ],
    hints: {
      pronunciation: "BUT-er-fly",
      funFact: "My wings are actually transparent!"
    }
  },
  {
    word: 'rainbow',
    category: 'nature',
    difficulty: 'easy',
    isKidsMode: true,
    clues: [
      "I appear after it rains",
      "I have many beautiful colors",
      "I look like a colorful bridge in the sky"
    ],
    hints: {
      pronunciation: "RAIN-bow",
      funFact: "I always have seven colors!"
    }
  },
  {
    word: 'dinosaur',
    category: 'animals',
    difficulty: 'medium',
    isKidsMode: true,
    clues: [
      "I lived a very long time ago",
      "Some of us were very big and scary",
      "You can find my bones in museums"
    ],
    hints: {
      pronunciation: "DY-no-sore",
      funFact: "Some of us had feathers like birds!"
    }
  },
  {
    word: 'telescope',
    category: 'science',
    difficulty: 'medium',
    isKidsMode: false,
    clues: [
      "I help you see things that are far away",
      "Scientists use me to study space",
      "I can show you stars and planets up close"
    ],
    hints: {
      pronunciation: "TEL-uh-scope",
      funFact: "The biggest ones are as tall as buildings!"
    }
  },
  {
    word: 'umbrella',
    category: 'objects',
    difficulty: 'medium',
    isKidsMode: true,
    clues: [
      "I keep you dry",
      "You use me when it rains",
      "I open up like a flower over your head"
    ],
    hints: {
      pronunciation: "um-BREL-uh",
      funFact: "I was invented over 4,000 years ago!"
    }
  },
  {
    word: 'penguin',
    category: 'animals',
    difficulty: 'medium',
    isKidsMode: true,
    clues: [
      "I'm a bird but I can't fly",
      "I love to swim and eat fish",
      "I walk funny and wear a black and white suit"
    ],
    hints: {
      pronunciation: "PENG-gwin",
      funFact: "I can swim as fast as a car drives!"
    }
  },
  {
    word: 'ice cream',
    category: 'food',
    difficulty: 'medium',
    isKidsMode: true,
    clues: [
      "A frozen delight that makes summer bright",
      "In cone or cup, when temperature's up",
      "Vanilla, chocolate, or berry-crowned, in this treat happiness is found"
    ],
    hints: {
      pronunciation: "AIS-KREEM",
      funFact: "The average American eats 23 pounds of this treat per year!"
    }
  },
  {
    word: 'northern lights',
    category: 'nature',
    difficulty: 'hard',
    isKidsMode: false,
    clues: [
      "Dancing colors in polar skies",
      "Aurora's celestial light show divine",
      "Nature's neon, in Arctic nights they shine"
    ],
    hints: {
      pronunciation: "NOR-thern LYTS",
      funFact: "Also known as Aurora Borealis, these lights occur when solar particles collide with Earth's atmosphere"
    }
  },
  {
    word: 'black hole',
    category: 'science',
    difficulty: 'medium',
    isKidsMode: false,
    clues: [
      "Where light itself cannot escape",
      "A cosmic vacuum, space and time I drape",
      "Einstein's theory helps explain my shape"
    ],
    hints: {
      pronunciation: "BLAK-HOHL",
      funFact: "The first image of one was captured in 2019!"
    }
  },
  {
    word: 'solar system',
    category: 'science',
    difficulty: 'hard',
    isKidsMode: false,
    clues: [
      "Eight planets in cosmic dance",
      "Around a star they all advance",
      "Mercury to Neptune's expanse"
    ],
    hints: {
      pronunciation: "SOH-lar SIS-tem",
      funFact: "It takes about 230 million years for our solar system to complete one orbit around the Milky Way galaxy"
    }
  },
  {
    word: 'great wall',
    category: 'history',
    difficulty: 'medium',
    isKidsMode: false,
    clues: [
      "Ancient barrier stretching far and wide",
      "In China's landscape I reside",
      "Stone dragon's back on which guards would ride"
    ],
    hints: {
      pronunciation: "GRAYT-WAWL",
      funFact: "Contrary to popular belief, it cannot be seen from space with the naked eye"
    }
  },
  {
    word: 'time machine',
    category: 'science fiction',
    difficulty: 'hard',
    isKidsMode: false,
    clues: [
      "H.G. Wells made me famous in prose",
      "Past or future, that's how it goes",
      "A device that chronology flows"
    ],
    hints: {
      pronunciation: "TAYM-muh-SHEEN",
      funFact: "The concept was popularized in an 1895 novel"
    }
  },
  {
    word: 'milky way',
    category: 'astronomy',
    difficulty: 'hard',
    isKidsMode: false,
    clues: [
      "Our cosmic home, a spiral bright",
      "Billions of stars in galactic light",
      "A band across the darkest night"
    ],
    hints: {
      pronunciation: "MIL-kee-WAY",
      funFact: "It contains over 100 billion stars!"
    }
  },
  {
    word: 'coral reef',
    category: 'nature',
    difficulty: 'medium',
    isKidsMode: false,
    clues: [
      "Ocean's rainbow, living stone",
      "Where countless species make their home",
      "Threatened by warming seas they roam"
    ],
    hints: {
      pronunciation: "KOR-ul REEF",
      funFact: "The Great Barrier Reef is the largest living structure on Earth"
    }
  },
  {
    word: 'rain forest',
    category: 'nature',
    difficulty: 'hard',
    isKidsMode: false,
    clues: [
      "Emerald canopy touches sky",
      "Where countless species multiply",
      "Earth's lungs that keep our planet spry"
    ],
    hints: {
      pronunciation: "RAYN-FOR-est",
      funFact: "These biomes contain half of the world's plant and animal species"
    }
  },
  {
    word: 'giraffe',
    category: 'animals',
    difficulty: 'easy',
    isKidsMode: true,
    clues: [
      "I have a very long neck",
      "I have spots all over my body",
      "I'm the tallest animal in the world"
    ],
    hints: {
      pronunciation: "juh-RAF",
      funFact: "A giraffe's neck can be up to 8 feet long!"
    }
  },
  {
    word: 'procrastination',
    category: 'concepts',
    difficulty: 'hard',
    isKidsMode: false,
    clues: [
      "I'm what happens when you delay important tasks",
      "Students often struggle with me during exam season",
      "Tomorrow is my favorite word, but I never arrive"
    ],
    hints: {
      pronunciation: "proh-kras-tuh-NAY-shun",
      funFact: "The word comes from Latin 'pro' (forward) and 'crastinus' (of tomorrow)"
    }
  },
  {
    word: 'serendipity',
    category: 'concepts',
    difficulty: 'hard',
    isKidsMode: false,
    clues: [
      "I'm a happy accident",
      "When good things happen by chance",
      "Finding something wonderful when you weren't looking for it"
    ],
    hints: {
      pronunciation: "ser-uhn-DIP-i-tee",
      funFact: "This word was inspired by an ancient Persian fairy tale called 'The Three Princes of Serendip'"
    }
  },
  {
    word: 'nostalgia',
    category: 'emotions',
    difficulty: 'medium',
    isKidsMode: false,
    clues: [
      "I'm a bittersweet feeling about the past",
      "Old photos and memories often bring me",
      "A sentimental longing for times gone by"
    ],
    hints: {
      pronunciation: "nuh-STAL-juh",
      funFact: "Originally considered a medical condition in the 17th century!"
    }
  }
];

export const categories = [...new Set(wordDatabase.map(item => item.category))];
export const difficulties = ['easy', 'medium', 'hard'] as const;
