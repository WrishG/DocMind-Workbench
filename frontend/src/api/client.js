// frontend/src/api/client.js
import axios from 'axios';

// This points to your FastAPI server!
// In production (Vercel), it uses the Render URL. In development, it defaults to localhost.
export const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});
