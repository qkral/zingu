import React from 'react';
import {
  Box,
  Paper,
  Typography,
  useTheme,
  Tooltip,
} from '@mui/material';

interface Word {
  word: string;
  accuracy_score: number;
  error_type: string | null;
  phonemes: Array<{
    phoneme: string;
    score: number;
  }>;
  start_time: number;
  duration: number;
}

interface WordTimelineProps {
  words: Word[];
}

export const WordTimeline: React.FC<WordTimelineProps> = ({ words }) => {
  const theme = useTheme();

  const getScoreColor = (score: number): string => {
    if (score >= 80) return theme.palette.success.light;
    if (score >= 60) return theme.palette.warning.light;
    return theme.palette.error.light;
  };

  const totalDuration = words.reduce((sum, word) => 
    Math.max(sum, word.start_time + word.duration), 0);

  return (
    <Box sx={{ width: '100%', overflowX: 'auto' }}>
      <Box sx={{ position: 'relative', height: 100, minWidth: 600 }}>
        {/* Time markers */}
        {Array.from({ length: Math.ceil(totalDuration / 1000) + 1 }).map((_, i) => (
          <Box
            key={i}
            sx={{
              position: 'absolute',
              left: `${(i * 1000 * 100) / totalDuration}%`,
              top: 0,
              height: '100%',
              borderLeft: '1px solid',
              borderColor: 'divider',
            }}
          >
            <Typography variant="caption" sx={{ ml: 0.5 }}>
              {i}s
            </Typography>
          </Box>
        ))}

        {/* Words */}
        {words.map((word, index) => {
          const left = (word.start_time * 100) / totalDuration;
          const width = (word.duration * 100) / totalDuration;

          return (
            <Tooltip
              key={index}
              title={
                <Box>
                  <Typography variant="body2">
                    Score: {Math.round(word.accuracy_score)}%
                  </Typography>
                  {word.error_type && (
                    <Typography variant="body2">
                      Error: {word.error_type}
                    </Typography>
                  )}
                  <Typography variant="body2">
                    Phonemes: {word.phonemes.map(p => p.phoneme).join(' ')}
                  </Typography>
                </Box>
              }
            >
              <Paper
                elevation={2}
                sx={{
                  position: 'absolute',
                  left: `${left}%`,
                  width: `${width}%`,
                  top: '30%',
                  height: '40%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: getScoreColor(word.accuracy_score),
                  cursor: 'pointer',
                  transition: 'transform 0.2s',
                  '&:hover': {
                    transform: 'scale(1.05)',
                  },
                }}
              >
                <Typography
                  variant="caption"
                  noWrap
                  sx={{
                    px: 0.5,
                    color: theme.palette.getContrastText(
                      getScoreColor(word.accuracy_score)
                    ),
                  }}
                >
                  {word.word}
                </Typography>
              </Paper>
            </Tooltip>
          );
        })}
      </Box>
    </Box>
  );
};
