import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Box, 
  Typography, 
  Button,
  IconButton,
  Tooltip,
  Container,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Paper,
  Avatar,
  LinearProgress,
  Snackbar,
  Alert,
  Collapse,
  Stack,
  Chip
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import MicIcon from '@mui/icons-material/Mic';
import StopIcon from '@mui/icons-material/Stop';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import SpellcheckIcon from '@mui/icons-material/Spellcheck';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import ChatIcon from '@mui/icons-material/Chat';
import MusicNoteIcon from '@mui/icons-material/MusicNote';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InfoIcon from '@mui/icons-material/Info';
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';
import SchoolIcon from '@mui/icons-material/School';
import RateReviewIcon from '@mui/icons-material/RateReview';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';
import { ErrorOutline as ErrorOutlineIcon } from '@mui/icons-material';
import axios from 'axios';
import { languages } from '../../config/languages';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import DraggableDrawingCanvas from './DraggableDrawingCanvas';
import CreateIcon from '@mui/icons-material/Create';
import StarIcon from '@mui/icons-material/Star';
import { API_BASE_URL } from '../../config/api';
import { saveConversation, auth, ensureAuth, getConversationHistory, loadConversation } from '../../firebase';
import { onAuthStateChanged } from 'firebase/auth';
import HistoryIcon from '@mui/icons-material/History';

interface Message {
  text: string;
  role: 'user' | 'assistant' | 'system';
  isUser: boolean;
  audioBlob?: Blob;
  pronunciationFeedback?: PronunciationFeedback;
  grammarCorrection?: string;
  grammarExplanation?: string;
  showGrammarExplanation?: boolean;
  intonation?: string;
  showIntonation?: boolean;
  isAnalyzingPronunciation?: boolean;
  pronunciationGuidance?: string;
  isLoadingPronunciationGuidance?: boolean;
  topic?: string;
  topicName?: string; 
  isLoading?: boolean;
}

interface PronunciationFeedback {
  pronunciation_score: number;
  fluency_score: number;
  feedback_messages: string[];
  poor_words: {
    word: string;
    accuracy: number;
    initial_accuracy?: number;
    transcribed_text?: string;
  }[];
}

interface PronunciationGuidanceModal {
  open: boolean;
  guidance: string;
  poorWords: any[];
  preventAutoplay: boolean;
}

interface HistoryMessage {
  text: string;
  isUser: boolean;
  topic_id: string;
}

// Voice mapping with male and female options
const voiceNameMapping: { [key: string]: { [key: string]: { male: string, female: string, kid: string } } } = {
  'en': {
    'neutral': { 
      male: 'en-US-GuyNeural', 
      female: 'en-US-JennyNeural',
      kid: 'en-US-AnaNeural'  // Child-like voice
    },
    'british': { 
      male: 'en-GB-RyanNeural', 
      female: 'en-GB-LibbyNeural',
      kid: 'en-GB-MaisieNeural'  // Changed to a more child-like British voice
    },
    'australian': { 
      male: 'en-AU-WilliamNeural', 
      female: 'en-AU-NatashaNeural',
      kid: 'en-AU-CarlyNeural'  // Child-like voice
    }
  },
  'fr': {
    'neutral': { 
      male: 'fr-FR-ClaudeNeural', 
      female: 'fr-FR-DeniseNeural',
      kid: 'fr-FR-EloiseNeural'  // Child-like voice
    },
    'canadian': { 
      male: 'fr-CA-JeanNeural', 
      female: 'fr-CA-SylvieNeural',
      kid: 'fr-CA-SylvieNeural'  // Using female voice as fallback
    }
  },
  'es': {
    'neutral': { 
      male: 'es-ES-AlvaroNeural', 
      female: 'es-ES-ElviraNeural',
      kid: 'es-ES-IreneNeural'  // Child-like voice
    },
    'mexican': { 
      male: 'es-MX-JorgeNeural', 
      female: 'es-MX-DaliaNeural',
      kid: 'es-MX-MarinaNeural'  // Child-like voice
    }
  }
};

interface ConversationalAICoachProps {
  isKidsMode?: boolean;
  onStart?: () => void;
}

