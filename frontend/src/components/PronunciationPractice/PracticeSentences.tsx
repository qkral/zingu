import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
  Paper,
} from '@mui/material';

interface PracticeSentencesProps {
  sentences: string[];
  selectedSentence: string;
  onSelectSentence: (sentence: string) => void;
}

export const PracticeSentences: React.FC<PracticeSentencesProps> = ({
  sentences,
  selectedSentence,
  onSelectSentence,
}) => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Practice Sentences
      </Typography>
      <Paper variant="outlined">
        <List>
          {sentences.map((sentence, index) => (
            <ListItem key={index} disablePadding>
              <ListItemButton
                selected={sentence === selectedSentence}
                onClick={() => onSelectSentence(sentence)}
              >
                <ListItemText
                  primary={sentence}
                  primaryTypographyProps={{
                    style: {
                      fontWeight: sentence === selectedSentence ? 600 : 400,
                    },
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  );
};
