import {
  Box,
  Button,
  Typography,
  CircularProgress,
  Stack,
  Snackbar,
  Alert,
  AlertColor
} from '@mui/material';
import { Mic as MicIcon, Stop as StopIcon } from '@mui/icons-material';
import { useState } from 'react';
import { useAudioRecorder } from '../hooks/useAudioRecorder';

interface AccentResult {
  [key: string]: number;
}

const isValidProbability = (value: unknown): value is number => 
  typeof value === 'number' && !isNaN(value);

const AccentDetectionRecorder = () => {
  const [results, setResults] = useState<AccentResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<AlertColor>('error');
  const { startRecording, stopRecording, isRecording } = useAudioRecorder();

  const handleStartRecording = async () => {
    try {
      await startRecording();
    } catch (error) {
      setSnackbarMessage('Failed to start recording. Please check microphone permissions.');
      setSnackbarSeverity('warning');
      setOpenSnackbar(true);
    }
  };

  const handleStopRecording = async () => {
    try {
      const audioBlob = await stopRecording();
      if (audioBlob) {
        await sendAudioForAnalysis(audioBlob);
      }
    } catch (error) {
      setSnackbarMessage('Failed to stop recording.');
      setSnackbarSeverity('error');
      setOpenSnackbar(true);
    }
  };

  const sendAudioForAnalysis = async (audioBlob: Blob) => {
    setIsProcessing(true);
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

    try {
      const response = await fetch('http://localhost:8000/api/detect-accent', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to analyze accent');
      }

      const data = await response.json();
      setResults(data);
    } catch (error) {
      setSnackbarMessage(error instanceof Error ? error.message : 'Failed to analyze accent. Please try again.');
      setSnackbarSeverity('error');
      setOpenSnackbar(true);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCloseSnackbar = () => {
    setOpenSnackbar(false);
  };

  return (
    <Stack spacing={6} sx={{ width: '100%', maxWidth: '600px', margin: 'auto', padding: 4 }}>
      <Typography variant="h4">Accent Detection</Typography>
      
      <Button
        startIcon={isRecording ? <StopIcon /> : <MicIcon />}
        color="primary"
        onClick={isRecording ? handleStopRecording : handleStartRecording}
        disabled={isProcessing}
      >
        {isRecording ? 'Stop Recording' : 'Start Recording'}
      </Button>

      {isProcessing && (
        <Box sx={{ width: '100%' }}>
          <Typography mb={2}>Processing audio...</Typography>
          <CircularProgress size={24} />
        </Box>
      )}

      {results && (
        <Stack 
          sx={{ 
            width: '100%', 
            spacing: 4, 
            alignItems: 'stretch' 
          }}
        >
          <Typography variant="h6">Detected Accents</Typography>
          {Object.entries(results).map(([accent, probability]) => {
            if (!isValidProbability(probability)) {
              throw new Error(`Invalid probability value: ${probability}`);
            }
            return (
              <Box key={accent} sx={{ width: '100%' }}>
                <Typography>{accent}</Typography>
                <CircularProgress
                  variant="determinate"
                  value={probability * 100}
                  size={24}
                />
                <Typography textAlign="right">{probability.toFixed(1)}%</Typography>
              </Box>
            );
          })}
        </Stack>
      )}
      <Snackbar
        open={openSnackbar}
        autoHideDuration={5000}
        onClose={handleCloseSnackbar}
      >
        <Alert severity={snackbarSeverity}>{snackbarMessage}</Alert>
      </Snackbar>
    </Stack>
  );
};

export default AccentDetectionRecorder;
