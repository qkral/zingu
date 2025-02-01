import { useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  styled
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import SportsEsportsIcon from '@mui/icons-material/SportsEsports';

const StyledCard = styled(Card)(({ }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'transform 0.2s ease-in-out',
  '&:hover': {
    transform: 'scale(1.02)',
    cursor: 'pointer',
  },
}));


const games = [
  {
    id: 'word-detective',
    title: 'Word Detective',
    description: 'Solve word puzzles by listening to clues and speaking the answer. Perfect for improving pronunciation and vocabulary!',
    icon: <SearchIcon sx={{ fontSize: 40 }} />,
    path: '/word-detective',
    color: '#FF9800', // Orange
  },
  // Add more games here in the future
];

export default function GamesPage() {
  const navigate = useNavigate();

  return (
    <Container maxWidth="lg" sx={{ py: 8 }}>
      <Typography
        component="h1"
        variant="h2"
        align="center"
        color="text.primary"
        gutterBottom
        sx={{ mb: 6 }}
      >
        <SportsEsportsIcon sx={{ fontSize: 45, verticalAlign: 'middle', mr: 2 }} />
        Fun Language Games
      </Typography>
      
      <Grid container spacing={4}>
        {games.map((game) => (
          <Grid item key={game.id} xs={12} sm={6} md={4}>
            <StyledCard 
              onClick={() => navigate(game.path)}
              sx={{ 
                '& .MuiCardContent-root': {
                  backgroundColor: `${game.color}15`, // Very light version of the color
                }
              }}
            >
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'center',
                    mb: 2,
                    color: game.color,
                  }}
                >
                  {game.icon}
                </Box>
                <Typography gutterBottom variant="h5" component="h2" align="center">
                  {game.title}
                </Typography>
                <Typography align="center" color="text.secondary">
                  {game.description}
                </Typography>
              </CardContent>
              <Box sx={{ flexGrow: 1 }} />
              <Button 
                size="large" 
                sx={{ 
                  m: 2,
                  color: game.color,
                  borderColor: game.color,
                  '&:hover': {
                    borderColor: game.color,
                    backgroundColor: `${game.color}15`,
                  }
                }}
                variant="outlined"
              >
                Play Now
              </Button>
            </StyledCard>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
}
