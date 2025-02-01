import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Container,
  IconButton,
  CircularProgress,
  Tooltip,
  Modal,
  Alert,
  AlertTitle
} from '@mui/material';
import { styled } from '@mui/material/styles';
import StarsIcon from '@mui/icons-material/Stars';
import MicIcon from '@mui/icons-material/Mic';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import SkipNextIcon from '@mui/icons-material/SkipNext';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import EmojiObjectsIcon from '@mui/icons-material/EmojiObjects';
import FavoriteIcon from '@mui/icons-material/Favorite';
import { useWordDetectiveGame } from '../../hooks/useWordDetectiveGame';

// Styled components for kid-friendly UI
const GameContainer = styled(Container)(({ theme }) => ({
  marginTop: theme.spacing(4),
}));

const DetectiveCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  backgroundColor: '#FFFFFF',
  borderRadius: theme.spacing(2),
  boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
  position: 'relative',
  overflow: 'hidden',
}));

const ScoreDisplay = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: theme.spacing(3),
  right: theme.spacing(3),
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
}));

interface WordDetectiveGameProps {
  onRecordingStart: () => void;
  onRecordingStop: () => void;
  onTranscription: (text: string) => void;
  onGameReset: () => void;
  isRecording: boolean;
  isThinking: boolean;
  transcribedText: string;
  difficulty: 'easy' | 'medium' | 'hard';
  isKidsMode: boolean;
}

