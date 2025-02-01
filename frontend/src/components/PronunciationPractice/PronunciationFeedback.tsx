import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
  Paper,
  Button,
} from '@mui/material';
import {
  CheckCircleOutline as SuccessIcon,
  ErrorOutline as ErrorIcon,
  InfoOutlined as InfoIcon,
  SmartToy as RobotIcon,
} from '@mui/icons-material';

interface Word {
  word: string;
  accuracy: number;
  error_type: string;
  syllables: Array<{
    syllable: string;
    accuracy: number;
  }>;
  phonemes: Array<{
    phoneme: string;
    accuracy: number;
  }>;
}

interface PronunciationFeedbackProps {
  accuracy: number;
  pronunciation: number;
  completeness: number;
  fluency: number;
  words: Word[];
  phoneme_level_feedback: string[];
  general_feedback: string[];
  onRequestCoach?: () => void;
  isLoadingCoach?: boolean;
}

export const PronunciationFeedback: React.FC<PronunciationFeedbackProps> = ({
  accuracy,
  pronunciation,
  completeness,
  fluency,
  words,
  phoneme_level_feedback,
  general_feedback,
  onRequestCoach,
  isLoadingCoach = false,
}) => {
  const getFeedbackIcon = (text: string) => {
    if (text.toLowerCase().includes('excellent') || text.toLowerCase().includes('good')) {
      return <SuccessIcon color="success" />;
    }
    if (text.toLowerCase().includes('work on') || text.toLowerCase().includes('focus on')) {
      return <ErrorIcon color="error" />;
    }
    return <InfoIcon color="info" />;
  };

  const hasIssues = words.some(word => word.accuracy < 0.8);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Pronunciation Feedback
      </Typography>

      {/* Scores */}
      <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          Scores
        </Typography>
        <List dense>
          <ListItem>
            <ListItemText 
              primary={`Accuracy: ${Math.round(accuracy * 100)}%`}
              secondary="How accurately you pronounced the words"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary={`Pronunciation: ${Math.round(pronunciation * 100)}%`}
              secondary="Overall pronunciation quality"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary={`Fluency: ${Math.round(fluency * 100)}%`}
              secondary="How smoothly you spoke"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary={`Completeness: ${Math.round(completeness * 100)}%`}
              secondary="How well you pronounced all parts of words"
            />
          </ListItem>
        </List>
      </Paper>

      {/* Word Analysis */}
      <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          Word Analysis
        </Typography>
        <List dense>
          {words.map((word, index) => (
            <ListItem key={index}>
              <ListItemIcon>
                {word.accuracy >= 0.8 ? (
                  <SuccessIcon color="success" />
                ) : (
                  <ErrorIcon color="error" />
                )}
              </ListItemIcon>
              <ListItemText
                primary={`${word.word}: ${Math.round(word.accuracy * 100)}%`}
                secondary={word.error_type ? `Issue: ${word.error_type}` : undefined}
              />
            </ListItem>
          ))}
        </List>
      </Paper>

      {/* Phoneme-Level Feedback */}
      {phoneme_level_feedback.length > 0 && (
        <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Phoneme-Level Feedback
          </Typography>
          <List dense>
            {phoneme_level_feedback.map((feedback, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  {getFeedbackIcon(feedback)}
                </ListItemIcon>
                <ListItemText primary={feedback} />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {/* General Feedback */}
      {general_feedback.length > 0 && (
        <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            General Feedback
          </Typography>
          <List dense>
            {general_feedback.map((feedback, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  {getFeedbackIcon(feedback)}
                </ListItemIcon>
                <ListItemText primary={feedback} />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {/* AI Coach Button */}
      {hasIssues && onRequestCoach && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<RobotIcon />}
            onClick={onRequestCoach}
            disabled={isLoadingCoach}
            sx={{ minWidth: 250 }}
          >
            {isLoadingCoach ? 'Getting AI Coach Suggestions...' : 'Get Personalized Practice Exercises'}
          </Button>
        </Box>
      )}
    </Box>
  );
};
