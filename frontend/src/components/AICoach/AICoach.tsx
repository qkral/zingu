import React, { useState } from 'react';
import { Box, Typography, ToggleButtonGroup, ToggleButton } from '@mui/material';
import ConversationalAICoach from './ConversationalAICoach';
import ChildCareIcon from '@mui/icons-material/ChildCare';
import PersonIcon from '@mui/icons-material/Person';

export const AICoach = () => {
  const [mode, setMode] = useState<'adult' | 'kids'>('adult');
  const [hasStarted, setHasStarted] = useState(false);

  const handleModeChange = (
    _event: React.MouseEvent<HTMLElement>,
    newMode: 'adult' | 'kids' | null,
  ) => {
    if (newMode !== null) {
      setMode(newMode);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      {!hasStarted && (
        <>
          <Typography variant="h4" gutterBottom align="center">
            AI Language Coach
          </Typography>
          <Typography variant="subtitle1" gutterBottom align="center" color="text.secondary" mb={2}>
            Have a natural conversation with your AI coach while improving your pronunciation
          </Typography>
          
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
            <ToggleButtonGroup
              value={mode}
              exclusive
              onChange={handleModeChange}
              aria-label="mode selection"
            >
              <ToggleButton value="adult" aria-label="adult mode">
                <PersonIcon sx={{ mr: 1 }} />
                Adult Mode
              </ToggleButton>
              <ToggleButton value="kids" aria-label="kids mode">
                <ChildCareIcon sx={{ mr: 1 }} />
                Kids Mode
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </>
      )}
      
      <ConversationalAICoach isKidsMode={mode === 'kids'} onStart={() => setHasStarted(true)} />
    </Box>
  );
};
