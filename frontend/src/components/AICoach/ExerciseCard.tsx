import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Rating,
} from '@mui/material';

interface Exercise {
  title: string;
  description: string;
  example_words: string[];
  difficulty: number;
}

interface ExerciseCardProps {
  exercise: Exercise;
}

export const ExerciseCard: React.FC<ExerciseCardProps> = ({ exercise }) => {
  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" component="div">
            {exercise.title}
          </Typography>
          <Rating
            value={exercise.difficulty}
            readOnly
            max={5}
            size="small"
          />
        </Box>

        <Typography variant="body1" sx={{ mb: 2 }}>
          {exercise.description}
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {exercise.example_words.map((word, index) => (
            <Chip
              key={index}
              label={word}
              color="primary"
              variant="outlined"
              size="small"
            />
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};
