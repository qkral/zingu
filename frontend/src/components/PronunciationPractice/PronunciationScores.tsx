import React from 'react';
import {
  Box,
  Grid,
  Typography,
  CircularProgress,
  useTheme,
} from '@mui/material';

interface Score {
  value: number;
  label: string;
  color: string;
}

interface PronunciationScoresProps {
  scores: {
    accuracy: number;
    pronunciation: number;
    completeness: number;
    fluency: number;
  };
}

export const PronunciationScores: React.FC<PronunciationScoresProps> = ({ scores }) => {
  const theme = useTheme();

  const getScoreColor = (score: number): string => {
    if (score >= 80) return theme.palette.success.main;
    if (score >= 60) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const scoreItems: Score[] = [
    {
      value: scores.accuracy,
      label: 'Accuracy',
      color: getScoreColor(scores.accuracy),
    },
    {
      value: scores.pronunciation,
      label: 'Pronunciation',
      color: getScoreColor(scores.pronunciation),
    },
    {
      value: scores.completeness,
      label: 'Completeness',
      color: getScoreColor(scores.completeness),
    },
    {
      value: scores.fluency,
      label: 'Fluency',
      color: getScoreColor(scores.fluency),
    },
  ];

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Pronunciation Scores
      </Typography>
      <Grid container spacing={4} justifyContent="center">
        {scoreItems.map((score) => (
          <Grid item key={score.label} xs={6} sm={3}>
            <Box display="flex" flexDirection="column" alignItems="center">
              <Box position="relative" display="inline-flex">
                <CircularProgress
                  variant="determinate"
                  value={score.value}
                  size={80}
                  thickness={4}
                  sx={{ color: score.color }}
                />
                <Box
                  sx={{
                    top: 0,
                    left: 0,
                    bottom: 0,
                    right: 0,
                    position: 'absolute',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Typography
                    variant="body2"
                    component="div"
                    color="text.secondary"
                  >
                    {`${Math.round(score.value)}%`}
                  </Typography>
                </Box>
              </Box>
              <Typography
                variant="body1"
                color="text.secondary"
                align="center"
                sx={{ mt: 1 }}
              >
                {score.label}
              </Typography>
            </Box>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};
