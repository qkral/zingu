import axios from 'axios';

// Determine the current environment
const isProduction = import.meta.env.PROD;



// Select the appropriate base URL
export const API_BASE_URL = isProduction 
  ? import.meta.env.VITE_API_BASE_URL_PRODUCTION 
  : import.meta.env.VITE_API_BASE_URL_LOCAL;

console.log('Selected API Base URL:', API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add request interceptor for error handling
api.interceptors.request.use(
  (config) => {
    // You can add auth headers or other request modifications here
    console.log('Making API request:', {
      url: config.url,
      method: config.method,
      baseURL: config.baseURL,
      data: config.data instanceof FormData ? 'FormData' : config.data
    });
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', {
      url: response.config.url,
      status: response.status,
      data: response.data
    });
    return response;
  },
  (error) => {
    console.error('API Response Error:', {
      url: error.config?.url,
      timeout: error.config?.timeout,
      code: error.code,
      message: error.message,
      response: error.response?.data
    });
    if (error.response) {
      // Server responded with error
      console.error('Error Response:', error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('No Response:', error.request);
    }
    return Promise.reject(error);
  }
);

export default api;
