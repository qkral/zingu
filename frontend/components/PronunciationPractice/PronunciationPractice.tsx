import { useState } from 'react';
import {
  Box,
  Button,
  Stack,
  Typography,
  TextField,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Modal,
} from '@mui/material';
import { Check as CheckIcon, Error as ErrorIcon, Mic as MicIcon } from '@mui/icons-material';
import axios from 'axios';

interface PronunciationFeedback {
  accuracy: number
  pronunciation: number
  completeness: number
  fluency: number
  words: Array<{
    word: string
    accuracy: number
    error_type: string
    syllables: Array<{
      syllable: string
      accuracy: number
    }>
    phonemes: Array<{
      phoneme: string
      accuracy: number
    }>
  }>
  phoneme_level_feedback: string[]
  general_feedback: string[]
}

interface Exercise {
  title: string
  description: string
  example_words: string[]
  difficulty: number
}

interface AICoachResponse {
  message: string
  exercises: Exercise[]
}

const PronunciationPractice = () => {
  const [isRecording, setIsRecording] = useState(false)
  const [text, setText] = useState('')
  const [feedback, setFeedback] = useState<PronunciationFeedback | null>(null)
  const [coachResponse, setCoachResponse] = useState<AICoachResponse | null>(null)
  const [isLoadingCoach, setIsLoadingCoach] = useState(false)
  const [open, setOpen] = useState(false)
  const handleOpen = () => setOpen(true)
  const handleClose = () => setOpen(false)

  const startRecording = async () => {
    if (!text.trim()) {
      alert('Please enter text to practice')
      return
    }

    try {
      setIsRecording(true)
      // TODO: Implement audio recording logic
      alert('Recording started')
    } catch (error) {
      alert('Error accessing microphone')
    }
  }

  const stopRecording = () => {
    setIsRecording(false)
    // TODO: Implement stop recording and send to backend
    // For now, using mock data that matches the backend format
    const mockFeedback = {
      accuracy: 0.75,
      pronunciation: 0.72,
      completeness: 0.80,
      fluency: 0.78,
      words: [
        {
          word: 'example',
          accuracy: 0.65,
          error_type: 'pronunciation',
          syllables: [
            { syllable: 'ex', accuracy: 0.7 },
            { syllable: 'am', accuracy: 0.6 },
            { syllable: 'ple', accuracy: 0.65 }
          ],
          phonemes: [
            { phoneme: 'ɪɡ', accuracy: 0.6 },
            { phoneme: 'z', accuracy: 0.7 }
          ]
        },
        {
          word: 'pronunciation',
          accuracy: 0.75,
          error_type: 'stress',
          syllables: [
            { syllable: 'pro', accuracy: 0.8 },
            { syllable: 'nun', accuracy: 0.7 },
            { syllable: 'ci', accuracy: 0.75 },
            { syllable: 'a', accuracy: 0.7 },
            { syllable: 'tion', accuracy: 0.8 }
          ],
          phonemes: [
            { phoneme: 'ʃ', accuracy: 0.7 },
            { phoneme: 'n', accuracy: 0.8 }
          ]
        }
      ],
      phoneme_level_feedback: [
        'The "ɪɡ" sound in "example" needs improvement',
        'Work on the "ʃ" sound in "pronunciation"'
      ],
      general_feedback: [
        'Focus on word stress patterns',
        'Pay attention to syllable timing'
      ]
    }
    
    console.log('Setting feedback with data:', mockFeedback)
    console.log('Words with accuracy:', mockFeedback.words.map(w => ({ word: w.word, accuracy: w.accuracy })))
    console.log('Any words below 0.8 accuracy:', mockFeedback.words.some(word => word.accuracy < 0.8))
    
    setFeedback(mockFeedback)
  }

  const consultAICoach = async () => {
    if (!feedback) return

    setIsLoadingCoach(true)
    try {
      // Send request even if no words detected
      const response = await axios.post<AICoachResponse>('/api/ai-coach', {
        message: feedback.words.length === 0 
          ? "No words were detected in the recording. I need help with basic pronunciation practice."
          : "I need help with pronunciation practice.",
        pronunciation_history: feedback.words.length === 0 
          ? [] // Empty history when no words detected
          : feedback.words
              .filter(item => item.accuracy < 0.8)
              .map(item => ({
                word: item.word,
                phoneme: item.phonemes.filter(p => p.accuracy < 0.8).map(p => p.phoneme).join(', '),
                accuracy: Math.round(item.accuracy * 100)
              }))
      })

      setCoachResponse(response.data)
      handleOpen()
    } catch (error) {
      alert('Error getting AI coach response')
    } finally {
      setIsLoadingCoach(false)
    }
  }

  return (
    <Stack 
      component="div" 
      spacing={8} 
      sx={{ width: '100%' }}
    >
      <Box textAlign="center">
        <Typography variant="h4" mb={4}>Pronunciation Practice</Typography>
        <Typography color="gray">
          Enter text and record yourself to get pronunciation feedback
        </Typography>
      </Box>

      <TextField
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter text to practice..."
        size="medium"
        rows={4}
      />

      <Box textAlign="center">
        <Button
          component="button"
          size="large"
          color={isRecording ? 'error' : 'primary'}
          onClick={isRecording ? stopRecording : startRecording}
          startIcon={<MicIcon />}
          sx={{ mr: 2 }}
        >
          {isRecording ? 'Stop Recording' : 'Start Recording'}
        </Button>
      </Box>

      {feedback && (
        <Box 
          component="div"
          sx={{
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 2,
            p: 6
          }}
        >
          <Typography variant="h6" mb={4}>Feedback</Typography>
          
          <Box mb={6}>
            <Typography mb={2}>
              Overall Accuracy: {(feedback.accuracy * 100).toFixed(1)}%
            </Typography>
            <Typography mb={2}>
              Pronunciation: {(feedback.pronunciation * 100).toFixed(1)}%
            </Typography>
            <Typography mb={2}>
              Completeness: {(feedback.completeness * 100).toFixed(1)}%
            </Typography>
            <Typography>
              Fluency: {(feedback.fluency * 100).toFixed(1)}%
            </Typography>
          </Box>

          <Box mb={6}>
            <Typography color="warning">
              No words were detected in your recording. This might be due to:
            </Typography>
            <List>
              <ListItem>
                <ListItemIcon>
                  <ErrorIcon color="warning" />
                </ListItemIcon>
                <ListItemText primary="Low speaking volume" />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <ErrorIcon color="warning" />
                </ListItemIcon>
                <ListItemText primary="Background noise" />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <ErrorIcon color="warning" />
                </ListItemIcon>
                <ListItemText primary="Unclear pronunciation" />
              </ListItem>
            </List>
          </Box>

          {feedback.phoneme_level_feedback.length > 0 && (
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <ErrorIcon color="warning" />
              <Typography color="text.secondary">
                {feedback.phoneme_level_feedback[0]}
              </Typography>
            </Box>
          )}
          {feedback.phoneme_level_feedback.length > 1 && (
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <ErrorIcon color="warning" />
              <Typography color="text.secondary">
                {feedback.phoneme_level_feedback[1]}
              </Typography>
            </Box>
          )}
          {feedback.phoneme_level_feedback.length > 2 && (
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <ErrorIcon color="warning" />
              <Typography color="text.secondary">
                {feedback.phoneme_level_feedback[2]}
              </Typography>
            </Box>
          )}
          {feedback.general_feedback.length > 0 && (
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <CheckIcon color="success" />
              <Typography color="text.secondary">
                {feedback.general_feedback[0]}
              </Typography>
            </Box>
          )}
          {feedback.general_feedback.length > 1 && (
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <CheckIcon color="success" />
              <Typography color="text.secondary">
                {feedback.general_feedback[1]}
              </Typography>
            </Box>
          )}
          {feedback.general_feedback.length > 2 && (
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <CheckIcon color="success" />
              <Typography color="text.secondary">
                {feedback.general_feedback[2]}
              </Typography>
            </Box>
          )}
          <Box textAlign="center">
            <Button
              component="button"
              color="primary"
              size="large"
              startIcon={<MicIcon />}
              onClick={consultAICoach}
              disabled={isLoadingCoach}
            >
              Get Personalized Practice Exercises
            </Button>
          </Box>
        </Box>
      )}

      <Modal
        open={open}
        onClose={handleClose}
      >
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '80%',
          bgcolor: 'background.paper',
          border: '2px solid #000',
          boxShadow: 24,
          p: 4,
        }}>
          <Typography variant="h6" mb={4}>AI Coach Suggestions</Typography>
          {coachResponse && (
            <Stack component="div" spacing={6} direction="column" sx={{ width: '100%' }}>
              <Typography>{coachResponse.message}</Typography>
              
              {coachResponse.exercises.length > 0 && (
                <Box>
                  <Typography variant="h6" mb={3}>Practice Exercises</Typography>
                  <List>
                    {coachResponse.exercises.map((exercise, index) => (
                      <ListItem key={index} sx={{ border: '1px solid #ddd', borderRadius: '10px', p: 4 }}>
                        <Typography variant="h6" mb={2}>{exercise.title}</Typography>
                        <Typography mb={2}>{exercise.description}</Typography>
                        <Typography fontStyle="italic">
                          Example words: {exercise.example_words.join(', ')}
                        </Typography>
                        <Typography fontSize="small" color="gray">
                          Difficulty: {exercise.difficulty}/5
                        </Typography>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Stack>
          )}
          <Box textAlign="center">
            <Button
              component="button"
              color="primary"
              onClick={handleClose}
            >
              Close
            </Button>
          </Box>
        </Box>
      </Modal>
    </Stack>
  )
}

export default PronunciationPractice
