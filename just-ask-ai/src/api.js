import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000'
});

export const sendUserQuery = async (question) => {
    try {
      const response = await api.post('/query', { question });
      console.log("API Response:", response.data); // Debugging
      return response.data;
    } catch (error) {
      console.error("API Error:", error.response ? error.response.data : error.message);
      return { error: "Error storing query." };
    }
  };
  
export default api;
