// API Configuration
const isDevelopment = process.env.NODE_ENV === 'development';

// Use local development server in dev, Firebase Functions in production
export const API_BASE_URL = isDevelopment 
  ? 'http://localhost:5001/api' 
  : 'https://us-central1-bulletbaseai.cloudfunctions.net/api/api';

export const config = {
  apiBaseUrl: API_BASE_URL,
};
