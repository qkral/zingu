import { Container, Typography, Box, Button, Stack, Grid, Paper, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import GitHubIcon from '@mui/icons-material/GitHub';
import CodeIcon from '@mui/icons-material/Code';
import GroupAddIcon from '@mui/icons-material/GroupAdd';
import { useAuth } from '../contexts/AuthContext';

export default function HomePage() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  return (
    <Container maxWidth="lg" sx={{ 
      py: { xs: 2, md: 4 },  
      mt: { xs: 0, md: -2 },  
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center' 
    }}>
      <Grid container spacing={{ xs: 2, md: 4 }} 
        direction={{ xs: 'column-reverse', md: 'row' }}  
        alignItems="center"
      >
        <Grid item xs={12} md={6}>
          <Box sx={{ 
            textAlign: 'center',  
            pr: { xs: 0, md: 4 },  
            maxWidth: { xs: '100%', md: 'auto' },
            margin: { xs: '0 auto', md: 'inherit' }
          }}>
            <RecordVoiceOverIcon sx={{ 
              fontSize: { xs: 60, md: 80 },  
              mb: 2,  
              color: 'primary.main',
              display: { xs: 'block', md: 'block' },
              margin: { xs: '0 auto', md: 'inherit' }  
            }} />
            <Typography 
              variant="h3"  
              component="h1" 
              gutterBottom 
              sx={{ 
                fontWeight: 'bold', 
                color: 'text.primary',
                fontSize: { xs: '2rem', md: '3rem' }  
              }}
            >
              Zingu: Learn Languages by Talking
            </Typography>
            <Typography 
              variant="h6"  
              component="p" 
              gutterBottom 
              sx={{ 
                color: 'text.secondary', 
                mb: 3,
                fontSize: { xs: '1rem', md: '1.25rem' }  
              }}
            >
              Learn, practice, and master your accent through personalized games and feedback.
            </Typography>

{/* Try Demo Button */}
<Box 
              sx={{ 
                display: 'flex', 
                justifyContent: 'center',  
                mb: 2 
              }}
            >
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={() => navigate('/coach')}
                sx={{ 
                  minWidth: 250, 
                  py: 1.5, 
                  fontSize: '1.1rem', 
                  fontWeight: 'bold',
                  borderRadius: 2,
                  boxShadow: 3,
                  '&:hover': {
                    transform: 'scale(1.05)',
                    transition: 'transform 0.3s ease-in-out'
                  }
                }}
              >
                Try Demo
              </Button>
            </Box>
            <Alert 
              icon={<CodeIcon />} 
              severity="info" 
              sx={{ 
                mb: 3, 
                maxWidth: 600,
                '& .MuiAlert-message': { 
                  width: '100%' 
                }
              }}
            >
              <Typography variant="body1">
                Unlock your language potential with Zingu's AI-powered accent coaching! Our innovative platform uses advanced machine learning to provide personalized pronunciation feedback, interactive language games, and real-time speech analysis. Whether you're preparing for an international presentation, learning a new language, or simply want to sound more confident, we're here to help you communicate clearly and effectively.
              </Typography>
            </Alert>

            <Stack 
              direction={{ xs: 'column', sm: 'row' }} 
              spacing={2} 
              sx={{ 
                mt: 2, 
                justifyContent: 'center',  
                alignItems: 'center',
                width: '100%'
              }}
            >
              {!currentUser && (
                <>
                  <Button
                    variant="outlined"
                    size="large"
                    onClick={() => navigate('/create-account')}
                    sx={{ 
                      minWidth: { xs: '100%', sm: 200 },  
                      mb: { xs: 2, sm: 0 }  
                    }}
                  >
                    Sign Up
                  </Button>
                  <Button
                    variant="outlined"
                    size="large"
                    onClick={() => navigate('/sign-in')}
                    sx={{ 
                      minWidth: { xs: '100%', sm: 200 }  
                    }}
                  >
                    Log In
                  </Button>
                </>
              )}
            </Stack>

            <Box sx={{ display: 'flex', justifyContent: 'center' }}>
              {currentUser && (
                <Stack 
                  direction={{ xs: 'column', sm: 'row' }} 
                  spacing={2} 
                  sx={{ 
                    mt: 2, 
                    justifyContent: 'center',  
                    alignItems: 'center',
                    width: '100%'
                  }}
                >
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => navigate('/dashboard')}
                    sx={{ 
                      minWidth: { xs: '100%', sm: 200 },  
                      mb: { xs: 2, sm: 0 }  
                    }}
                  >
                    Go to Dashboard
                  </Button>
                  <Button
                    variant="outlined"
                    color="primary"
                    onClick={() => navigate('/games')}
                    sx={{ 
                      minWidth: { xs: '100%', sm: 200 }  
                    }}
                  >
                    Explore Games
                  </Button>
                </Stack>
              )}
            </Box>

            

            {/* Open Source Section */}
            <Paper 
              elevation={2} 
              sx={{ 
                p: 3, 
                mt: 2, 
                backgroundColor: 'background.default',
                borderRadius: 2,
                textAlign: 'center'  
              }}
            >
              <Typography variant="h6" gutterBottom>
                We're an Open-Source Project! 🌍
              </Typography>
              <Typography variant="body1" paragraph>
                Zingu is an open-source language learning platform that empowers developers and language enthusiasts to contribute to innovative AI coaching tools. Help us improve features, create new learning experiences, or translate the platform to make language learning accessible worldwide.
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <Button
                  variant="text"
                  startIcon={<GitHubIcon />}
                  href="https://github.com/qkral/zingu"
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ mr: 2 }}
                >
                  View on GitHub
                </Button>
                <Button
                  variant="text"
                  startIcon={<GroupAddIcon />}
                  href="https://github.com/qkral/zingu/blob/main/CONTRIBUTING.md"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Contribute
                </Button>
              </Box>
            </Paper>
          </Box>
        </Grid>
        <Grid 
          item 
          xs={12} 
          md={6} 
          sx={{ 
            display: { xs: 'none', md: 'block' },
            textAlign: 'center' 
          }}
        >
          <Paper 
            elevation={12} 
            sx={{ 
              borderRadius: 4, 
              overflow: 'hidden',
              maxWidth: 500,
              margin: 'auto'
            }}
          >
            {(() => {
              console.log('Current directory:', window.location.pathname);
              console.log('Image full path:', window.location.origin + '/images/hero-illustration-new.jpg');
              return null;
            })()}
            <img
              src="/images/soner-eker-jhtPCeQ2mMU-unsplash.jpg"
              alt="Signage Illustration"
              className="mx-auto max-w-full h-auto"
            />
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}