const WordDetectiveGame = React.memo<WordDetectiveGameProps>(({ 
  onRecordingStart, 
  onRecordingStop, 
  isRecording,
  isThinking,
  transcribedText,
  isKidsMode
}) => {
  // Initialize game with current mode
  const game = useWordDetectiveGame(
    'medium', // default difficulty
    isKidsMode
  );
  const [showCelebration, setShowCelebration] = useState(false);
  const [showGameOver, setShowGameOver] = useState(false);
  const [feedback, setFeedback] = useState<{ message: string; isCorrect: boolean; transcribedText: string | null } | null>(null);
  const [isProcessingAnswer, setIsProcessingAnswer] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  /*const [showContinueButton, setShowContinueButton] = useState(false);*/
  const [recordingTimeLeft, setRecordingTimeLeft] = useState<number>(3);

  const speakText = useCallback((text: string) => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = isKidsMode ? 0.9 : 1; // Slower for kids mode
      utterance.pitch = isKidsMode ? 1.1 : 1; // Slightly higher pitch for kids mode
      
      // Get available voices
      const voices = window.speechSynthesis.getVoices();
      let preferredVoice;

      if (isKidsMode) {
        // Kid-friendly voices
        preferredVoice = voices.find(voice => 
          voice.name.toLowerCase().includes('samantha') || // macOS
          voice.name.toLowerCase().includes('microsoft zira') || // Windows
          (voice.lang === 'en-US' && voice.name.toLowerCase().includes('female')) // Fallback
        );
      } else {
        // Adult mode - English voices
        preferredVoice = voices.find(voice => 
          (voice.lang.startsWith('en') && !voice.name.toLowerCase().includes('zira')) ||
          voice.name.toLowerCase().includes('daniel') || // macOS
          voice.name.toLowerCase().includes('david') // Windows
        );
      }
      
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      } else {
        // Fallback to default English
        utterance.lang = 'en-US';
      }

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    }
  }, [isKidsMode]);

  const handleStopRecording = useCallback(() => {
    onRecordingStop();
  }, [onRecordingStop]);

  const handleStartRecording = useCallback(async () => {
    setFeedback(null);
    onRecordingStart();
  }, [onRecordingStart]);

  // Effect to handle recording countdown
  useEffect(() => {
    let interval: NodeJS.Timeout;
    let timeout: NodeJS.Timeout;
    
    if (isRecording) {
      setRecordingTimeLeft(3);
      interval = setInterval(() => {
        setRecordingTimeLeft((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            handleStopRecording();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      // Auto-stop after 3 seconds as a backup
      timeout = setTimeout(() => {
        handleStopRecording();
      }, 3000);
    }

    return () => {
      if (interval) clearInterval(interval);
      if (timeout) clearTimeout(timeout);
    };
  }, [isRecording, handleStopRecording]);

  // Effect to handle game mode changes
  useEffect(() => {
    if ('speechSynthesis' in window) {
      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) {
        // Voice selection moved to speakText function
      }
    }
    // Start new round when mode changes
    game.startNewRound();
  }, [isKidsMode, game.startNewRound]);

  // Effect to handle new transcriptions
  useEffect(() => {
    console.log('Transcription effect running with:', {
      transcribedText,
      isGameActive: game.isGameActive,
      isProcessingAnswer,
      isRecording,
      isThinking
    });

    // Skip if game is inactive, processing, recording, or thinking
    if (!game.isGameActive || isProcessingAnswer || isRecording || isThinking) {
      console.log('Skipping transcription processing because:', {
        gameInactive: !game.isGameActive,
        processing: isProcessingAnswer,
        recording: isRecording,
        thinking: isThinking
      });
      return;
    }

    const processTranscription = () => {
      console.log('Processing transcription:', transcribedText);
      setIsProcessingAnswer(true);

      // Wait for API response before showing no speech message
      if (transcribedText === undefined || transcribedText === null) {
        console.log('Transcription is undefined/null, waiting for API response');
        setIsProcessingAnswer(false);
        return;
      }

      // Handle empty or NO_SPEECH_DETECTED cases
      if (transcribedText === '' || transcribedText === 'NO_SPEECH_DETECTED') {
        console.log('No speech detected, setting feedback');
        setFeedback({ 
          message: "I didn't hear anything. Please try speaking again!", 
          isCorrect: false,
          transcribedText: null
        });
        setIsProcessingAnswer(false);
        return;
      }

      console.log('Checking answer:', transcribedText);
      const isCorrect = game.checkAnswer(transcribedText);
      console.log('Answer check result:', isCorrect);
      
      if (isCorrect) {
        setShowCelebration(true);
        setFeedback({ 
          message: "That's correct! You found the word!", 
          isCorrect: true,
          transcribedText
        });
      } else {
        setFeedback({ 
          message: "Not quite right. Try again!", 
          isCorrect: false,
          transcribedText
        });
        
        // Check if game is over after wrong answer
        if (game.remainingAttempts <= 0) {
          setShowGameOver(true);
          return;
        }
        
        // Automatically show next clue if available
        const hasMoreClues = game.getNextClue();
        if (!hasMoreClues && game.remainingAttempts <= 1) {
          setShowGameOver(true);
        }
      }
      setIsProcessingAnswer(false);
    };

    // Use setTimeout to avoid state updates during render
    setTimeout(processTranscription, 0);
  }, [transcribedText, game.isGameActive, isRecording, isThinking]);

  // Effect to handle celebration
  useEffect(() => {
    if (showCelebration) {
      // Stop any ongoing speech
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    }
  }, [showCelebration]);

  // Effect to read clue when it changes
  useEffect(() => {
    const shouldSpeak = game.isGameActive && 
                       !showGameOver && 
                       !showCelebration && 
                       !isRecording && 
                       !isThinking && 
                       game.currentClue;

    if (shouldSpeak) {
      speakText(game.currentClue);
    }
  }, [game.currentClue, game.isGameActive, showGameOver, showCelebration, isRecording, isThinking, speakText]);





  return (
    <GameContainer maxWidth="sm">
      <DetectiveCard elevation={3}>
        <Box sx={{ position: 'relative' }}>
          <Typography variant="h4" sx={{ 
            color: '#2C3E50',
            fontWeight: 'bold',
            marginBottom: 2,
            fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit'
          }}>
            Word Detective
          </Typography>
          
          <ScoreDisplay>
            <StarsIcon sx={{ color: '#FFD700' }} />
            <Typography variant="h5" sx={{ 
              color: '#2C3E50',
              fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit'
            }}>
              Score: {game.score}
            </Typography>
          </ScoreDisplay>

          <Box sx={{ marginY: 3 }}>
            <Typography variant="h6" sx={{ 
              color: '#5D6D7E', 
              marginBottom: 1,
              fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit'
            }}>
              Clue {game.clueNumber} of {game.totalClues}:
            </Typography>
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 1,
              backgroundColor: '#F8F9FA',
              padding: 2,
              borderRadius: 1,
              border: '1px solid #E9ECEF'
            }}>
              <Typography variant="body1" sx={{ 
                color: '#34495E',
                fontSize: isKidsMode ? '1.3rem' : '1.1rem',
                fontStyle: 'italic',
                flex: 1,
                fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit'
              }}>
                {game.currentClue}
              </Typography>
              <Tooltip title="Hear clue again">
                <IconButton 
                  onClick={() => speakText(game.currentClue)}
                  disabled={isSpeaking || isRecording}
                  size="small"
                  sx={{
                    color: '#5D6D7E',
                    '&:hover': {
                      color: '#34495E',
                    },
                    '&.Mui-disabled': {
                      color: '#95A5A6',
                    }
                  }}
                >
                  <VolumeUpIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          {feedback && (
            <Alert 
              severity={feedback.isCorrect ? "success" : "info"}
              sx={{ 
                marginY: 2,
                fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit'
              }}
            >
              <AlertTitle>{feedback.message}</AlertTitle>
              {feedback.transcribedText && (
                <Typography 
                  variant="body2" 
                  sx={{ 
                    mt: 1,
                    color: 'text.secondary',
                    fontStyle: 'italic',
                    fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit'
                  }}
                >
                  I heard: "{feedback.transcribedText}"
                </Typography>
              )}
            </Alert>
          )}

          <Box sx={{ 
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 1,
            mb: 2
          }}>
            {Array.from({ length: game.maxAttempts }).map((_, index) => (
              <FavoriteIcon
                key={index}
                sx={{
                  color: index < game.remainingAttempts ? '#FF6B6B' : '#E0E0E0',
                  fontSize: 24
                }}
              />
            ))}
          </Box>

          <Box sx={{ 
            display: 'flex', 
            gap: 2, 
            justifyContent: 'center',
            mt: 3 
          }}>
            {!isRecording ? (
              <Button
                variant="contained"
                onClick={handleStartRecording}
                disabled={!game.isGameActive || isThinking}
                startIcon={<MicIcon />}
                sx={{
                  backgroundColor: '#4CAF50',
                  '&:hover': {
                    backgroundColor: '#45a049',
                  },
                  fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit'
                }}
              >
                Speak Answer
              </Button>
            ) : (
              <Button
                variant="contained"
                color="secondary"
                disabled={true}
                startIcon={<CircularProgress size={20} color="inherit" />}
                sx={{
                  fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit'
                }}
              >
                Recording... ({recordingTimeLeft}s)
              </Button>
            )}
            
            <Button
              variant="outlined"
              onClick={() => {
                const hasMoreClues = game.skipCurrentClue();
                if (!hasMoreClues && game.remainingAttempts <= 1) {
                  setShowGameOver(true);
                }
                // Read the new clue regardless
                speakText(game.currentClue);
              }}
              disabled={!game.isGameActive || isRecording || isThinking}
              startIcon={<SkipNextIcon />}
              sx={{
                borderColor: '#FFA726',
                color: '#F57C00',
                '&:hover': {
                  borderColor: '#FB8C00',
                  backgroundColor: 'rgba(255, 167, 38, 0.04)'
                },
                fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit'
              }}
            >
              Skip ({game.remainingAttempts - 1} {game.remainingAttempts - 1 === 1 ? 'try' : 'tries'} left)
            </Button>
          </Box>

          {isThinking && (
            <Box sx={{ marginY: 2 }}>
              <CircularProgress size={24} />
              <Typography variant="body2" sx={{ color: '#7F8C8D', marginTop: 1 }}>
                Thinking...
              </Typography>
            </Box>
          )}

          <Box sx={{ marginY: 2 }}>
            <Typography variant="body2" sx={{ color: '#7F8C8D' }}>
              Attempts Left: {game.remainingAttempts} of {game.maxAttempts}
            </Typography>
            {game.remainingAttempts < game.maxAttempts && (
              <Typography variant="body2" sx={{ color: '#95A5A6', marginTop: 0.5 }}>
                {game.maxAttempts - game.remainingAttempts} attempt{game.maxAttempts - game.remainingAttempts !== 1 ? 's' : ''} used
              </Typography>
            )}
          </Box>

          {(showCelebration || showGameOver) && (
            <Modal
              open={true}
              onClose={() => {}}
              aria-labelledby="game-result-modal"
            >
              <Box sx={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: 400,
                bgcolor: 'background.paper',
                borderRadius: 3,
                boxShadow: 24,
                p: 4,
                outline: 'none',
                textAlign: 'center'
              }}>
                {showCelebration ? (
                  <>
                    <Typography variant="h4" sx={{ 
                      color: '#2C3E50',
                      fontWeight: 'bold',
                      fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit',
                      marginBottom: 2,
                      textAlign: 'center'
                    }}>
                      🎉 Congratulations! 🎉
                    </Typography>
                    <Typography variant="h6" sx={{ 
                      color: '#34495E',
                      fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit',
                      marginBottom: 3,
                      textAlign: 'center'
                    }}>
                      You got it right!
                    </Typography>
                  </>
                ) : (
                  <>
                    <Typography variant="h4" sx={{ 
                      color: '#2C3E50',
                      fontWeight: 'bold',
                      fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit',
                      marginBottom: 2,
                      textAlign: 'center'
                    }}>
                      Game Over
                    </Typography>
                    <Typography variant="h6" sx={{ 
                      color: '#34495E',
                      fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit',
                      marginBottom: 3,
                      textAlign: 'center'
                    }}>
                      The word was: {game.currentWord}
                    </Typography>
                  </>
                )}

                {/* Hints Section */}
                <Box sx={{ 
                  backgroundColor: '#F8F9FA',
                  borderRadius: 2,
                  p: 2,
                  mb: 3,
                  border: '1px solid #E9ECEF'
                }}>
                  <Typography variant="subtitle1" sx={{
                    color: '#2C3E50',
                    fontWeight: 'bold',
                    mb: 2,
                    fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit'
                  }}>
                    Word Details:
                  </Typography>
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body1" sx={{
                      color: '#34495E',
                      mb: 1,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit'
                    }}>
                      <RecordVoiceOverIcon sx={{ color: '#3498DB' }} />
                      Pronunciation: {game.pronunciation}
                    </Typography>
                    <IconButton 
                      onClick={() => speakText(game.currentWord)}
                      size="small"
                      sx={{
                        color: '#3498DB',
                        '&:hover': { color: '#2980B9' }
                      }}
                    >
                      <VolumeUpIcon />
                    </IconButton>
                  </Box>

                  {game.funFact && (
                    <Typography variant="body1" sx={{
                      color: '#34495E',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit'
                    }}>
                      <EmojiObjectsIcon sx={{ color: '#F1C40F' }} />
                      Fun Fact: {game.funFact}
                    </Typography>
                  )}
                </Box>

                <Button
                  variant="contained"
                  onClick={() => {
                    setShowCelebration(false);
                    setShowGameOver(false);
                    game.startNewRound();
                  }}
                  sx={{
                    backgroundColor: showCelebration ? '#4CAF50' : '#F57C00',
                    '&:hover': {
                      backgroundColor: showCelebration ? '#43A047' : '#F57C00',
                    },
                    fontFamily: isKidsMode ? 'Comic Sans MS, cursive' : 'inherit',
                    borderRadius: 20,
                    padding: '10px 30px',
                  }}
                >
                  Try Another Word
                </Button>
              </Box>
            </Modal>
          )}
        </Box>
      </DetectiveCard>
    </GameContainer>
  );
});

export default WordDetectiveGame;
