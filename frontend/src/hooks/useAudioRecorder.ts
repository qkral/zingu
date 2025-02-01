import { useState, useRef, useCallback } from 'react';

export const useAudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const keepAliveIntervalRef = useRef<number | null>(null);

  const startRecording = useCallback(async () => {
    try {
      console.log('Starting recording setup...');
      
      // Get microphone stream with minimal processing
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false
        }
      });
      
      streamRef.current = stream;
      
      // Create MediaRecorder with specific options
      const options = {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 128000
      };
      
      mediaRecorderRef.current = new MediaRecorder(stream, options);
      chunksRef.current = [];
      
      // Handle data available event
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      // Start recording with very small timeslice to keep it active
      mediaRecorderRef.current.start(10);
      
      // Set up keep-alive interval
      keepAliveIntervalRef.current = window.setInterval(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.requestData();
        }
      }, 200);

      setIsRecording(true);
      console.log('Recording started');
      
    } catch (error) {
      console.error('Error starting recording:', error);
      await cleanup();
      throw error;
    }
  }, []);

  const cleanup = async () => {
    // Clear keep-alive interval
    if (keepAliveIntervalRef.current) {
      clearInterval(keepAliveIntervalRef.current);
      keepAliveIntervalRef.current = null;
    }

    // Stop media stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        track.stop();
      });
      streamRef.current = null;
    }
  };

  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
        cleanup();
        setIsRecording(false);
        resolve(null);
        return;
      }

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { 
          type: 'audio/webm;codecs=opus'
        });
        
        await cleanup();
        setIsRecording(false);
        resolve(audioBlob);
      };

      // Request final data and stop
      if (mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.requestData();
        mediaRecorderRef.current.stop();
      }
    });
  }, []);

  const cancelRecording = useCallback(async () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      await cleanup();
      setIsRecording(false);
    }
  }, []);

  return {
    startRecording,
    stopRecording,
    cancelRecording,
    isRecording,
    mediaRecorderRef
  };
};
