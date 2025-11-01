import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const sendNlQuery = (query) => {
  return apiClient.post('/nl2gql', { query });
};

export const sendGqlQuery = (query, variables = {}) => {
    return apiClient.post('/graphql', { query, variables });
};

export default apiClient;
