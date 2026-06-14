import axios, { type InternalAxiosRequestConfig } from 'axios';

const api = axios.create({
  baseURL: '/api',
});

// Interceptor for JWT injection
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('omnicore_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
