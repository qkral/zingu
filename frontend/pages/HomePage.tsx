import { Container, Typography, Box, Button, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import { useAuth } from '../contexts/AuthContext';

export default function HomePage() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Box sx={{ textAlign: 'center' }}>
        <RecordVoiceOverIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
        <Typography variant="h2" component="h1" gutterBottom>
          Welcome to Accent Improver
        </Typography>
        <Typography variant="h5" color="text.secondary" paragraph>
          Enhance your pronunciation through interactive games and AI-powered coaching.
        </Typography>
        
        {!currentUser ? (
          <Stack
            direction="row"
            spacing={2}
            justifyContent="center"
            sx={{ mt: 4 }}
          >
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/create-account')}
            >
              Create Account
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/sign-in')}
            >
              Sign In
            </Button>
            <Button
              variant="text"
              size="large"
              onClick={() => navigate('/coach')}
            >
              Try Demo
            </Button>
          </Stack>
        ) : (
          <Stack
            direction="row"
            spacing={2}
            justifyContent="center"
            sx={{ mt: 4 }}
          >
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/coach')}
            >
              Start Practicing
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/games')}
            >
              Play Games
            </Button>
          </Stack>
        )}
      </Box>
    </Container>
  );
}
