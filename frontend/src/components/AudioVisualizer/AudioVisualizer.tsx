import React, { useEffect, useRef } from 'react';
import { Box } from '@mui/material';

interface AudioVisualizerProps {
  isRecording?: boolean;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({ isRecording = false }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);

  useEffect(() => {
    let audioContext: AudioContext | null = null;
    let mediaStream: MediaStream | null = null;

    const initializeAudio = async () => {
      try {
        if (isRecording) {
          // Create audio context and analyzer
          audioContext = new AudioContext();
          analyserRef.current = audioContext.createAnalyser();
          analyserRef.current.fftSize = 256;
          
          // Get microphone stream
          mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          const source = audioContext.createMediaStreamSource(mediaStream);
          source.connect(analyserRef.current);

          // Create data array for visualization
          const bufferLength = analyserRef.current.frequencyBinCount;
          dataArrayRef.current = new Uint8Array(bufferLength);

          // Start animation
          animate();
        } else {
          // Clean up when stopping recording
          if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
          }
          if (audioContext) {
            await audioContext.close();
          }
          if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
          }
          
          // Clear canvas
          const canvas = canvasRef.current;
          if (canvas) {
            const ctx = canvas.getContext('2d');
            if (ctx) {
              ctx.clearRect(0, 0, canvas.width, canvas.height);
            }
          }
        }
      } catch (error) {
        console.error('Error initializing audio:', error);
      }
    };

    const animate = () => {
      const canvas = canvasRef.current;
      if (!canvas || !analyserRef.current || !dataArrayRef.current) return;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const draw = () => {
        if (!analyserRef.current || !dataArrayRef.current) return;

        animationFrameRef.current = requestAnimationFrame(draw);

        analyserRef.current.getByteFrequencyData(dataArrayRef.current);

        ctx.fillStyle = 'rgb(200, 200, 200)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const barWidth = (canvas.width / dataArrayRef.current.length) * 2.5;
        let barHeight;
        let x = 0;

        for (let i = 0; i < dataArrayRef.current.length; i++) {
          barHeight = (dataArrayRef.current[i] / 255) * canvas.height;

          const hue = (i / dataArrayRef.current.length) * 360;
          ctx.fillStyle = `hsl(${hue}, 70%, 50%)`;
          ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

          x += barWidth + 1;
        }
      };

      draw();
    };

    initializeAudio();

    return () => {
      if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isRecording]);

  return (
    <Box sx={{ width: '100%', height: '120px', bgcolor: 'background.paper' }}>
      <canvas
        ref={canvasRef}
        width={800}
        height={120}
        style={{
          width: '100%',
          height: '100%',
          borderRadius: '8px',
        }}
      />
    </Box>
  );
};
