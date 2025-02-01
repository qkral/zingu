import React, { useState, useCallback } from 'react';
import { Box, Container } from '@mui/material';
import WordDetectiveGame from '../components/KidsMode/WordDetectiveGame';
import KidsModeToggle from '../components/KidsMode/KidsModeToggle';
import { useAudioRecording } from '../hooks/useAudioRecording';

interface RecognitionResult {
  text: string;
}

const WordDetectivePage: React.FC = () => {
  const [isKidsMode, setIsKidsMode] = useState(true);
  const { 
    isRecording, 
    startRecording, 
    stopRecording 
  } = useAudioRecording();
  const [lastTranscription, setLastTranscription] = useState<string>('');
  const [isThinking, setIsThinking] = useState(false);

  const handleRecordingStart = useCallback(async () => {
    try {
      setLastTranscription(''); // Clear previous transcription
      await startRecording();
    } catch (error) {
      console.error('Error starting recording:', error);
      setIsThinking(false);
    }
  }, [startRecording]);

  const handleRecordingStop = useCallback(async () => {
    try {
      setIsThinking(true);
      const result = await stopRecording();
      if (result?.text) {
        // Extract just the text from the response
        const transcribedText = typeof result.text === 'string' 
          ? result.text 
          : (result as RecognitionResult).text || '';
        
        setLastTranscription(transcribedText);
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
    } finally {
      setIsThinking(false);
    }
  }, [stopRecording]);

  const handleTranscription = useCallback((text: string) => {
    console.log('Transcribed text:', text);
  }, []);

  // Effect to handle new transcriptions
  React.useEffect(() => {
    if (lastTranscription) {
      handleTranscription(lastTranscription);
    }
  }, [lastTranscription, handleTranscription]);

  const handleGameReset = useCallback(() => {
    setLastTranscription(''); // Clear transcription when game resets
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'flex-end' }}>
        <KidsModeToggle 
          isKidsMode={isKidsMode} 
          onToggle={setIsKidsMode} 
        />
      </Box>
      
      <WordDetectiveGame
        onRecordingStart={handleRecordingStart}
        onRecordingStop={handleRecordingStop}
        onTranscription={handleTranscription}
        onGameReset={handleGameReset}
        isRecording={isRecording}
        isThinking={isThinking}
        transcribedText={lastTranscription}
        difficulty={isKidsMode ? "easy" : "hard"}
        isKidsMode={isKidsMode}
      />
    </Container>
  );
};

export default WordDetectivePage;
