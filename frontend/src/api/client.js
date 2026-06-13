// frontend/src/api/client.js
import axios from 'axios';

// This points directly to your FastAPI server!
export const apiClient = axios.create({
    baseURL: 'http://localhost:8000',
});
