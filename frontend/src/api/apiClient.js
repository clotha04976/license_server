import axios from 'axios';

const apiClient = axios.create({
  // Use environment variable for API base URL
  // In Vite, environment variables are exposed via import.meta.env
  // They must be prefixed with VITE_ (e.g., VITE_API_BASE_URL)
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1', // Fallback for local development
  headers: {
    'Content-Type': 'application/json',
  },
});

// You can add interceptors here for handling tokens, errors, etc.
// For example, to add the auth token to every request:

apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;