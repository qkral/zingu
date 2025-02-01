import React from 'react';
import ConversationalAICoach from '../AICoach/ConversationalAICoach';
import { Box, Paper } from '@mui/material';
import { styled } from '@mui/material/styles';

const KidsContainer = styled(Paper)(({ theme }) => ({
  background: 'linear-gradient(135deg, #FFE5E5 0%, #E5F3FF 50%, #E5FFE5 100%)',
  padding: theme.spacing(3),
  borderRadius: '20px',
  border: '3px solid #FFB6C1',
  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
  '& .MuiButton-root': {
    background: 'linear-gradient(45deg, #FF69B4 30%, #87CEEB 90%)',
    borderRadius: '25px',
    border: '2px solid #FFF',
    color: 'white',
    fontWeight: 'bold',
    '&:hover': {
      background: 'linear-gradient(45deg, #FF1493 30%, #4169E1 90%)',
    }
  },
  '& .MuiTypography-root': {
    color: '#4A4A4A',
    '&.MuiTypography-h4, &.MuiTypography-h5': {
      color: '#FF69B4',
      fontWeight: 'bold',
      textShadow: '2px 2px 4px rgba(0,0,0,0.1)',
    }
  },
  '& .MuiPaper-root': {
    background: 'rgba(255, 255, 255, 0.9)',
    borderRadius: '15px',
    border: '2px solid #87CEEB',
  },
  '& .MuiChip-root': {
    background: 'linear-gradient(45deg, #FFB6C1 30%, #ADD8E6 90%)',
    border: '1px solid #FFF',
    '& .MuiChip-label': {
      color: '#4A4A4A',
      fontWeight: 'bold',
    }
  },
  '& .MuiIconButton-root': {
    color: '#FF69B4',
    '&:hover': {
      color: '#4169E1',
    }
  }
}));

const KidsAICoach: React.FC = () => {
  return (
    <KidsContainer>
      <Box sx={{ position: 'relative' }}>
        <ConversationalAICoach />
      </Box>
    </KidsContainer>
  );
};

export default KidsAICoach;