const ConversationalAICoach: React.FC<ConversationalAICoachProps> = ({ 
  isKidsMode: isKidsModeProp = false,
  onStart
}) => {
  // Pronunciation recording state
  const [pronunciationRecording, setPronunciationRecording] = useState(false);
  const [currentPronunciationWord, setCurrentPronunciationWord] = useState<string>('');
  const pronunciationAudioPlayerRef = useRef<HTMLAudioElement>(null);
  const pronunciationMediaRecorderRef = useRef<MediaRecorder | null>(null);

  // Use isKidsMode directly from props
  const isKidsMode = isKidsModeProp;

  // Add debug effect to monitor isKidsMode changes
  useEffect(() => {
    console.log('isKidsMode changed:', isKidsMode);
  }, [isKidsMode]);

  // Pronunciation cleanup effect
  useEffect(() => {
    return () => {
      if (pronunciationRecording) {
        stopPronunciationRecording();
      }
      if (pronunciationAudioPlayerRef.current) {
        URL.revokeObjectURL(pronunciationAudioPlayerRef.current.src);
      }
    };
  }, [pronunciationRecording]);

  // Pronunciation recording functions
  const startPronunciationRecording = async (word: string) => {
    try {
      setPronunciationRecording(true);
      setCurrentPronunciationWord(word);
      setWordError(null);
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks: Blob[] = [];
      let silenceTimeout: NodeJS.Timeout;
      
      // Set a timeout to stop recording if no audio is detected
      const resetSilenceTimeout = () => {
        if (silenceTimeout) clearTimeout(silenceTimeout);
        silenceTimeout = setTimeout(() => {
          console.log('Recording timeout - no audio detected');
          if (mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
          }
        }, 5000); // 5 seconds timeout
      };
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
          resetSilenceTimeout(); // Reset timeout when audio is detected
        }
      };
      
      mediaRecorder.onstop = async () => {
        setPronunciationRecording(false);
        if (silenceTimeout) clearTimeout(silenceTimeout);
        
        if (audioChunks.length === 0) {
          setWordError('No audio detected. Please speak into your microphone.');
          setCurrentPronunciationWord(word);
          stream.getTracks().forEach(track => track.stop());
          return;
        }
        
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        console.log('Audio recorded for word:', word, 'blob size:', audioBlob.size);
        
        // Store the audio blob immediately after recording
        setRecordedAudioBlobs(prev => {
          const newBlobs = { ...prev, [word]: audioBlob };
          console.log('Updated audio blobs:', Object.keys(newBlobs));
          return newBlobs;
        });
        
        await handlePronunciationResult(audioBlob, word);
        
        // Cleanup
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start(100); // Collect data every 100ms
      pronunciationMediaRecorderRef.current = mediaRecorder;
      resetSilenceTimeout(); // Start initial timeout
      
    } catch (error) {
      console.error('Error starting recording:', error);
      setPronunciationRecording(false);
      setCurrentPronunciationWord('');
      setWordError('Failed to start recording. Please check your microphone permissions.');
      setError('Failed to start recording. Please check your microphone permissions.');
    }
  };

  const stopPronunciationRecording = () => {
    if (pronunciationMediaRecorderRef.current && pronunciationMediaRecorderRef.current.state === 'recording') {
      pronunciationMediaRecorderRef.current.stop();
      pronunciationMediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setPronunciationRecording(false);
    }
  };



  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isMessageLoading, setIsMessageLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [, setHistory] = useState<HistoryMessage[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const [hasUserInteracted, setHasUserInteracted] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<string>(languages[0].code);
  const [selectedAccent, setSelectedAccent] = useState<string>(languages[0].accents[0].code);
  const [selectedVoiceGender, setSelectedVoiceGender] = useState<'male' | 'female' | 'kid'>('female');
  const [selectedTopic, setSelectedTopic] = useState<string>('random');
  const [currentPlayingAudioSrc, setCurrentPlayingAudioSrc] = useState<string | null>(null);
  const [explanationButtonClicked, setExplanationButtonClicked] = useState(false);
  const [pronunciationButtonClicked, setPronunciationButtonClicked] = useState(false);
  const [intonationButtonClicked, setIntonationButtonClicked] = useState(false);
  const [isAutoplayEnabled, setIsAutoplayEnabled] = useState(true);
  const [currentAutoplayState, setCurrentAutoplayState] = useState(true);  
  const [pronunciationGuidanceModal, setPronunciationGuidanceModal] = useState<PronunciationGuidanceModal>({
    open: false,
    guidance: '',
    poorWords: [] as any[],
    preventAutoplay: false
  });
  const [currentTopic, setCurrentTopic] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioQueue = useRef<Blob[]>([]);
  const hasInitialized = useRef(false);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // Initialize audio stream when component mounts
  useEffect(() => {
    return () => {
      // Cleanup function
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
        audioStreamRef.current = null;
      }
    };
  }, []);

  // Add state for modal recording
  const [modalRecording, setModalRecording] = useState(false);
  const [, setModalAudioBlob] = useState<Blob | null>(null);
  const modalAudioPlayerRef = useRef<HTMLAudioElement>(null);
  const modalMediaRecorderRef = useRef<MediaRecorder | null>(null);





  const stopModalRecording = () => {
    if (modalMediaRecorderRef.current && modalMediaRecorderRef.current.state === 'recording') {
      modalMediaRecorderRef.current.stop();
      modalMediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setModalRecording(false);
    }
  };

  // Recording state for chat interface
  //const [currentRecordingWord, setCurrentRecordingWord] = useState<string>('');
  //const [wordRecordings, setWordRecordings] = useState<Record<string, Blob>>({});

  // Add state for storing recorded audio
  const [recordedAudioBlobs, setRecordedAudioBlobs] = useState<{ [key: string]: Blob }>({});

  useEffect(() => {
    if (!hasInitialized.current) {
      hasInitialized.current = true;
    }
  }, []);

  const scrollToBottom = useCallback(() => {
    // Simplified scrolling with a single, reliable method
    if (messagesEndRef.current) {
      // Use scrollIntoView with the last child element for most reliable scrolling
      const lastMessage = messagesEndRef.current.lastElementChild;
      if (lastMessage) {
        lastMessage.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'end',
          inline: 'nearest'
        });
      }
    }
  }, []);

  useEffect(() => {
    console.log('Messages effect triggered');
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    const hasExpandedContent = messages.some(
      m => m.showGrammarExplanation || 
           m.showIntonation || 
           m.pronunciationFeedback
    );
    if (hasExpandedContent) {
      scrollToBottom();
    }
  }, [messages.map(m => m.showGrammarExplanation || m.showIntonation || m.pronunciationFeedback).join(','), scrollToBottom]);

  useEffect(() => {
    // Convert all messages to history format, preserving everything
    const conversationHistory: HistoryMessage[] = messages
      .filter((msg): msg is Message => msg.role !== 'system')  // Only skip system messages
      .map(msg => ({
        text: msg.text || '',  // Ensure text is always a string
        isUser: msg.isUser,
        topic_id: msg.topic || 'random'
      }));

    setHistory(conversationHistory);
  }, [messages]);

  useEffect(() => {
    const handleInteraction = () => {
      setHasUserInteracted(true);
      // Try to play any queued audio
      if (audioQueue.current.length > 0) {
        const nextAudio = audioQueue.current.shift();
        if (nextAudio) {
          console.log('hhere');
          playAudio(nextAudio);
        }
      }
      // Remove the listener after first interaction
      document.removeEventListener('click', handleInteraction);
    };

    document.addEventListener('click', handleInteraction);
    return () => document.removeEventListener('click', handleInteraction);
  }, []);

  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Add authentication state listener and ensure authentication
  useEffect(() => {
    const checkAndSetAuth = async () => {
      try {
        const authToken = await ensureAuth();
        setIsAuthenticated(!!authToken);
      } catch (error) {
        console.error('Authentication failed:', error);
        setIsAuthenticated(false);
      }
    };

    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setIsAuthenticated(!!user);
    });

    checkAndSetAuth();

    // Cleanup subscription on unmount
    return () => unsubscribe();
  }, []);

  const handleSaveConversation = useCallback(async () => {
    if (!isAuthenticated) {
      try {
        const authToken = await ensureAuth();
        setIsAuthenticated(!!authToken);
      } catch (error) {
        console.error('Failed to authenticate:', error);
        return null;
      }
    }

    if (messages.length > 0) {
      try {
        const conversationId = await saveConversation(messages, currentTopic);
        console.log('Conversation saved with ID:', conversationId);
        return conversationId;
      } catch (error) {
        console.error('Failed to save conversation:', error);
        return null;
      }
    }
    return null;
  }, [messages, currentTopic, isAuthenticated]);

  const handleEndConversation = useCallback(async () => {
    await handleSaveConversation();
    // Existing end conversation logic
    setMessages([]);
    setCurrentTopic(null);
    // ... other existing logic
  }, [handleSaveConversation]);

  useEffect(() => {
    if (messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
      handleSaveConversation();
    }
  }, [messages, handleSaveConversation]);

  // Auto-play only non-initial AI messages
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    
    // Detailed debug logging
    console.log('=== Auto-play effect triggered ===');
    console.log('Last message details:', {
      text: lastMessage?.text,
      isUser: lastMessage?.isUser,
      hasAudioBlob: !!lastMessage?.audioBlob,
      pronunciationFeedback: lastMessage?.pronunciationFeedback
    });
    console.log('Messages length:', messages.length);
    console.log('Has started:', hasStarted);
    console.log('Has user interacted:', hasUserInteracted);
    
    // Detailed conditions logging
    const shouldPlayConditions = {
      isNotUserMessage: !lastMessage?.isUser,
      hasAudioBlob: !!lastMessage?.audioBlob,
      hasStarted,
      noExplanationButtonClicked: !explanationButtonClicked,
      noIntonationButtonClicked: !intonationButtonClicked,
      noPronunciationButtonClicked: !pronunciationButtonClicked
    };
    console.log('Pronunciation button clicked state:', pronunciationButtonClicked);
    console.log('Should play conditions:', shouldPlayConditions);

    // Check if all conditions are true
    const shouldPlay = Object.values(shouldPlayConditions).every(Boolean);

    // Reset explanation and intonation button clicked state after checking
    if (explanationButtonClicked) {
      setExplanationButtonClicked(false);
    }
    if (intonationButtonClicked) {
      setIntonationButtonClicked(false);
    }
    // Only reset pronunciation button if we're not currently analyzing
    if (pronunciationButtonClicked && !messages.some(m => m.isAnalyzingPronunciation)) {
      setPronunciationButtonClicked(false);
      console.log('Pronunciation button state reset to false');
    }

    if (shouldPlay && isAutoplayEnabled && !pronunciationGuidanceModal.preventAutoplay) {
      console.log('Attempting to play audio',shouldPlay);
      if (hasUserInteracted) {
        console.log('hhere2');
        if (lastMessage.audioBlob) {
          playAudio(lastMessage.audioBlob);
        } else {
          console.log('No audio blob available to play');
        }
      } else {
        console.log('Queueing audio');
        if (lastMessage.audioBlob) {
          audioQueue.current.push(lastMessage.audioBlob);
        }
      }
    } else {
      console.log('Audio playback conditions not met');
    }
  }, [messages, hasUserInteracted, hasStarted]);

  useEffect(() => {
    console.log('Full Voice Name Mapping:', JSON.stringify(voiceNameMapping, null, 2));
  }, [selectedLanguage, selectedAccent, selectedVoiceGender]);

  useEffect(() => {
    console.log('Loading States Debug:', {
      isMessageLoading: isMessageLoading,
      isProcessing,
      isRecording,
      isAnalyzing: messages.some(m => m.isAnalyzingPronunciation),
      hasStarted
    });
  }, [isProcessing, isRecording, hasStarted, messages]);

  useEffect(() => {
    console.log('Current Topic:', currentTopic);
  }, [currentTopic]);

  useEffect(() => {
    if (pronunciationGuidanceModal.open) {
      // Only play if preventAutoplay is not set
      if (!pronunciationGuidanceModal.preventAutoplay) {
        speakAIText(pronunciationGuidanceModal.guidance);
      }
      
      // Reset preventAutoplay after first render
      setPronunciationGuidanceModal(prev => ({
        ...prev,
        preventAutoplay: false
      }));
    }
  }, [pronunciationGuidanceModal.open, pronunciationGuidanceModal.guidance]);

  useEffect(() => {
    console.log('Mode or topic changed:', { isKidsMode, currentTopic, selectedTopic });
    // Remove the automatic setting of random topic in kids mode
  }, [isKidsMode, currentTopic, selectedTopic]);

  const getCurrentAccent = (): string => {
    
    // Map frontend accent codes to backend accent names
    const accentMapping: { [key: string]: string } = {
      // English accents
      'en-us-neutral': 'neutral',
      'en-us-southern': 'neutral',
      'en-gb-neutral': 'british',
      'en-gb-british': 'british',
      'en-gb': 'british',
      'en-au-australian': 'australian',
      'en-au': 'australian',
      
      // French accents
      'fr-fr-neutral': 'neutral',
      'fr-ca-canadian': 'canadian',
      'fr-ca': 'canadian',
      
      // Spanish accents
      'es-es-neutral': 'neutral',
      'es-mx-mexican': 'mexican',
      'es-mx': 'mexican'
    };

    const mappedAccent = accentMapping[`${selectedLanguage}-${selectedAccent}`];
    
    if (!mappedAccent) {
      console.warn(`No accent mapping found for ${selectedLanguage}-${selectedAccent}, defaulting to 'neutral'`);
      return 'neutral';
    }
    
    return mappedAccent;
  };

  const handleLanguageChange = (event: SelectChangeEvent<string>) => {
    const newLanguage = event.target.value;
    console.log('Language changed to:', newLanguage);  
    setSelectedLanguage(newLanguage);
    // Reset accent to first available accent for the new language
    const language = languages.find(l => l.code === newLanguage);
    if (language && language.accents.length > 0) {
      setSelectedAccent(language.accents[0].code);
    }
  };

  const handleAccentChange = (event: SelectChangeEvent<string>) => {
    const newAccent = event.target.value;
    console.log('Accent changed to:', newAccent);  
    setSelectedAccent(newAccent);
  };

  const handleVoiceGenderChange = (event: SelectChangeEvent<string>) => {
    const newVoiceGender = event.target.value;
    console.log('Voice gender changed to:', newVoiceGender);  
    setSelectedVoiceGender(newVoiceGender as 'male' | 'female' | 'kid');
  };

  const handleTopicChange = (event: SelectChangeEvent<string>) => {
    const newTopic = event.target.value;
    console.log('Topic change initiated:', {
      newTopic,
      isKidsMode,
      kidsTopics,
      adultTopics
    });
    
    setSelectedTopic(newTopic);
    setCurrentTopic(null);
    
    // Clear existing messages when topic changes
    setMessages([]);
  };


  const handleStart = () => {
    setHasStarted(true);
    onStart?.(); 
  };

  const handleStartConversation = async () => {
    if (!selectedTopic) {
      console.error('No topic selected');
      return;
    }
    
    try {
      handleStart(); 
      setIsProcessing(true);
      setError(null);
      
      console.log('Start Conversation Debug:', {
        language: selectedLanguage,
        accent: selectedAccent,
        voiceGender: selectedVoiceGender,
        currentAccent: JSON.stringify(getCurrentAccent()),
        isKidsMode,
        selectedTopic,
        currentTopic,
        availableTopics: isKidsMode ? kidsTopics : adultTopics
      });

      // Get the correct voice name based on language, accent, and gender
      const voiceName = voiceNameMapping[selectedLanguage]?.[getCurrentAccent()]?.[selectedVoiceGender] || 'en-US-JennyNeural';
      
      console.log('Voice Selection Debug:', {
        language: selectedLanguage,
        accent: getCurrentAccent(),
        gender: selectedVoiceGender,
        voiceName
      });
      console.log('testtttttt', selectedTopic, currentTopic);

      if (currentTopic) {
        console.log('22222222222222aaa');
      }
      if (!currentTopic && selectedTopic) {
        console.log('22222222222222');
      }

      const formData = new FormData();
      formData.append('language', selectedLanguage);
      formData.append('accent', selectedAccent);
      formData.append('voice_name', voiceName);

      // Send the current topic and prevent_random flag
      if (currentTopic) {
        formData.append('topic', currentTopic);
      }
      if (!currentTopic && selectedTopic) {
        formData.append('topic', selectedTopic);
      }
      formData.append('current_topic', selectedTopic || currentTopic || 'random');
      formData.append('is_kids_mode', String(isKidsMode));
      formData.append('prevent_random', String(isKidsMode)); 

      console.log('Sending request to:', `${API_BASE_URL}/api/coach/start-conversation`);

      const response = await fetch(`${API_BASE_URL}/api/coach/start-conversation`, {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', {
          status: response.status,
          statusText: response.statusText,
          body: errorText
        });
        throw new Error(`Failed to start conversation: ${errorText}`);
      }

      const data = await response.json();
      console.log('Received response data:', data);

      const { message, topic_name, audio } = data;
      
      // Validate received data
      if (!message) {
        console.error('No message received from the API');
        throw new Error('No conversation message received');
      }

      const initialTopic = currentTopic; 

      // Convert base64 to blob
      const audioBlob = audio ? base64ToBlob(audio, 'audio/wav') : undefined;
      
      // Wait a bit for the UI to update
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Set the initial message with the correct topic
      const initialMessage: Message = {
        text: message,
        role: 'assistant',
        isUser: false,
        audioBlob,
        topic: initialTopic || undefined,
        topicName: topic_name
      };
      
      console.log('Setting initial message:', initialMessage);
      
      setMessages([initialMessage]);
      setCurrentTopic(initialTopic);
      
      // Wait a bit more for the message to be displayed
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Play the audio manually
      if (audioBlob) {
        console.log('Playing audio blob');
        playAudio(audioBlob);
      } else {
        console.warn('No audio blob to play');
      }
      
    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error('Detailed Error in handleStartConversation:', {
          name: error.name,
          message: error.message,
          stack: error.stack
        });
        setError(`Failed to start conversation: ${error.message}`);
      } else {
        console.error('Unknown error in handleStartConversation:', error);
        setError('Failed to start conversation due to an unknown error');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePlayPauseAudio = async (message: Message) => {
    // If no audio blob exists, return
    if (!message.audioBlob) return;

    const audioSourceKey = `${message.audioBlob.size}_${message.audioBlob.type}`;

    // If no audio player, create one
    if (!audioPlayerRef.current) {
      audioPlayerRef.current = new Audio();
    }

    // If this is the first time playing this audio or a different audio
    if (currentPlayingAudioSrc !== audioSourceKey) {
      // Stop any currently playing audio
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
        audioPlayerRef.current.currentTime = 0;
      }

      // Create blob URL and set source
      const url = URL.createObjectURL(message.audioBlob);
      audioPlayerRef.current.src = url;

      // Add event listeners
      audioPlayerRef.current.onended = () => {
        setIsPlaying(false);
        setCurrentPlayingAudioSrc(null);
      };
    }

    // If the audio is paused or not playing
    if (audioPlayerRef.current.paused) {
      try {
        await audioPlayerRef.current.play();
        setIsPlaying(true);
        setCurrentPlayingAudioSrc(audioSourceKey);
      } catch (error) {
        console.error('Error playing audio:', error);
        setIsPlaying(false);
        setCurrentPlayingAudioSrc(null);
      }
    } 
    // If the audio is currently playing
    else {
      // Pause the audio
      audioPlayerRef.current.pause();
      setIsPlaying(false);
      // Keep the current playing audio source so we can resume from this point
      setCurrentPlayingAudioSrc(audioSourceKey);
    }
  };

  const playAudio = async (audioBlob: Blob) => {
    try {
      if (!audioPlayerRef.current) {
        console.error('Audio player reference is not available');
        return;
      }

      if (!audioBlob) {
        console.warn('No audio blob provided');
        return;
      }

      // Clear any previous source
      audioPlayerRef.current.pause();
      audioPlayerRef.current.src = '';

      // Create and set new audio source
      const audioUrl = URL.createObjectURL(audioBlob);
      audioPlayerRef.current.src = audioUrl;

      // Explicitly set playing state
      const audioSourceKey = `${audioBlob.size}_${audioBlob.type}`;
      setIsPlaying(true);
      setCurrentPlayingAudioSrc(audioSourceKey);

      // Attempt to play audio
      try {
        await audioPlayerRef.current.play();
        // Explicitly set playing state to true
        setIsPlaying(true);
        setCurrentPlayingAudioSrc(audioSourceKey);
      } catch (error) {
        console.error('Error playing audio:', error);
        // Reset playing state if play fails
        setIsPlaying(false);
        setCurrentPlayingAudioSrc(null);
      }
    } catch (error) {
      console.error('Error in playAudio:', error);
    }
  };

  const speakAIText = async (text: string) => {
    try {
      setIsProcessing(true);
      
      // Generate a unique identifier for the AI speech
      const blobKey = `ai_speech_${text.length}_${selectedLanguage}`;

      // If this text is already playing, pause it
      if (currentPlayingAudioSrc === blobKey) {
        if (audioPlayerRef.current) {
          if (!audioPlayerRef.current.paused) {
            // If currently playing, pause
            console.log('Pausing AI speech');
            audioPlayerRef.current.pause();
            setIsPlaying(false);
          } else {
            // If paused, resume from current position
            console.log('Resuming AI speech');
            await audioPlayerRef.current.play();
          }
          return;
        }
      }

      // If a different audio is playing, stop it
      if (currentPlayingAudioSrc) {
        if (audioPlayerRef.current) {
          audioPlayerRef.current.pause();
          audioPlayerRef.current.currentTime = 0;
        }
      }

      // Request AI speech generation
      const formData = new FormData();
      formData.append('text', text);
      formData.append('language', selectedLanguage);
      
      const currentAccent = getCurrentAccent();
      if (!currentAccent) {
        throw new Error('Invalid language or accent selection');
      }
      formData.append('accent', currentAccent);

      const voiceName = voiceNameMapping[selectedLanguage]?.[currentAccent]?.[selectedVoiceGender] || 'en-US-JennyNeural';
      
      console.log('Voice Selection Debug:', {
        language: selectedLanguage,
        accent: currentAccent,
        gender: selectedVoiceGender,
        voiceName
      });
      
      formData.append('voice_name', voiceName);

      const response = await fetch(`${API_BASE_URL}/api/coach/generate-speech`, {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        throw new Error('Failed to generate AI speech');
      }

      const data = await response.json();
      const audioBlob = data.audio ? base64ToBlob(data.audio, 'audio/wav') : undefined;
      
      // Event listeners for audio playback
      const handlePlay = () => {
        console.log('AI Speech Play Event');
        setIsPlaying(true);
        setCurrentPlayingAudioSrc(blobKey);
      };
      
      const handlePause = () => {
        console.log('AI Speech Pause Event');
        setIsPlaying(false);
      };
      
      const handleEnded = () => {
        console.log('AI Speech Ended Event');
        setIsPlaying(false);
        setCurrentPlayingAudioSrc(null);
      };
      
      // Set up audio player
      if (audioPlayerRef.current) {
        audioPlayerRef.current.srcObject = null;
        if (audioBlob) {
          audioPlayerRef.current.src = URL.createObjectURL(audioBlob);
        } else {
          audioPlayerRef.current.src = '';
        }
        
        // Add event listeners
        audioPlayerRef.current.addEventListener('play', handlePlay);
        audioPlayerRef.current.addEventListener('pause', handlePause);
        audioPlayerRef.current.addEventListener('ended', handleEnded);
        
        try {
          // Attempt to play
          await audioPlayerRef.current.play();
          // Explicitly set playing state to true
          setIsPlaying(true);
          setCurrentPlayingAudioSrc(blobKey);
        } catch (error) {
          console.error('Error playing AI speech:', error);
          setIsPlaying(false);
          setCurrentPlayingAudioSrc(null);
        }
      }
    } catch (error) {
      console.error('Error generating AI speech:', error);
      if (axios.isAxiosError(error)) {
        const errorMessage = error.response?.data?.detail || "An error occurred while generating speech";
        setError(errorMessage);
      } else {
        setError('Failed to generate AI speech');
      }
    } finally {
      setIsProcessing(false);
    }
  };



  const processRecording = useCallback(async (audioBlob: Blob) => {
    try {
      setIsProcessing(true);
      setError(null);
      
      console.log('Processing recording:', {
        currentTopic,
        selectedTopic,
        topicToUse: currentTopic || selectedTopic,
        isKidsMode,
        messagesCount: messages.length
      });
      
      // Add a temporary loading message
      const loadingMessage: Message = {
        text: '',
        role: 'user',
        isUser: true,
        isLoading: true,
        topic: currentTopic || selectedTopic,
        grammarCorrection: undefined,
        grammarExplanation: undefined
      };
      setMessages(prev => [...prev, loadingMessage]);

      const formData = new FormData();
      formData.append('audio', audioBlob);
      formData.append('language', selectedLanguage);
      formData.append('accent', selectedAccent);
      
      const voiceName = voiceNameMapping[selectedLanguage]?.[getCurrentAccent()]?.[selectedVoiceGender] || 'en-US-JennyNeural';
      
      console.log('Voice Selection Debug:', {
        language: selectedLanguage,
        accent: getCurrentAccent(),
        gender: selectedVoiceGender,
        voiceName
      });
      
      formData.append('voice_name', voiceName);

      // Send the current topic and prevent_random flag
      if (currentTopic) {
        formData.append('topic', currentTopic);
      }
      formData.append('current_topic', currentTopic || selectedTopic);
      formData.append('is_kids_mode', String(isKidsMode));
      formData.append('prevent_random', String(isKidsMode));

      // Convert history to the format expected by the backend
      const formatHistoryForAPI = (messages: Message[]) => {
        return messages
          .filter((msg): msg is Message => msg.role !== 'system')  // Only skip system messages
          .map(msg => ({
            text: msg.text || '',  // Ensure text is always a string
            isUser: msg.isUser,
            topic_id: msg.topic || 'random'
          }));
      };

      const history = formatHistoryForAPI(messages);
      console.log('Sending message history:', {
        history,
        topicToUse: currentTopic || selectedTopic,
        isKidsMode
      });
      
      formData.append('history', JSON.stringify(history));

      console.log('here2...here2...here2...here2...here2...here2...here2...here2...here2...here2...here2...here2...')

      const response = await fetch(`${API_BASE_URL}/api/coach/generate-response`, {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', {
          status: response.status,
          statusText: response.statusText,
          body: errorText
        });
        throw new Error(`Failed to generate response: ${errorText}`);
      }

      const data = await response.json();
      console.log('Response from server:', data);
      console.log('Grammar feedback:', data.grammar_feedback);
      
      const { message, audio } = data;

      // Handle scoring in kids mode
      if (isKidsMode) {
        console.log('Checking grammar for scoring:', {
          grammar_feedback: data.grammar_feedback,
          explanation: data.explanation
        });

        if (data.grammar_feedback === 'Perfect!' || !data.explanation) {
          console.log('Adding 10 points for perfect grammar!');
          setScore(prev => prev + 10);
        } else if (data.explanation) {
          console.log('Subtracting 5 points for grammar mistake');
          setScore(prev => Math.max(0, prev - 5));
        }
      }

      // Remove the loading message
      setMessages(prev => prev.slice(0, -1));

      // If transcription is empty, show an error message instead of an empty bubble
      if (!data.transcribed_text || data.transcribed_text.trim() === '') {
        setError("I couldn't hear what you said. Please try speaking again.");
        return;
      }

      // Create user message with transcribed text
      const userMessage: Message = {
        text: data.transcribed_text,
        role: 'user',
        isUser: true,
        audioBlob: audioBlob,
        intonation: data.intonation,
        showIntonation: false,
        grammarCorrection: data.grammar_feedback || '',
        grammarExplanation: data.explanation || '',
        showGrammarExplanation: data.explanation ? true : false,
        topic: currentTopic || selectedTopic
      };

      // Create AI message
      const aiMessage: Message = {
        text: message,
        role: 'assistant',
        isUser: false,
        audioBlob: audio ? base64ToBlob(audio, 'audio/wav') : undefined,
        topic: currentTopic || selectedTopic,
        grammarCorrection: undefined,
        grammarExplanation: undefined
      };

      console.log('Creating new messages:', {
        userMessage,
        aiMessage,
        topic: currentTopic || selectedTopic
      });

      // Update messages while maintaining the topic
      setMessages(prev => [...prev, userMessage, aiMessage]);
      setCurrentTopic(currentTopic || selectedTopic);
      
      return data;
    } catch (error) {
      console.error('Error processing user message:', error);
      
      // Remove the loading message on error
      setMessages(prev => prev.slice(0, -1));
      
      // Handle Axios error response
      if (axios.isAxiosError(error) && error.response) {
        const errorMessage = error.response.data.error || "An error occurred while generating response";
        setError(errorMessage);
      } else {
        setError('Failed to process message');
      }
      
      throw error;
    } finally {
      setIsProcessing(false);
      setIsMessageLoading(false);
    }
  }, [selectedLanguage, selectedAccent, voiceNameMapping, selectedVoiceGender, selectedTopic, currentTopic, messages, isKidsMode, getCurrentAccent]);

  const getCurrentBackground = useCallback(() => {
    // Don't show backgrounds in adult mode
    if (!isKidsMode) {
      return 'none';
    }

    // Determine background based on current topic
    const backgroundMapping: { [key: string]: string } = {
      'animals': '/backgrounds/animals_bg.jpg',
      'superheroes': '/backgrounds/superhero_bg.jpg',
      'cartoon_characters': '/backgrounds/cartoon_characters_bg.jpg',
      'space': '/backgrounds/space_bg.jpg',
      'underwater': '/backgrounds/underwater_bg.jpg',
      'fantasy_world': '/backgrounds/fantasy_world_bg.jpg',
      'adventure': '/backgrounds/adventure_bg.jpg',
      'magic_forest': '/backgrounds/magic_forest_bg.jpg',
    };

    // Prioritize current topic, then fall back to selected topic
    const topicToUse = currentTopic || selectedTopic;
    const backgroundUrl = backgroundMapping[topicToUse];

    console.log('Selected background:', backgroundUrl);
    
    return backgroundUrl ? backgroundUrl : 'none';
  }, [currentTopic, selectedTopic, isKidsMode]);

  const getTopicDisplayName = useCallback((topic: string) => {
    const displayNames: { [key: string]: string } = {
      'animals': 'Animals',
      'superheroes': 'Superheroes',
      'cartoon_characters': 'Cartoon Characters',
      'space': 'Space Exploration',
      'underwater': 'Underwater World',
      'fantasy_world': 'Fantasy World',
      'adventure': 'Adventure',
      'magic_forest': 'Magic Forest',
    };

    // If exact match found, return it
    if (displayNames[topic]) {
      return displayNames[topic];
    }

    // Otherwise, convert snake_case to Title Case
    return topic
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }, []);

  const analyzeSpeech = async (messageIndex: number) => {
    try {
      const message = messages[messageIndex];
      if (!message.isUser || !message.audioBlob) {
        return;
      }

      console.log('rrrrrrr');
      // Update message state to show analysis in progress
      setMessages(prevMessages => 
        prevMessages.map((msg, idx) => 
          idx === messageIndex ? { ...msg, isAnalyzingPronunciation: true } : msg
        )
      );

      const formData = new FormData();
      formData.append('audio', message.audioBlob, 'audio.webm');
      formData.append('language', selectedLanguage);
      formData.append('accent', selectedAccent);
      formData.append('reference_text', message.text);
      formData.append('is_word_practice', 'false');  
      formData.append('is_kids_mode', String(isKidsMode)); 

      const response = await fetch(`${API_BASE_URL}/api/coach/analyze-pronunciation`, {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Pronunciation analysis failed:', response.status, errorText);
        throw new Error(`Pronunciation analysis failed: ${errorText}`);
      }

      const result = await response.json();
      console.log("Full message pronunciation analysis response:", result);

      if (result.pronunciation_feedback.error) {
        setError(result.pronunciation_feedback.error);
        // Reset analyzing state on error
        setMessages(prevMessages => 
          prevMessages.map((msg, idx) => 
            idx === messageIndex ? { ...msg, isAnalyzingPronunciation: false } : msg
          )
        );
        return;
      }

      // Update message state with analysis results
      setMessages(prevMessages => 
        prevMessages.map((msg, idx) => 
          idx === messageIndex ? {
            ...msg,
            isAnalyzingPronunciation: false,
            pronunciationFeedback: {
              pronunciation_score: result.pronunciation_feedback.pronunciation_score ?? 0,
              fluency_score: result.pronunciation_feedback.fluency_score ?? 0,
              feedback_messages: result.pronunciation_feedback.feedback_messages ?? [],
              poor_words: result.pronunciation_feedback.poor_words ?? []
            }
          } : msg
        )
      );

      setError(null);

    } catch (error) {
      console.error('Error analyzing speech:', error);
      
      // Reset analyzing state on error
      setMessages(prevMessages => 
        prevMessages.map((msg, idx) => 
          idx === messageIndex ? { ...msg, isAnalyzingPronunciation: false } : msg
        )
      );
    }
  };

  const togglePronunciationButton = (messageIndex: number) => {
    console.log('Toggle pronunciation button called with index:', messageIndex);
    const message = messages[messageIndex];
    console.log('Message at index:', message);
    
    // Set the state regardless of whether there's feedback
    setPronunciationButtonClicked(prevState => {
      const newState = !prevState;
      console.log('Pronunciation button state changed from:', prevState, 'to:', newState);
      return newState;
    });
    
    // If there's no pronunciation feedback yet, analyze the speech
    if (!message.pronunciationFeedback) {
      analyzeSpeech(messageIndex);
    }
  };

  const fetchPronunciationHelp = async (messageIndex: number) => {
    try {
      // Temporarily disable autoplay for this specific action
      const currentAutoplayState = isAutoplayEnabled;
      setCurrentAutoplayState(currentAutoplayState);  
      setIsAutoplayEnabled(false);

      const message = messages[messageIndex];
      console.log('Fetching pronunciation help for message:', message);

      if (!message.isUser || !message.pronunciationFeedback) {
        console.warn('Invalid message for pronunciation help:', message);
        return;
      }

      const poorWords = message.pronunciationFeedback.poor_words;
      console.log('Poor words:', poorWords);

      if (!poorWords || poorWords.length === 0) {
        console.warn('No poor words found');
        return;
      }

      // Check if pronunciation guidance is already cached
      if (message.pronunciationGuidance) {
        setPronunciationGuidanceModal({
          open: true,
          guidance: message.pronunciationGuidance,
          poorWords: poorWords,
          preventAutoplay: true
        });
        // Restore previous autoplay state
        setIsAutoplayEnabled(currentAutoplayState);
        return;
      }

      // Set loading state
      const updatedMessages = [...messages];
      updatedMessages[messageIndex] = {
        ...updatedMessages[messageIndex],
        isLoadingPronunciationGuidance: true
      };
      setMessages(updatedMessages);

      // Get current language and accent from the selected voice
      const currentAccent = getCurrentAccent();
      console.log('Current accent:', currentAccent);

      // Comprehensive mapping of accents to language codes
      const accentToLanguageMap: {[key: string]: string} = {
        // English variants
        'british': 'en-GB',
        'american': 'en-US',
        'australian': 'en-AU',
        'canadian': 'en-CA',
        'indian': 'en-IN',

        // French variants
        'parisian': 'fr-FR',
        'canadian french': 'fr-CA',
        'belgian': 'fr-BE',
        'swiss french': 'fr-CH',

        // Spanish variants
        'castilian': 'es-ES',
        'mexican': 'es-MX',
        'argentine': 'es-AR',

        // German variants
        'standard german': 'de-DE',
        'austrian': 'de-AT',
        'swiss german': 'de-CH',

        // Other languages
        'standard': selectedLanguage || 'en-US'  
      };

      // Determine language and accent
      let language = 'en-US';
      let accent = 'neutral';

      
      if (typeof currentAccent === 'string') {
        const normalizedAccent = currentAccent.toLowerCase().trim();
        language = accentToLanguageMap[normalizedAccent] || selectedLanguage || 'en-US';
        accent = normalizedAccent;
      }  else {
        // Fallback if currentAccent is neither a string nor an object with accent
        language = selectedLanguage || 'en-US';
        accent = 'neutral';
      }
      
      console.log('Sending pronunciation help request:', { language, accent });

      const response = await axios.post(`${API_BASE_URL}/api/coach/pronunciation-help`, { 
        poor_words: poorWords,
        language: language,
        accent: accent,
        is_kids_mode: true
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (response.data.success) {
        // Cache the pronunciation guidance in the message
        const finalUpdatedMessages = [...messages];
        finalUpdatedMessages[messageIndex] = {
          ...finalUpdatedMessages[messageIndex],
          pronunciationGuidance: response.data.pronunciation_help,
          isLoadingPronunciationGuidance: false
        };
        setMessages(finalUpdatedMessages);

        setPronunciationGuidanceModal({
          open: true,
          guidance: response.data.pronunciation_help,
          poorWords: poorWords,
          preventAutoplay: true
        });
      } else {
        console.error('Failed to get pronunciation help:', response.data);
        
        // Reset loading state
        const finalUpdatedMessages = [...messages];
        finalUpdatedMessages[messageIndex] = {
          ...finalUpdatedMessages[messageIndex],
          isLoadingPronunciationGuidance: false
        };
        setMessages(finalUpdatedMessages);

        setPronunciationGuidanceModal({
          open: true,
          guidance: 'Sorry, I could not generate pronunciation help at the moment.',
          poorWords: poorWords,
          preventAutoplay: true
        });
      }

      // Restore previous autoplay state
      setIsAutoplayEnabled(currentAutoplayState);
    } catch (error) {
      console.error('Error fetching pronunciation help:', error);
      
      // Reset loading state
      const finalUpdatedMessages = [...messages];
      finalUpdatedMessages[messageIndex] = {
        ...finalUpdatedMessages[messageIndex],
        isLoadingPronunciationGuidance: false
      };
      setMessages(finalUpdatedMessages);

      setPronunciationGuidanceModal({
        open: true,
        guidance: 'An error occurred while generating pronunciation help. Please try again later.',
        poorWords: [],
        preventAutoplay: true
      });

      // Restore previous autoplay state
      setIsAutoplayEnabled(currentAutoplayState);
    }
  };

  const formatGrammarSuggestion = (correction: string) => {
    // If the correction starts with a suggestion marker like "Suggestion:", remove it
    const cleanCorrection = correction.replace(/^(Suggestion|Correction):\s*/i, '');
    return cleanCorrection;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'success.main';
    if (score >= 60) return 'warning.main';
    return 'error.main';
  };

  const base64ToBlob = (base64: string, mimeType: string): Blob => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  };

 /* const convertToWav = async (audioBuffer: AudioBuffer): Promise<ArrayBuffer> => {
    const numOfChannels = 1; // Mono
    const sampleRate = 16000; // 16kHz
    const bitsPerSample = 16;
    const bytesPerSample = bitsPerSample / 8;
    
    // Get the PCM data from the first channel and convert to 16-bit
    const samples = audioBuffer.getChannelData(0);
    const buffer = new ArrayBuffer(44 + samples.length * bytesPerSample);
    const view = new DataView(buffer);
    
    // Write WAV header
    const writeString = (view: DataView, offset: number, string: string) => {
      for (let i = 0; i <string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    
    writeString(view, 0, 'RIFF');  // ChunkID
    view.setUint32(4, 36 + samples.length * bytesPerSample, true);  // ChunkSize
    writeString(view, 8, 'WAVE');  // Format
    writeString(view, 12, 'fmt ');  // Subchunk1ID
    view.setUint32(16, 16, true);  // Subchunk1Size
    view.setUint16(20, 1, true);   // AudioFormat (PCM)
    view.setUint16(22, numOfChannels, true);  // NumChannels
    view.setUint32(24, sampleRate, true);     // SampleRate
    view.setUint32(28, sampleRate * numOfChannels * bytesPerSample, true);  // ByteRate
    view.setUint16(32, numOfChannels * bytesPerSample, true);  // BlockAlign
    view.setUint16(34, bitsPerSample, true);  // BitsPerSample
    writeString(view, 36, 'data');  // Subchunk2ID
    view.setUint32(40, samples.length * bytesPerSample, true);  // Subchunk2Size
    
    // Write PCM samples
    const offset = 44;
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset + i * bytesPerSample, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    
    return buffer;
  };*/

  /*const handlePronunciationHelp = async (message: Message, words: any[]) => {
    try {
      const messageIndex = messages.findIndex(m => m.text === message.text);
      if (messageIndex === -1) return;

      // Update message state to show loading
      setMessages(prev => prev.map((m, i) => 
        i === messageIndex 
          ? {...m, isLoadingPronunciationGuidance: true }
          : m
      ));

      // Fetch pronunciation help
      await fetchPronunciationHelp(messageIndex);
    } catch (error) {
      console.error('Error getting pronunciation help:', error);
    }
  };*/

  const handleRecordWord = async (word: string) => {
    try {
      console.log("Record word state before:", {
        pronunciationRecording,
        wordError,
        currentPronunciationWord,
        word
      });

      if (pronunciationRecording && currentPronunciationWord === word) {
        await stopPronunciationRecording();
        // Don't clear states here, let the result handler do it
      } else {
        if (pronunciationRecording) {
          await stopPronunciationRecording();
        }
        setCurrentPronunciationWord(word);
        setWordError(null);
        await startPronunciationRecording(word);
      }

      console.log("Record word state after:", {
        pronunciationRecording,
        wordError,
        currentPronunciationWord,
        word
      });
    } catch (error) {
      console.error('Error handling word recording:', error);
      setError('Failed to start recording. Please check your microphone permissions.');
      setWordError('Failed to start recording. Please check your microphone permissions.');
      setCurrentPronunciationWord('');
    }
  };

  const handlePronunciationResult = async (audioBlob: Blob, word: string) => {
    try {
      console.log("Pronunciation result state before:", {
        pronunciationRecording,
        wordError,
        currentPronunciationWord,
        word
      });

      const formData = new FormData();
      // Ensure we're sending a Blob with the correct MIME type
      const audioFile = new Blob([audioBlob], { type: 'audio/webm' });
      formData.append('audio', audioFile, 'audio.webm');
      formData.append('reference_text', word);
      formData.append('language', 'en');  
      formData.append('accent', 'neutral');  
      formData.append('is_word_practice', 'true');  
      formData.append('is_kids_mode', 'true');  

      const response = await fetch(`${API_BASE_URL}/api/coach/analyze-pronunciation`, {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Pronunciation analysis failed:', response.status, errorText);
        throw new Error(`Pronunciation analysis failed: ${errorText}`);
      }

      const result = await response.json();
      console.log("Pronunciation API response:", result);
      console.log("Pronunciation API response2:", result.pronunciation_feedback.error);

      if (result.pronunciation_feedback.error) {
        setWordError(result.pronunciation_feedback.error);
        setCurrentPronunciationWord(word); 
        // Restore autoplay state
        setIsAutoplayEnabled(true);
        return;
      }

      // Ensure we have valid pronunciation feedback data
      const pronunciationFeedback = {
        pronunciation_score: result.pronunciation_feedback?.pronunciation_score ?? 0,
        fluency_score: result.pronunciation_feedback?.fluency_score ?? 0,
        feedback_messages: result.pronunciation_feedback?.feedback_messages ?? [],
        poor_words: [{
          word: word,
          accuracy: result.pronunciation_feedback?.pronunciation_score ?? 0
        }]
      };

      // Update the message containing this word with the new pronunciation feedback
      setMessages(prevMessages => 
        prevMessages.map(msg => {
          if (msg.pronunciationFeedback?.poor_words.some(pw => pw.word.toLowerCase() === word.toLowerCase())) {
            return {
              ...msg,
              pronunciationFeedback: {
                ...pronunciationFeedback,
                poor_words: msg.pronunciationFeedback.poor_words.map(pw => 
                  pw.word.toLowerCase() === word.toLowerCase() ? {
                    ...pw,
                    initial_accuracy: pw.initial_accuracy ?? pw.accuracy,
                    accuracy: pronunciationFeedback.pronunciation_score
                  } : pw
                )
              }
            };
          }
          return msg;
        })
      );

      if (pronunciationFeedback.pronunciation_score >= 80) {
        setError(null);
      }

      // Keep autoplay disabled after word practice
      setIsAutoplayEnabled(false);

      return result;
    } catch (error) {
      console.error('Error analyzing pronunciation:', error);
      setError('Failed to analyze pronunciation. Please try again.');
      setWordError('Failed to analyze pronunciation. Please try again.');
      setCurrentPronunciationWord('');
      // Restore autoplay state on error
      setIsAutoplayEnabled(true);
    }
  };

  const playRecordedAudio = async (word: string) => {
    console.log('Attempting to play audio for word:', word);
    console.log('Available recordings:', Object.keys(recordedAudioBlobs));
    const audioBlob = recordedAudioBlobs[word];
    if (audioBlob) {
      console.log('Found audio blob for word:', word, 'size:', audioBlob.size);
      const url = URL.createObjectURL(audioBlob);
      const audio = new Audio(url);
      await audio.play();
      // Clean up URL after playback
      audio.onended = () => URL.revokeObjectURL(url);
    } else {
      console.log('No audio blob found for word:', word);
    }
  };

  const [wordError, setWordError] = useState<string | null>(null);

  // Add smileys to text for kids mode
  const addSmileysToText = (text: string | undefined) => {
    if (!text) return '';
    
    const smileys = ['😊', '🌟', '✨', '🎈', '🎨', '🌈', '🦄', '🐼', '🦁', '🐯', '🐰'];
    const randomSmiley = () => smileys[Math.floor(Math.random() * smileys.length)];
    const sentences = text.split(/(?<=[.!?])\s+/);
    return sentences.map(sentence => `${sentence} ${randomSmiley()}`).join(' ');
  };

  const renderMessage = (message: Message, index: number) => {
    // Check if this is the most recent AI message and is still loading
    const isLoading = message.role === 'assistant' && 
      index === messages.length - 1 && 
      isMessageLoading;

    // Show loading state for user message while processing
    const isProcessingUserMessage = message.isUser && 
      index === messages.length - 1 && 
      (isProcessing || message.isLoading);
    
    // Add a null check to ensure we always return a valid React node
    if (!message) {
      return null;
    }

    return (
      <Box
        key={index}
        sx={{
          display: 'flex',
          flexDirection: message.isUser ? 'row-reverse' : 'row',
          mb: 2,
          gap: 1,
        }}
      >
        {/* Avatar */}
        <Avatar
          sx={{
            bgcolor: message.isUser ? 'primary.main' : 'secondary.main',
            width: 40,
            height: 40,
          }}
        >
          {message.isUser ? 'U' : message.role === 'assistant' ? 'AI' : 'S'}
        </Avatar>

        {/* Message Content */}
        <Box
          sx={{
            maxWidth: '70%',
            minWidth: '20%',
          }}
        >
          <Paper
            elevation={1}
            sx={{
              p: 2,
              borderRadius: 2,
              bgcolor: message.isUser ? 'primary.light' : 'background.paper',
              color: message.isUser ? 'primary.contrastText' : 'text.primary',
              position: 'relative',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 20,
                [message.isUser ? 'right' : 'left']: -10,
                borderStyle: 'solid',
                borderWidth: '10px 10px 0',
                borderColor: `${message.isUser ? 'primary.light' : 'background.paper'} transparent transparent`,
                transform: message.isUser ? 'rotate(-45deg)' : 'rotate(45deg)',
              },
            }}
          >
            {/* Message Text or Loading Indicator */}
            {isProcessingUserMessage ? (
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1,
                minHeight: '24px' 
              }}>
                <CircularProgress size={20} color="inherit" />
                <Typography variant="body1">
                  Processing your message...
                </Typography>
              </Box>
            ) : (
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {message.isUser || !isKidsMode ? (
                  message.text
                ) : (
                  <Box component="span">
                    {addSmileysToText(message.text).split(' ').map((word, i) => (
                      <Box
                        key={i}
                        component="span"
                        sx={{
                          display: 'inline-block',
                          position: 'relative',
                          mr: 1,
                          '&:hover .magic-wand': {
                            opacity: 1,
                            transform: 'translateY(0)',
                          }
                        }}
                      >
                        {word}
                        {!word.match(/[😊🌟✨🎈🎨🌈🦄🐼🦁🐯🐰]/) && (
                          <IconButton
                            className="magic-wand"
                            size="small"
                            onClick={() => handleWandClick(word)}
                            disabled={isWandActive}
                            sx={{
                              position: 'absolute',
                              top: '-20px',
                              left: '50%',
                              transform: 'translateX(-50%) translateY(5px)',
                              opacity: 0,
                              transition: 'all 0.2s ease-in-out',
                              backgroundColor: 'primary.light',
                              '&:hover': {
                                backgroundColor: 'primary.main',
                              },
                              width: '20px',
                              height: '20px',
                              '& svg': {
                                width: '14px',
                                height: '14px',
                              }
                            }}
                          >
                            <AutoFixHighIcon />
                          </IconButton>
                        )}
                      </Box>
                    ))}
                  </Box>
                )}
              </Typography>
            )}

            {/* Grammar Feedback */}
            {message.isUser && message.grammarCorrection && (
              <Paper
                elevation={0}
                sx={{
                  mt: 2,
                  p: 2,
                  borderRadius: 1,
                  bgcolor: 'info.50',
                  borderLeft: 4,
                  borderColor: 'info.main',
                }}
              >
                {message.grammarCorrection ? (
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                    <RateReviewIcon color="info" sx={{ mt: 0.5 }} />
                    <Box>
                      <Typography variant="subtitle2" color="info.main" sx={{ fontWeight: 600, mb: 0.5 }}>
                        Grammar Suggestion
                      </Typography>
                      <Typography variant="body2" color="text.primary">
                        {formatGrammarSuggestion(message.grammarCorrection)}
                      </Typography>
                      {message.grammarExplanation && message.showGrammarExplanation && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="subtitle2" color="info.main" sx={{ fontWeight: 600, mb: 0.5 }}>
                            Explanation
                          </Typography>
                          <Typography variant="body2" color="text.primary">
                            {message.grammarExplanation}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </Box>
                ) : null}
              </Paper>
            )}

            {/* Intonation Feedback */}
            {message.isUser && message.intonation && message.showIntonation && (
              <Paper
                elevation={0}
                sx={{
                  mt: 2,
                  p: 2,
                  borderRadius: 1,
                  bgcolor: 'warning.50',
                  borderLeft: 4,
                  borderColor: 'warning.main',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                  <GraphicEqIcon color="warning" sx={{ mt: 0.5 }} />
                  <Box>
                    <Typography variant="subtitle2" color="warning.main" sx={{ fontWeight: 600, mb: 0.5 }}>
                      Intonation Guidance
                    </Typography>
                    <Typography variant="body2" color="text.primary">
                      {message.intonation}
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            )}

            {/* Message Controls */}
            {!isLoading && (
              <Box sx={{ 
                display: 'flex', 
                gap: 1, 
                mt: 2,
                flexWrap: 'wrap',
                alignItems: 'center',
                opacity: 0.9,
                '&:hover': {
                  opacity: 1
                }
              }}>
                {message.audioBlob && (
                  <Tooltip title={isPlaying ? "Pause audio" : "Play audio"} arrow>
                    <IconButton
                      onClick={async () => {
                        await handlePlayPauseAudio(message);
                      }}
                      sx={{ 
                        color: 'primary.main',
                        bgcolor: 'background.paper',
                        boxShadow: 1,
                        '&:hover': {
                          bgcolor: 'primary.light',
                          color: 'white'
                        }
                      }}
                    >
                      {isPlaying && currentPlayingAudioSrc === `${message.audioBlob.size}_${message.audioBlob.type}` ? (
                        <PauseIcon />
                      ) : (
                        <PlayArrowIcon />
                      )}
                    </IconButton>
                  </Tooltip>
                )}
                {message.isUser && (
                  <Tooltip title="Listen to AI voice" arrow>
                    <IconButton
                      size="small"
                      onClick={() => speakAIText(message.text)}
                      sx={{ 
                        color: 'secondary.main',
                        bgcolor: 'background.paper',
                        boxShadow: 1,
                        '&:hover': {
                          bgcolor: 'secondary.light',
                          color: 'white'
                        }
                      }}
                    >
                      {isPlaying && currentPlayingAudioSrc === `ai_speech_${message.text.length}_${selectedLanguage}` ? (
                        <PauseIcon />
                      ) : (
                        <RecordVoiceOverIcon />
                      )}
                    </IconButton>
                  </Tooltip>
                )}
                {message.isUser && (
                  <Tooltip title="Analyze pronunciation" arrow>
                    <IconButton
                      size="small"
                      disabled={message.isAnalyzingPronunciation}
                      onClick={() => togglePronunciationButton(messages.findIndex(m => m.text === message.text))}
                      sx={{ 
                        color: 'success.main',
                        bgcolor: 'background.paper',
                        boxShadow: 1,
                        '&:hover': {
                          bgcolor: 'success.light',
                          color: 'white'
                        },
                        '&.Mui-disabled': {
                          bgcolor: 'action.disabledBackground'
                        }
                      }}
                    >
                      {message.isAnalyzingPronunciation ? (
                        <CircularProgress size={20} color="inherit" />
                      ) : (
                        <SpellcheckIcon />
                      )}
                    </IconButton>
                  </Tooltip>
                )}
                {message.isUser && message.pronunciationFeedback && 
                 message.pronunciationFeedback.poor_words && 
                 message.pronunciationFeedback.poor_words.length > 0 && (
                  <Button
                    variant="outlined"
                    size="small"
                    disabled={message.isLoadingPronunciationGuidance}
                    onClick={() => fetchPronunciationHelp(messages.findIndex(m => m.text === message.text))}
                    startIcon={message.isLoadingPronunciationGuidance ? 
                      <CircularProgress size={16} /> : 
                      <RecordVoiceOverIcon />
                    }
                    sx={{
                      bgcolor: 'background.paper',
                      boxShadow: 1,
                      '&:hover': {
                        bgcolor: 'primary.light',
                        color: 'white'
                      }
                    }}
                  >
                    {message.isLoadingPronunciationGuidance ? 'Generating...' : 'Get Help'}
                  </Button>
                )}
                {message.isUser && message.intonation && (
                  <Tooltip title={message.showIntonation ? "Hide intonation" : "Show intonation"} arrow>
                    <IconButton
                      size="small"
                      onClick={() => {
                        if (audioPlayerRef.current) {
                          audioPlayerRef.current.pause();
                          setIsPlaying(false);
                        }
                        setIntonationButtonClicked(true);
                        setMessages(prev => 
                          prev.map(m => 
                            m.text === message.text 
                              ? {...m, showIntonation: !m.showIntonation} 
                              : m
                          )
                        );
                      }}
                      sx={{ 
                        color: message.showIntonation ? 'warning.main' : 'text.secondary',
                        bgcolor: 'background.paper',
                        boxShadow: 1,
                        '&:hover': {
                          bgcolor: 'warning.light',
                          color: 'white'
                        }
                      }}
                    >
                      {message.showIntonation ? <TrendingDownIcon /> : <TrendingUpIcon />}
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            )}

            {/* Pronunciation Feedback */}
            {message.pronunciationFeedback && (
              <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                {/* Score Display */}
                <Box sx={{ 
                  display: 'flex', 
                  alignItems: 'center',
                  gap: 1,
                  mb: 2,
                  p: 2,
                  borderRadius: 1,
                  bgcolor: 'background.paper',
                  borderLeft: 3,
                  borderColor: getScoreColor(message.pronunciationFeedback.pronunciation_score)
                }}>
                  <SpellcheckIcon color="primary" />
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle1" color="text.primary" sx={{ fontWeight: 600, mb: 0.5 }}>
                      Pronunciation Score:
                    </Typography>
                    <Box
                      sx={{
                        px: 1.5,
                        py: 0.5,
                        borderRadius: 1,
                        bgcolor: getScoreColor(message.pronunciationFeedback.pronunciation_score),
                        color: 'white',
                        fontWeight: 600
                      }}
                    >
                      {message.pronunciationFeedback.pronunciation_score.toFixed(1)}%
                    </Box>
                  </Box>
                </Box>

                {/* Feedback Messages */}
                {message.pronunciationFeedback.feedback_messages.map((feedback, idx) => (
                  <Box
                    key={idx}
                    sx={{
                      mb: 2,
                      p: 2,
                      borderRadius: 1,
                      bgcolor: 'background.paper',
                      boxShadow: 1,
                      borderLeft: 3,
                      borderColor: feedback.toLowerCase().includes('great') || feedback.toLowerCase().includes('good')
                        ? 'success.main'
                        : feedback.toLowerCase().includes('improve') || feedback.toLowerCase().includes('focus')
                        ? 'warning.main'
                        : 'info.main',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                      {feedback.toLowerCase().includes('great') || feedback.toLowerCase().includes('good') ? (
                        <CheckCircleIcon color="success" />
                      ) : feedback.toLowerCase().includes('improve') || feedback.toLowerCase().includes('focus') ? (
                        <InfoIcon color="warning" />
                      ) : (
                        <TipsAndUpdatesIcon color="info" />
                      )}
                      <Typography variant="body2" color="text.primary">{feedback}</Typography>
                    </Box>
                  </Box>
                ))}

                {/* Words to Practice */}
                {message.pronunciationFeedback.poor_words && 
                 message.pronunciationFeedback.poor_words.length > 0 && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle1" color="primary" sx={{ 
                      mb: 2,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      color: 'text.primary'
                    }}>
                      <MusicNoteIcon />
                      Words to Practice
                    </Typography>
                    
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {message.pronunciationFeedback.poor_words.map((word, idx) => (
                        <Paper
                          key={`${word.word}-${idx}`}
                          elevation={2}
                          component="div"
                          sx={{
                            p: 2,
                            mb: 2,
                            borderRadius: 2,
                            bgcolor: 'background.default'
                          }}
                        >
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                            <Typography variant="h6" color="text.primary">{word.word}</Typography>
                            <Box
                              sx={{
                                px: 1.5,
                                py: 0.5,
                                borderRadius: 1,
                                bgcolor: typeof word.accuracy === 'number' 
                                  ? getScoreColor(word.accuracy)
                                  : 'warning.main',
                                color: 'white',
                                fontWeight: 600
                              }}
                            >
                              {typeof word.accuracy === 'number' ? `${word.accuracy.toFixed(0)}%` : 'N/A'}
                            </Box>
                          </Box>

                          {/* Word Practice Controls */}
                          <Grid container spacing={2}>
                            <Grid item xs={12} md={6}>
                              <Button
                                startIcon={<VolumeUpIcon />}
                                variant="contained"
                                onClick={() => speakAIText(word.word)}
                                fullWidth
                              >
                                Listen to AI
                              </Button>
                            </Grid>
                            <Grid item xs={12} md={6}>
                              <Button
                                variant="contained"
                                color="primary"
                                onClick={() => handleRecordWord(word.word)}
                                startIcon={pronunciationRecording && currentPronunciationWord === word.word ? <StopIcon /> : <MicIcon />}
                                sx={{
                                  transition: 'all 0.2s ease-in-out',
                                  position: 'relative',
                                  overflow: 'hidden',
                                  '&:hover': {
                                    bgcolor: pronunciationRecording && currentPronunciationWord === word.word ? 'error.dark' : 'primary.dark',
                                  },
                                  '&::after': pronunciationRecording && currentPronunciationWord === word.word ? {
                                    content: '""',
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                    right: 0,
                                    bottom: 0,
                                    background: 'rgba(255, 255, 255, 0.1)',
                                    animation: 'pulse 1.5s ease-in-out infinite'
                                  } : {}
                                }}
                                fullWidth
                              >
                                {pronunciationRecording && currentPronunciationWord === word.word ? (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    Stop Recording
                                  </Box>
                                ) : (
                                  'Record'
                                )}
                              </Button>
                            </Grid>
                           
                          </Grid>

                          {recordedAudioBlobs[word.word] ? (
                            <Button
                              variant="outlined"
                              size="small"
                              startIcon={<PlayArrowIcon />}
                              onClick={() => playRecordedAudio(word.word)}
                              sx={{ mt: 1 }}
                            >
                              Listen to Recording
                            </Button>
                          ) : null}
                        
                      

                          {pronunciationRecording && currentPronunciationWord === word.word && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'error.main' }}>
                              <CircularProgress size={16} color="error" />
                              <Typography variant="body2" color="error">Recording in progress...</Typography>
                            </Box>
                          )}


                          {wordError && word.word === currentPronunciationWord && (
                            <Box sx={{ 
                              mt: 1,
                              p: 1.5,
                              borderRadius: 1,
                              bgcolor: 'error.50',
                              borderLeft: 3,
                              borderColor: 'error.main',
                              display: 'flex',
                              alignItems: 'flex-start',
                              gap: 1
                            }}>
                              <ErrorOutlineIcon color="error" sx={{ mt: 0.2 }} />
                              <Typography variant="body2" color="error.main">
                                {wordError}
                              </Typography>
                            </Box>
                          )}

                          {!pronunciationRecording && !wordError && word.transcribed_text && (
                            <Box sx={{ 
                              mt: 1,
                              p: 1.5,
                              borderRadius: 1,
                              bgcolor: 'info.50',
                              borderLeft: 3,
                              borderColor: 'info.main',
                              display: 'flex',
                              alignItems: 'flex-start',
                              gap: 1
                            }}>
                              <InfoIcon color="info" sx={{ mt: 0.2 }} />
                              <Typography variant="body2" color="info.main">
                                You said: "{word.transcribed_text}"
                              </Typography>
                            </Box>
                          )}
                        </Paper>
                      ))}
                    </Box>
                  </Box>
                )}
              </Box>
            )}
          </Paper>
        </Box>
      </Box>
    );
  };

  const kidsTopics = [
    'animals', 'superheroes', 'fairy_tales', 'space_adventure', 'dinosaurs',
    'magic_school', 'pirates', 'jungle_safari', 'underwater_world',
    'cartoon_characters'
  ];

  const adultTopics = [
    'hobbies', 'travel', 'food', 'movies', 'role_play', 'everyday_situations',
    'debates', 'current_events', 'personal_growth'
  ];

  const topicOptions = isKidsMode ? kidsTopics : adultTopics;

  useEffect(() => {
    console.log('Mode changed, resetting topics:', {
      isKidsMode,
      previousTopic: selectedTopic
    });
    setSelectedTopic('random');
    setCurrentTopic(null);
  }, [isKidsMode]);

  useEffect(() => {
    console.log('Topic options updated:', {
      isKidsMode,
      topicOptions,
      selectedTopic,
      currentTopic
    });
  }, [isKidsMode, topicOptions, selectedTopic, currentTopic]);

  useEffect(() => {
    if (selectedTopic === 'random') {
      const availableTopics = isKidsMode ? kidsTopics : adultTopics;
      console.log('Initial random topic selection:', {
        isKidsMode,
        selectedTopic,
        availableTopics,
        topicCount: availableTopics.length
      });
      
      const randomIndex = Math.floor(Math.random() * availableTopics.length);
      const randomTopic = availableTopics[randomIndex];
      
      console.log('Selected random topic:', {
        randomIndex,
        randomTopic,
        allTopics: availableTopics
      });
      
      setCurrentTopic(randomTopic);
    }
  }, [selectedTopic, isKidsMode]);

  

  // Background mapping for kids topics
  

  // Add magic wand state
  const [isWandActive, setIsWandActive] = useState(false);
  const [, setSelectedWord] = useState<string>('');

  // Handle magic wand click
  const handleWandClick = async (word: string) => {
    setIsWandActive(true);
    setSelectedWord(word);
    
    try {
      const formData = new FormData();
      formData.append('text', word);
      formData.append('voice_name', voiceNameMapping[selectedLanguage]?.[getCurrentAccent()]?.[selectedVoiceGender] || 'en-US-JennyNeural');
      
      const response = await fetch(`${API_BASE_URL}/api/coach/generate-speech`, {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        throw new Error('Failed to generate speech');
      }

      const data = await response.json();
      if (data.audio) {
        const audioBlob = base64ToBlob(data.audio, 'audio/wav');
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        await audio.play();
        URL.revokeObjectURL(audioUrl);
      }
    } catch (error) {
      console.error('Error playing word:', error);
    } finally {
      setIsWandActive(false);
    }
  };

  // Helper function to get display name for topic
  

  const [showDrawingCanvas, setShowDrawingCanvas] = useState(false);

  useEffect(() => {
    if (isKidsMode) {
      setShowDrawingCanvas(true);
    } else {
      setShowDrawingCanvas(false);
    }
  }, [isKidsMode]);

  const [score, setScore] = useState(0);

  useEffect(() => {
    if (!isKidsMode) return;
  }, [isKidsMode]);

  useEffect(() => {
    if (isKidsMode) {
      setSelectedVoiceGender('kid');
    }
  }, [isKidsMode]);


  const [pastConversations, setPastConversations] = useState<any[]>([]);
  const [isPastConversationsOpen, setIsPastConversationsOpen] = useState(false);
  const [isLoadingPastConversations, setIsLoadingPastConversations] = useState(false);

  const handleLoadPastConversations = async () => {
    console.group('Handle Load Past Conversations');
    console.log('Function Called', {
      currentUser: auth.currentUser ? {
        uid: auth.currentUser.uid,
        email: auth.currentUser.email
      } : 'No User'
    });

    // Ensure user is authenticated
    if (!auth.currentUser) {
      console.warn('User must be logged in to view past conversations');
      console.groupEnd();
      return;
    }

    try {
      // Show loading state
      setIsLoadingPastConversations(true);
      console.log('Loading past conversations...');

      // Fetch conversation history
      const conversations = await getConversationHistory();
      
      // Log loaded conversations for debugging
      console.log('Loaded Past Conversations:', {
        count: conversations.length,
        topics: conversations.map(conv => conv.topicName)
      });

      // Update conversations state first
      setPastConversations(conversations);
      
      // Use functional update to ensure correct state
      setIsPastConversationsOpen(prevState => {
        const newState = conversations.length > 0;
        console.log('Panel State Updated:', {
          previousState: prevState,
          newState: newState,
          conversationsCount: conversations.length
        });
        return newState;
      });

      // Additional logging to confirm state
      console.log('Panel State After Opening:', {
        conversationsLength: conversations.length
      });

    } catch (error) {
      console.error('Detailed Error loading past conversations:', {
        errorName: error.name,
        errorMessage: error.message,
        errorStack: error.stack
      });
    } finally {
      // Always hide loading state
      setIsLoadingPastConversations(false);
      console.groupEnd();
    }
  };

  const handleSelectPastConversation = async (conversationId: string) => {
    console.group('Select Past Conversation');
    console.log('Loading conversation:', conversationId);

    try {
      // Load the specific conversation
      const conversation = await loadConversation(conversationId);
      
      if (!conversation) {
        console.error('No conversation found with ID:', conversationId);
        return;
      }

      // Log conversation details for debugging
      console.log('Loaded Conversation Details:', {
        id: conversation.id,
        topicName: conversation.topicName,
        messageCount: conversation.messages?.length,
        originalTimestamp: conversation.originalTimestamp
      });

      // Reset necessary states to prepare for conversation resumption
      setIsLoadingConversation(true);
      
      // Set conversation-specific states
      setSelectedLanguage(conversation.language || 'en');
      setSelectedAccent(conversation.accent || 'neutral');
      setSelectedTopic(conversation.topicName || 'random');
      
      // Populate messages with correct roles
      if (conversation.messages && conversation.messages.length > 0) {
        // Map messages to ensure correct role and isUser attribute
        const formattedMessages = conversation.messages.map(msg => ({
          ...msg,
          role: msg.role || (msg.isUser ? 'user' : 'assistant'),
          isUser: msg.isUser !== undefined 
            ? msg.isUser 
            : (msg.role === 'user' || msg.isUser === true)
        }));

        // Set the entire message history
        setMessages(formattedMessages);
        
        // Determine the last AI message to start from
        const lastAIMessage = formattedMessages
          .filter(msg => msg.role === 'assistant')
          .pop();
        
        if (lastAIMessage) {
          console.log('Resuming from last AI message:', lastAIMessage.text);
          
          // Optional: Trigger AI to continue from the last message
          await handleContinueConversation(lastAIMessage);
        }
      }

      // Mark conversation as started
      setHasStarted(true);
      
      // Close past conversations panel
      setIsPastConversationsOpen(false);

      console.log('Conversation Resumed Successfully');
    } catch (error) {
      console.error('Error loading past conversation:', {
        errorName: error.name,
        errorMessage: error.message,
        errorStack: error.stack
      });
    } finally {
      setIsLoadingConversation(false);
      console.groupEnd();
    }
  };

  // Helper function to continue conversation from last message
  const handleContinueConversation = async (lastMessage: Message) => {
    try {
      // Prepare the context for continuing the conversation
      const continueContext: Message = {
        role: 'user',
        text: `Continue our previous conversation from where we left off. The last message was: "${lastMessage.text}". Please pick up the conversation naturally.`,
        isUser: true,
        timestamp: Date.now()
      };

      // Add the continue message to the conversation
      setMessages(prevMessages => [...prevMessages, continueContext]);

      // Trigger AI response
      await processRecording(new Blob([continueContext.text], { type: 'text/plain' }));
    } catch (error) {
      console.error('Error continuing conversation:', error);
    }
  };

  const PastConversationsButton = () => {
    const handleClick = () => {
      setIsPastConversationsOpen(!isPastConversationsOpen);
    };

    return (
      <Tooltip title="View Past Conversations">
        <span style={{ display: 'inline-block' }}>
          <IconButton 
            onClick={handleClick}
            color="primary"
            sx={{
              position: 'absolute',
              top: 16,
              right: 16,
              zIndex: 20,
            }}
          >
            {isLoadingPastConversations ? (
              <CircularProgress size={24} />
            ) : (
              <HistoryIcon />
            )}
          </IconButton>
        </span>
      </Tooltip>
    );
  };

  const [isLoadingConversation, setIsLoadingConversation] = useState(false);

  if (!hasStarted) {
    return (
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        height: '100%', 
        width: '100%' 
      }}>
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          height: '100%', 
          width: '100%' 
        }}>
          <PastConversationsButton />
          <Collapse 
            in={isPastConversationsOpen} 
            unmountOnExit 
            sx={{ 
              width: '100%', 
              position: 'relative',
              zIndex: 10,
              mt: 1  // Add margin top to position below the button
            }}
          >
            <Paper 
              elevation={4} 
              sx={{ 
                width: '100%', 
                backgroundColor: 'background.paper', 
                borderRadius: 2,
                p: 2
              }}
            >
              {/* Existing past conversations content */}
              <Stack 
                direction="row" 
                justifyContent="space-between" 
                alignItems="center" 
                sx={{ mb: 2 }}
              >
                <Typography variant="h6" fontWeight="bold">
                  Past Conversations
                </Typography>
                <IconButton 
                  onClick={() => setIsPastConversationsOpen(false)}
                  size="small"
                >
                  <CloseIcon />
                </IconButton>
              </Stack>

              <Grid container spacing={2}>
                {pastConversations.map((conversation) => (
                  <Grid item xs={12} key={conversation.id}>
                    <Paper 
                      variant="outlined"
                      sx={{ 
                        p: 2, 
                        cursor: 'pointer', 
                        transition: 'all 0.3s ease',
                        '&:hover': { 
                          backgroundColor: 'action.hover',
                          transform: 'scale(1.01)'
                        } 
                      }}
                      onClick={() => {
                        console.log('Conversation Selected:', {
                          id: conversation.id,
                          topicName: conversation.topicName
                        });
                        handleSelectPastConversation(conversation.id);
                        setIsPastConversationsOpen(false);
                      }}
                    >
                      <Grid container justifyContent="space-between" alignItems="center">
                        <Grid item xs={10}>
                          <Typography variant="subtitle1" fontWeight="bold">
                            {conversation.topicName || 'Untitled Conversation'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {new Date(conversation.originalTimestamp).toLocaleString()}
                          </Typography>
                          <Typography 
                            variant="body2" 
                            color="text.secondary" 
                            sx={{ 
                              overflow: 'hidden', 
                              textOverflow: 'ellipsis', 
                              whiteSpace: 'nowrap' 
                            }}
                          >
                            {conversation.messages?.[0]?.text?.slice(0, 100) || 'No messages'}
                          </Typography>
                        </Grid>
                        <Grid item>
                          <Chip 
                            label={`${conversation.messages?.length || 0} Messages`} 
                            size="small" 
                            color="secondary" 
                            variant="outlined"
                          />
                        </Grid>
                      </Grid>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Collapse>
          {/* Main content area */}
          <Box sx={{ flex: 1, overflow: 'auto' }}>
            {/* Existing component content */}
            <Box sx={{ 
              height: '70vh', 
              width: '100%', 
              display: 'flex', 
              flexDirection: 'column'
            }}>
              <Container 
                sx={{ 
                  flex: 1,
                  display: 'flex', 
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minHeight: '60vh',
                  textAlign: 'center',
                  gap: 3,
                  bgcolor: 'background.paper'
                }}
              >
                <Typography variant="h4" component="h1" gutterBottom>
                  Welcome to Your AI Pronunciation Coach
                </Typography>
                
                <Typography variant="body1" gutterBottom>
                  Select your target language, accent, topic, and then start practicing your conversation skills!
                </Typography>

                <Box sx={{ minWidth: 200, display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Language</InputLabel>
                    <Select
                      value={selectedLanguage}
                      onChange={handleLanguageChange}
                      label="Language"
                    >
                      {languages.map((lang) => (
                        <MenuItem key={lang.code} value={lang.code}>
                          {lang.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Accent</InputLabel>
                    <Select
                      value={selectedAccent}
                      onChange={handleAccentChange}
                      label="Accent"
                    >
                      {languages
                        .find((l) => l.code === selectedLanguage)
                        ?.accents.map((accent) => (
                          <MenuItem key={accent.code} value={accent.code}>
                            {accent.name}
                          </MenuItem>
                        ))}
                    </Select>
                  </FormControl>

                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Voice Gender</InputLabel>
                    <Select
                      value={selectedVoiceGender}
                      onChange={handleVoiceGenderChange}
                      label="Voice Gender"
                    >
                      <MenuItem value="male">Male</MenuItem>
                      <MenuItem value="female">Female</MenuItem>
                      <MenuItem value="kid">Kid</MenuItem>
                    </Select>
                  </FormControl>

                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Topic</InputLabel>
                    <Select
                      value={selectedTopic || 'random'}
                      onChange={handleTopicChange}
                      label="Topic"
                    >
                      <MenuItem value="random">Random Topic</MenuItem>
                      {topicOptions.map((topic) => (
                        <MenuItem key={topic} value={topic}>
                          {getTopicDisplayName(topic)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <Button
                    variant="contained"
                    color="primary"
                    size="large"
                    startIcon={<ChatIcon />}
                    onClick={handleStartConversation}
                    disabled={isProcessing}
                  >
                    {isProcessing ? (
                      <>
                        <CircularProgress size={24} color="inherit" sx={{ mr: 1 }} />
                        Starting Conversation...
                      </>
                    ) : (
                      "Let's Start Chatting and Improve Your Pronunciation"
                    )}
                  </Button>
                </Box>
              </Container>
            </Box>
          </Box>
        </Box>
      </Box>
    );
  }

  const handleToggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const startRecording = async () => {
    try {
      // Set state first to show visual feedback
      setIsRecording(true);
      setError(null);
      
      // Pause any playing audio
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
        setIsPlaying(false);
      }
      
      // Always get a fresh stream
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
      }
      
      // Get the stream first
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,         // Mono
          sampleRate: 16000,       // 16kHz
          sampleSize: 16,          // 16-bit
          echoCancellation: true,  // Reduce echo
          noiseSuppression: true,  // Reduce background noise
          autoGainControl: true    // Normalize volume
        }
      });
      audioStreamRef.current = stream;

      // Small delay to ensure stream is fully initialized
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Check supported MIME types
      let mimeType = 'audio/webm';
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      }
      
      // Create media recorder with timeslice to get data frequently
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 16000 * 16
      });
      
      // Store audio chunks
      audioChunksRef.current = [];
      
      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Add start event handler to ensure we're recording
      mediaRecorder.onstart = () => {
        console.log('Recording started successfully');
        // Request data immediately after start
        mediaRecorder.requestData();
      };
      
      // Start recording with timeslice to get data more frequently
      mediaRecorder.start(10); // Get data every 10ms
      mediaRecorderRef.current = mediaRecorder;
      
    } catch (error) {
      console.error('Error starting recording:', error);
      setError('Failed to start recording. Please check your microphone permissions.');
      setIsRecording(false);
      
      // Clean up any existing stream
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
        audioStreamRef.current = null;
      }
    }
  };
  
  const stopRecording = async () => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') return;

    try {
      setIsProcessing(true);
      setIsMessageLoading(true); 
      setIsRecording(false); 
      
      const mediaRecorder = mediaRecorderRef.current;

      // Request final data chunk before stopping
      mediaRecorder.requestData();
      
      // Create a promise for the audio blob
      const audioPromise = new Promise<Blob>((resolve) => {
        mediaRecorder.onstop = () => {
          const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          audioChunksRef.current = [];
          resolve(blob);
        };
      });

      // Stop recording after a short delay
      setTimeout(() => {
        mediaRecorder.stop();
        // Stop all tracks in the stream
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
      }, 100);

      // Wait for the audio data and process it
      const audioBlob = await audioPromise;
      await processRecording(audioBlob);

    } catch (error) {
      console.error('Error stopping recording:', error);
      setError('Failed to stop recording. Please try again.');
      // Remove any temporary messages
      setMessages(prev => prev.filter(msg => !msg.isLoading));
    } finally {
      setIsProcessing(false);
      setIsMessageLoading(false);
      setIsRecording(false); 
      
      // Ensure all tracks are stopped in case of error
      if (mediaRecorderRef.current?.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      }
    }
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%', 
      width: '100%' 
    }}>
      {/* Error Snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>

      {/* Language and Settings */}
      {/* <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider', bgcolor: 'background.paper', boxShadow: 1, zIndex: 1 }}>
        <Typography variant="h6" component="h1" sx={{ fontWeight: 600, color: 'primary.main' }}>
          AI Language Coach
        </Typography>
      </Box> */}

      {/* Chat Container */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          position: 'relative',
          backgroundImage: !hasStarted ? 'none' : getCurrentBackground(),
          backgroundRepeat: 'no-repeat',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          transition: 'all 0.5s ease-in-out',
          bgcolor: !hasStarted ? 'background.paper' : 'transparent',
          '&::before': !hasStarted ? {} : {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: theme => theme.palette.mode === 'light' ? 'rgba(255, 255, 255, 0.85)' : 'rgba(0, 0, 0, 0.85)',
            zIndex: 1
          },
          '& > *': {
            position: 'relative',
            zIndex: 2
          }
        }}
      >
        {/* Messages Container */}
        <Box
          ref={messagesEndRef}
          sx={{
            flex: 1,
            overflowY: 'auto',
            p: 3,
            position: 'relative',
            zIndex: 2,
            height: 'calc(100vh - 200px)', 
            maxHeight: 'calc(100vh - 200px)',
            display: 'flex',
            flexDirection: 'column',
            paddingBottom: '100px' 
          }}
        >
          <Box sx={{ 
            flex: 1, 
            display: 'flex', 
            flexDirection: 'column', 
            justifyContent: 'flex-end' 
          }}>
            {messages.map((message, index) => renderMessage(message, index))}
          </Box>
          <div 
            id="scroll-anchor" 
            style={{ 
              float: 'left', 
              clear: 'both', 
              height: '1px' 
            }} 
          />
        </Box>

        {/* Recording Controls */}
        <Box
          sx={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            zIndex: 1000,
            p: 2,
            borderTop: '1px solid',
            borderColor: 'divider',
            bgcolor: 'background.paper',
            boxShadow: '0 -2px 10px rgba(0,0,0,0.05)',
            width: '100%',
            maxWidth: 'md',
            margin: '0 auto'
          }}
        >
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <IconButton
              color={isRecording ? 'error' : 'primary'}
              onClick={handleToggleRecording}
              disabled={isProcessing}
              sx={{
                width: 56,
                height: 56,
                border: 2,
                borderColor: isRecording ? 'error.main' : 'primary.main',
                '&:hover': {
                  bgcolor: isRecording ? 'error.light' : 'primary.light',
                  '& .MuiSvgIcon-root': {
                    color: 'white',
                  },
                },
                animation: isRecording ? 'pulse 1.5s infinite' : 'none',
                '@keyframes pulse': {
                  '0%': {
                    boxShadow: '0 0 0 0 rgba(25, 118, 210, 0.4)',
                  },
                  '70%': {
                    boxShadow: '0 0 0 10px rgba(25, 118, 210, 0)',
                  },
                  '100%': {
                    boxShadow: '0 0 0 0 rgba(25, 118, 210, 0)',
                  },
                },
              }}
            >
              <MicIcon sx={{ fontSize: 28 }} />
            </IconButton>
            <Box sx={{ flex: 1 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                {isRecording ? 'Recording...' : 'Click the microphone to start speaking'}
              </Typography>
              <LinearProgress
                variant={isRecording ? 'indeterminate' : 'determinate'}
                value={0}
                sx={{
                  height: 4,
                  borderRadius: 2,
                  visibility: isRecording ? 'visible' : 'hidden',
                }}
              />
            </Box>
          </Box>
        </Box>

        {/* Hidden audio player */}
        <audio 
          ref={audioPlayerRef} 
          style={{ display: 'none' }}
          onEnded={() => setIsPlaying(false)}
          onError={() => {
            setIsPlaying(false);
            setError('Failed to play audio. Please try again.');
          }}
        />

        {/* Pronunciation Guidance Modal */}
        <Dialog
          open={pronunciationGuidanceModal.open}
          onClose={() => {
            setPronunciationGuidanceModal(prev => ({ ...prev, open: false }));
            setModalAudioBlob(null); 
            if (modalRecording) {
              stopModalRecording();
            }
          }}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SchoolIcon color="primary" />
              <Typography variant="h6">Let's Practice Your Pronunciation</Typography>
            </Box>
          </DialogTitle>
          <DialogContent>
            {/* Introduction */}
            <Box sx={{ mb: 3, p: 2, bgcolor: 'primary.light', borderRadius: 1, color: 'white' }}>
              <Typography variant="body1" sx={{ mb: 1 }}>
                Follow these steps to improve your pronunciation:
              </Typography>
              <Typography variant="body2" component="div">
                1. Listen to the correct pronunciation by clicking the speaker icon
                <br />
                2. Practice saying the word slowly, focusing on each sound
                <br />
                3. Record yourself using the practice section below
                <br />
                4. Compare your recording with the AI voice and keep practicing!
              </Typography>
            </Box>

            {/* Words to Practice Section with integrated practice controls */}
            {pronunciationGuidanceModal.poorWords.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" color="primary" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <MusicNoteIcon />
                  Words to Practice
                </Typography>
                
                <Grid container spacing={2}>
                  {pronunciationGuidanceModal.poorWords.map((word, index) => (
                    <Grid item xs={12} key={index}>
                      <Paper 
                        elevation={2}
                        sx={{ 
                          p: 2,
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 1,
                          bgcolor: 'background.paper',
                          borderLeft: 3,
                          borderColor: typeof word.accuracy === 'number' 
                            ? (word.accuracy >= 80 
                              ? 'success.main'
                              : (word.accuracy < 60 
                                ? 'error.main'
                                : 'warning.main'))
                          : 'warning.main'
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="h6" color="text.primary">{word.word}</Typography>
                          <Box
                            sx={{
                              px: 1.5,
                              py: 0.5,
                              borderRadius: 1,
                              bgcolor: typeof word.accuracy === 'number' 
                                ? getScoreColor(word.accuracy)
                                : 'warning.main',
                              color: 'white',
                              fontWeight: 600
                            }}
                          >
                            {typeof word.accuracy === 'number' ? `${word.accuracy.toFixed(0)}%` : 'N/A'}
                          </Box>
                        </Box>

                        {/* Word Practice Controls */}
                        <Grid container spacing={2}>
                          <Grid item xs={12} md={6}>
                            <Button
                              startIcon={<VolumeUpIcon />}
                              variant="contained"
                              onClick={() => speakAIText(word.word)}
                              fullWidth
                            >
                              Listen to AI
                            </Button>
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Button
                              variant="contained"
                              color="primary"
                              onClick={() => handleRecordWord(word.word)}
                              startIcon={pronunciationRecording && currentPronunciationWord === word.word ? <StopIcon /> : <MicIcon />}
                              sx={{
                                transition: 'all 0.2s ease-in-out',
                                position: 'relative',
                                overflow: 'hidden',
                                '&:hover': {
                                  bgcolor: pronunciationRecording && currentPronunciationWord === word.word ? 'error.dark' : 'primary.dark',
                                },
                                '&::after': pronunciationRecording && currentPronunciationWord === word.word ? {
                                  content: '""',
                                  position: 'absolute',
                                  top: 0,
                                  left: 0,
                                  right: 0,
                                  bottom: 0,
                                  background: 'rgba(255, 255, 255, 0.1)',
                                  animation: 'pulse 1.5s ease-in-out infinite'
                                } : {}
                              }}
                              fullWidth
                            >
                              {pronunciationRecording && currentPronunciationWord === word.word ? (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  Stop Recording
                                </Box>
                              ) : (
                                'Record'
                              )}
                            </Button>
                          </Grid>
                           
                        </Grid>

                        {recordedAudioBlobs[word.word] ? (
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={<PlayArrowIcon />}
                            onClick={() => playRecordedAudio(word.word)}
                            sx={{ mt: 1 }}
                          >
                            Listen to Recording
                          </Button>
                        ) : null}
                        
                      

                        {pronunciationRecording && currentPronunciationWord === word.word && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'error.main' }}>
                            <CircularProgress size={16} color="error" />
                            <Typography variant="body2" color="error">Recording in progress...</Typography>
                          </Box>
                        )}


                        {wordError && word.word === currentPronunciationWord && (
                          <Box sx={{ 
                            mt: 1,
                            p: 1.5,
                            borderRadius: 1,
                            bgcolor: 'error.50',
                            borderLeft: 3,
                            borderColor: 'error.main',
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: 1
                          }}>
                            <ErrorOutlineIcon color="error" sx={{ mt: 0.2 }} />
                            <Typography variant="body2" color="error.main">
                              {wordError}
                            </Typography>
                          </Box>
                        )}

                        {!pronunciationRecording && !wordError && word.transcribed_text && (
                          <Box sx={{ 
                            mt: 1,
                            p: 1.5,
                            borderRadius: 1,
                            bgcolor: 'info.50',
                            borderLeft: 3,
                            borderColor: 'info.main',
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: 1
                          }}>
                            <InfoIcon color="info" sx={{ mt: 0.2 }} />
                            <Typography variant="body2" color="info.main">
                              You said: "{word.transcribed_text}"
                            </Typography>
                          </Box>
                        )}
                      </Paper>
                    </Grid>
                    ))}
                  </Grid>
                </Box>
              )}
              {/* Detailed Guidance */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" color="primary" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TipsAndUpdatesIcon />
                  Pronunciation Tips
                </Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                    {pronunciationGuidanceModal.guidance}
                  </Typography>
                </Paper>
              </Box>

              {/* Hidden audio player for modal recording playback */}
              <audio 
                ref={modalAudioPlayerRef} 
                style={{ display: 'none' }}
                onEnded={() => {
                  if (modalAudioPlayerRef.current) {
                    URL.revokeObjectURL(modalAudioPlayerRef.current.src);
                  }
                }}
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={() => {
                setPronunciationGuidanceModal(prev => ({ ...prev, open: false }));
                setModalAudioBlob(null);
                if (modalRecording) {
                  stopModalRecording();
                }
              }} color="primary">
                Close
              </Button>
            </DialogActions>
          </Dialog>

          {/* Modal Recording */}
          <Dialog
            open={modalRecording}
            onClose={() => setModalRecording(false)}
            maxWidth="md"
            fullWidth
          >
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SchoolIcon color="primary" />
                <Typography variant="h6">Record Your Pronunciation</Typography>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', py: 2 }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={stopModalRecording}
                  startIcon={<StopIcon />}
                >
                  Stop Recording
                </Button>
              </Box>
            </DialogContent>
          </Dialog>

          {/* Hidden modal audio player */}
          <audio 
            ref={modalAudioPlayerRef} 
            style={{ display: 'none' }}
            onEnded={() => {
              console.log('Modal audio ended');
            }}
            onError={() => {
              console.error('Error playing modal audio');
            }}
          />
        
       
        {showDrawingCanvas && isKidsMode && (
          <DraggableDrawingCanvas 
            onClose={() => setShowDrawingCanvas(false)} 
            width={300}
            height={200}
          />
        )}
        {isKidsMode && !showDrawingCanvas && (
          <Tooltip title="Open Drawing Canvas" arrow>
            <IconButton
              onClick={() => setShowDrawingCanvas(true)}
              sx={{
                position: 'fixed',
                right: 20,
                top: 20,
                bgcolor: 'background.paper',
                boxShadow: 2,
                '&:hover': {
                  bgcolor: 'primary.light',
                  color: 'white'
                }
              }}
            >
              <CreateIcon />
            </IconButton>
          </Tooltip>
        )}
        {isKidsMode && (
          <Box sx={{ 
            position: 'fixed',
            right: 20,
            top: 80,
            zIndex: 1000,
            bgcolor: 'background.paper',
            borderRadius: 2,
            boxShadow: 3,
            p: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 1
          }}>
            <StarIcon sx={{ color: 'warning.main' }} />
            <Typography variant="h6" component="div" sx={{ color: 'text.primary' }}>
              Score: {score}
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Collapse 
        in={isPastConversationsOpen} 
        unmountOnExit 
        sx={{ 
          width: '100%', 
          position: 'relative',
          zIndex: 10,
          mt: 1  // Add margin top to position below the button
        }}
      >
        <Paper 
          elevation={4} 
          sx={{ 
            width: '100%', 
            backgroundColor: 'background.paper', 
            borderRadius: 2,
            p: 2
          }}
        >
          {/* Existing past conversations content */}
          <Stack 
            direction="row" 
            justifyContent="space-between" 
            alignItems="center" 
            sx={{ mb: 2 }}
          >
            <Typography variant="h6" fontWeight="bold">
              Past Conversations
            </Typography>
            <IconButton 
              onClick={() => setIsPastConversationsOpen(false)}
              size="small"
            >
              <CloseIcon />
            </IconButton>
          </Stack>

          <Grid container spacing={2}>
            {pastConversations.map((conversation) => (
              <Grid item xs={12} key={conversation.id}>
                <Paper 
                  elevation={2} 
                  sx={{ 
                    p: 2, 
                    cursor: 'pointer', 
                    transition: 'all 0.3s ease',
                    '&:hover': { 
                      backgroundColor: 'action.hover',
                      transform: 'scale(1.01)'
                    } 
                  }}
                  onClick={() => {
                    console.log('Conversation Selected:', {
                      id: conversation.id,
                      topicName: conversation.topicName
                    });
                    handleSelectPastConversation(conversation.id);
                    setIsPastConversationsOpen(false);
                  }}
                >
                  <Grid container justifyContent="space-between" alignItems="center">
                    <Grid item xs={10}>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {conversation.topicName || 'Untitled Conversation'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {new Date(conversation.originalTimestamp).toLocaleString()}
                      </Typography>
                      <Typography 
                        variant="body2" 
                        color="text.secondary" 
                        sx={{ 
                          overflow: 'hidden', 
                          textOverflow: 'ellipsis', 
                          whiteSpace: 'nowrap' 
                        }}
                      >
                        {conversation.messages?.[0]?.text?.slice(0, 100) || 'No messages'}
                      </Typography>
                    </Grid>
                    <Grid item>
                      <Chip 
                        label={`${conversation.messages?.length || 0} Messages`} 
                        size="small" 
                        color="secondary" 
                        variant="outlined"
                      />
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Paper>
      </Collapse>
    </Box>
  );
};

export default ConversationalAICoach;
