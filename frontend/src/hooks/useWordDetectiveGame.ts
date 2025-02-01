import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { wordDatabase } from '../data/wordDetectiveData';

interface GameState {
  currentWord: string;
  currentClues: string[];
  clueIndex: number;
  score: number;
  isGameActive: boolean;
  difficulty: 'easy' | 'medium' | 'hard';
  remainingAttempts: number;
  pronunciation: string;
  funFact?: string;
  category?: string;
}

const MAX_ATTEMPTS = 3;

export const useWordDetectiveGame = (initialDifficulty: 'easy' | 'medium' | 'hard' = 'easy', isKidsMode: boolean = false) => {
  const [gameState, setGameState] = useState<GameState>({
    currentWord: '',
    currentClues: [],
    clueIndex: 0,
    score: 0,
    isGameActive: false,
    difficulty: initialDifficulty,
    remainingAttempts: MAX_ATTEMPTS,
    pronunciation: '',
    funFact: '',
    category: ''
  });

  // Use refs to prevent unnecessary re-renders
  const gameStateRef = useRef(gameState);
  gameStateRef.current = gameState;

  // Update difficulty when it changes
  useEffect(() => {
    if (gameState.difficulty !== initialDifficulty) {
      setGameState(prev => ({
        ...prev,
        difficulty: initialDifficulty,
        isGameActive: false // Reset the game when difficulty changes
      }));
    }
  }, [initialDifficulty]);

  // Get a random word based on the current mode
  const getRandomWord = useCallback(() => {
    const filteredWords = wordDatabase.filter(word => word.isKidsMode === isKidsMode);
    if (filteredWords.length === 0) {
      console.error('No words found for the current mode');
      return null;
    }
    const randomIndex = Math.floor(Math.random() * filteredWords.length);
    return filteredWords[randomIndex];
  }, [isKidsMode]);

  const startNewRound = useCallback(() => {
    const wordItem = getRandomWord();
    if (!wordItem) {
      console.error('Failed to get a random word');
      return;
    }

    // Cancel any ongoing speech before starting new round
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    setGameState(prev => ({
      ...prev,
      currentWord: wordItem.word.toLowerCase(),
      currentClues: wordItem.clues,
      clueIndex: 0,
      isGameActive: true,
      remainingAttempts: MAX_ATTEMPTS,
      pronunciation: wordItem.hints.pronunciation,
      funFact: wordItem.hints.funFact,
      category: wordItem.category
    }));
  }, [getRandomWord]);

  const checkAnswer = useCallback((answer: string) => {
    // Clean up both the answer and current word
    const cleanAnswer = answer.toLowerCase().trim().replace(/[.,!?]/g, '');
    const cleanWord = gameStateRef.current.currentWord.toLowerCase().trim();
    
    const isCorrect = cleanAnswer.includes(cleanWord) || cleanWord.includes(cleanAnswer);
    
    if (!isCorrect && gameStateRef.current.remainingAttempts > 0) {
      // Reduce attempts for wrong answers
      setGameState(prev => ({
        ...prev,
        remainingAttempts: prev.remainingAttempts - 1
      }));
    }

    if (isCorrect) {
      const attempts = MAX_ATTEMPTS - gameStateRef.current.remainingAttempts + 1;
      const basePoints = gameStateRef.current.difficulty === 'hard' ? 30 : 20;
      const attemptBonus = (MAX_ATTEMPTS - attempts + 1) * 5;
      setGameState(prev => ({
        ...prev,
        score: prev.score + basePoints + attemptBonus,
        isGameActive: false
      }));
    }

    return isCorrect;
  }, []);

  const getNextClue = useCallback(() => {
    // Check if we have more clues (0-based index, so we need -1)
    const hasMoreClues = gameStateRef.current.clueIndex < (gameStateRef.current.currentClues.length - 1);
    
    if (hasMoreClues) {
      setGameState(prev => ({
        ...prev,
        clueIndex: prev.clueIndex + 1
      }));
    }
    return hasMoreClues;
  }, []);

  const skipCurrentClue = useCallback(() => {
    // Check if we have more clues (0-based index, so we need -1)
    const hasMoreClues = gameStateRef.current.clueIndex < (gameStateRef.current.currentClues.length - 1);
    
    if (gameStateRef.current.remainingAttempts > 1) {
      setGameState(prev => ({
        ...prev,
        remainingAttempts: prev.remainingAttempts - 1,
        clueIndex: hasMoreClues ? prev.clueIndex + 1 : prev.clueIndex
      }));
      return hasMoreClues;
    } else {
      // Game over if no attempts left
      setGameState(prev => ({
        ...prev,
        remainingAttempts: 0,
        isGameActive: false
      }));
      return false;
    }
  }, []);



  // Memoize the return value to prevent unnecessary re-renders
  const gameInterface = useMemo(() => ({
    currentWord: gameState.currentWord,
    currentClue: gameState.currentClues[gameState.clueIndex] || '',
    clueNumber: gameState.clueIndex + 1,
    totalClues: gameState.currentClues.length,
    score: gameState.score,
    isGameActive: gameState.isGameActive,
    remainingAttempts: gameState.remainingAttempts,
    maxAttempts: MAX_ATTEMPTS,
    pronunciation: gameState.pronunciation,
    funFact: gameState.funFact,
    category: gameState.category,
    checkAnswer,
    startNewRound,
    skipCurrentClue,
    getNextClue
  }), [gameState, checkAnswer, startNewRound, skipCurrentClue, getNextClue]);

  // Start first round only once on mount
  useEffect(() => {
    startNewRound();
  }, []); // Empty dependency array

  return gameInterface;
};

export type WordDetectiveGameHook = ReturnType<typeof useWordDetectiveGame>;
