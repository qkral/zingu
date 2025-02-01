import { useState, useRef, useCallback } from 'react';
import api from '../config/api';

interface RecognitionResult {
  text: string;
  confidence?: number;
  transcribed_text?: string;
}

export const useAudioRecording = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    try {
      setIsRecording(true);
      
      // Get audio stream with specific constraints
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
      
      // Check supported MIME types
      let mimeType = 'audio/webm';
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      }
      
      // Create media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 16000 * 16  // 16kHz * 16-bit
      });
      
      // Store audio chunks
      audioChunksRef.current = [];
      
      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      // Start recording
      mediaRecorder.start(100); // Collect data every 100ms
      mediaRecorderRef.current = mediaRecorder;
      
    } catch (error) {
      console.error('Error starting recording:', error);
      setIsRecording(false);
      throw error;
    }
  }, []);

  const stopRecording = useCallback(async (): Promise<RecognitionResult | null> => {
    return new Promise((resolve, reject) => {
      if (!mediaRecorderRef.current) {
        setIsRecording(false);
        reject(new Error('No media recorder found'));
        return;
      }

      mediaRecorderRef.current.onstop = async () => {
        try {
          setIsProcessing(true);
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          
          // Create form data
          const formData = new FormData();
          formData.append('audio', audioBlob);
          formData.append('language', 'en');  // Default to English for the game
          formData.append('accent', 'neutral');  // Default accent
          
          // Send to backend
          const response = await api.post('/api/coach/transcribe', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });

          resolve({
            text: response.data.transcription,
            transcribed_text: response.data.transcription,
          });
        } catch (error) {
          console.error('Error processing audio:', error);
          reject(error);
        } finally {
          setIsProcessing(false);
        }
      };

      // Stop the media recorder
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    });
  }, []);

  return {
    isRecording,
    isProcessing,
    startRecording,
    stopRecording,
  };
};
