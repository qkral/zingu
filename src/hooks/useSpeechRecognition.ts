import { useState, useCallback, useEffect, useMemo } from 'react';

// Comprehensive type declaration for SpeechRecognition
interface SpeechRecognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxResults: number;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  [index: number]: {
    transcript: string;
    confidence: number;
  };
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

// Declare the webkitSpeechRecognition type
declare global {
  interface Window {
    webkitSpeechRecognition: {
      new (): SpeechRecognition;
      prototype: SpeechRecognition;
    }
  }
}


export const useSpeechRecognition = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [transcribedText, setTranscribedText] = useState('');

  // Create recognition instance only once
  const recognition = useMemo(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const instance = new (window as any).webkitSpeechRecognition() as SpeechRecognition;
      instance.lang = 'en-US';
      instance.maxResults = 10;
      instance.continuous = false;
      instance.interimResults = false;
      return instance;
    }
    return null;
  }, []);

  // Set up recognition handlers
  useEffect(() => {
    if (!recognition) return;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      console.log('Recognition result:', event.results);
      // Get the last result
      const lastResult = event.results[event.results.length - 1];
      
      // Only process if it's the final result
      if (lastResult.isFinal) {
        const transcript = lastResult[0].transcript;
        console.log('Got final transcript:', transcript);
        if (transcript && transcript.trim()) {
          console.log('Setting valid transcript');
          setTranscribedText(transcript);
        }
      }
      // Don't set NO_SPEECH_DETECTED here, let onend handle it
    };

    recognition.onend = () => {
      console.log('Recognition ended, current transcribedText:', transcribedText);
      setIsRecording(false);
      setIsThinking(false);
      
      // Only set NO_SPEECH_DETECTED if we haven't got any text
      setTimeout(() => {
        setTranscribedText(prev => {
          if (!prev || prev === '') {
            console.log('Setting NO_SPEECH_DETECTED from onend');
            return 'NO_SPEECH_DETECTED';
          }
          return prev;
        });
      }, 100); // Small delay to ensure final results are processed
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      setIsRecording(false);
      setIsThinking(false);
      if (event.error === 'no-speech' || event.error === 'audio-capture') {
        console.log('Setting NO_SPEECH_DETECTED from onerror');
        setTranscribedText('NO_SPEECH_DETECTED');
      }
    };

    return () => {
      recognition.onresult = null;
      recognition.onend = null;
      recognition.onerror = null;
    };
  }, [recognition]);

  const startRecording = useCallback(() => {
    if (!recognition) {
      console.error('Speech recognition not supported');
      return;
    }

    console.log('Starting recording...');
    setIsRecording(true);
    setIsThinking(false);
    // Don't set transcribed text to empty when starting
    // setTranscribedText('');

    try {
      recognition.start();
    } catch (error) {
      console.error('Failed to start recording:', error);
      setIsRecording(false);
      console.log('Setting NO_SPEECH_DETECTED from start error');
      setTranscribedText('NO_SPEECH_DETECTED');
    }
  }, [recognition]);

  const stopRecording = useCallback(() => {
    if (!recognition) return;
    
    console.log('Stopping recording...');
    recognition.stop();
    setIsRecording(false);
  }, [recognition]);

  // Clean up recognition on unmount
  useEffect(() => {
    return () => {
      if (recognition) {
        try {
          recognition.stop();
        } catch (error) {
          // Ignore errors during cleanup
        }
      }
    };
  }, [recognition]);

  return {
    isRecording,
    isThinking,
    transcribedText,
    startRecording,
    stopRecording
  };
};
