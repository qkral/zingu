import React, { useState } from 'react';
import {
  Box,
  Button,
  Container,
  Typography,
  Card,
  LinearProgress,
  Stack,
} from '@mui/material';
import { Mic, Stop } from '@mui/icons-material';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { AudioVisualizer } from './AudioVisualizer';

interface AccentResult {
  accents: Record<string, number>;
  confidence: number;
}

const AccentDetection: React.FC = () => {
  const [results, setResults] = useState<AccentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const { isRecording, startRecording, stopRecording, mediaRecorderRef } = useAudioRecorder();

  const handleStartRecording = async () => {
    try {
      setError(null);
      setResults(null);
      await startRecording();
    } catch (error) {
      console.error('Error starting recording:', error);
      setError('Failed to start recording. Please make sure your microphone is connected and you have granted permission to use it.');
    }
  };

  const handleStopRecording = async () => {
    try {
      if (!mediaRecorderRef.current) return;

      const audioBlob = await stopRecording();
      if (!audioBlob) {
        console.log('No audio data available');
        return;
      }

      setIsProcessing(true);

      // Create form data
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.wav');

      // Send to backend
      const response = await fetch('http://localhost:8000/api/detect-accent', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to detect accent');
      }

      const data = await response.json();
      console.log('Received accent data:', data);
      
      // Convert percentage values to probabilities (0-1)
      const accents = Object.fromEntries(
        Object.entries(data).map(([accent, percentage]) => [
          accent,
          (percentage as number) / 100
        ])
      );

      setResults({
        accents,
        confidence: Object.values(accents).reduce((max, val) => Math.max(max, val), 0)
      });

    } catch (error) {
      console.error('Error processing recording:', error);
      setError('Failed to process recording');
    } finally {
      setIsProcessing(false);
    }
  };

  const renderResults = () => {
    if (!results || !results.accents) return null;

    return (
      <Card sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Results
        </Typography>
        
        <Stack spacing={2}>
          {Object.entries(results.accents).map(([accent, percentage]) => (
            <Box key={accent}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography>{accent}</Typography>
                <Typography>{(percentage * 100).toFixed(1)}%</Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={percentage * 100}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
          ))}
        </Stack>

        <Typography sx={{ mt: 2 }} color="text.secondary">
          Confidence: {(results.confidence * 100).toFixed(1)}%
        </Typography>
      </Card>
    );
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Accent Detection
        </Typography>
        
        <Typography variant="subtitle1" gutterBottom align="center" color="text.secondary">
          Record your voice to analyze your accent patterns
        </Typography>

        <Card sx={{ p: 3, mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
            <Button
              variant="contained"
              color={isRecording ? "error" : "primary"}
              onClick={isRecording ? handleStopRecording : handleStartRecording}
              startIcon={isRecording ? <Stop /> : <Mic />}
              disabled={isProcessing}
              size="large"
            >
              {isRecording ? "Stop Recording" : "Start Recording"}
            </Button>
          </Box>

          {isRecording && (
            <Box sx={{ mb: 2 }}>
              <AudioVisualizer />
            </Box>
          )}

          {error && (
            <Typography color="error" sx={{ mb: 2 }} align="center">
              {error}
            </Typography>
          )}

          {isProcessing && (
            <Box sx={{ width: '100%', mb: 2 }}>
              <LinearProgress />
            </Box>
          )}
        </Card>

        {renderResults()}
      </Box>
    </Container>
  );
};

export default AccentDetection;
