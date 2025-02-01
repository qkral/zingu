import { useState } from 'react';
import axios from 'axios';

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

interface PronunciationAssessment {
  accuracy: number;
  pronunciation: number;
  completeness: number;
  fluency: number;
  words: Word[];
  phoneme_level_feedback: string[];
  general_feedback: string[];
}

export const usePronunciationAssessment = () => {
  const [isAssessing, setIsAssessing] = useState(false);
  const [assessment, setAssessment] = useState<PronunciationAssessment | null>(null);
  const [error, setError] = useState<string | null>(null);

  const assess = async (formData: FormData) => {
    try {
      console.log('Starting pronunciation assessment...');
      setIsAssessing(true);
      setError(null);

      // Log form data contents
      console.log('Form data entries:');
      for (const [key, value] of formData.entries()) {
        if (value instanceof Blob) {
          console.log(`${key}: Blob size=${value.size} bytes, type=${value.type}`);
        } else {
          console.log(`${key}: ${value}`);
        }
      }

      const response = await axios.post<PronunciationAssessment>(
        'http://localhost:8000/api/improve-pronunciation',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      console.log('Assessment API response:', response.data);
      setAssessment(response.data);
      
    } catch (err) {
      console.error('Assessment error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to assess pronunciation';
      console.error('Error details:', errorMessage);
      setError(errorMessage);
      setAssessment(null);
    } finally {
      setIsAssessing(false);
      console.log('Assessment completed');
    }
  };

  return {
    assess,
    isAssessing,
    assessment,
    error,
  };
};
