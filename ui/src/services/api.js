const API_BASE_URL = 'http://127.0.0.1:8000';

export const apiService = {
  // Health check endpoint
  async checkHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  },

  // Analyze text using Llama API
  async analyzeText(text) {
    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Text analysis failed:', error);
      throw error;
    }
  },

  async improveText(text) {
    try {
      const response = await fetch(`${API_BASE_URL}/improve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Text improvement failed:', error);
      throw error;
    }
  },

  // Test simple endpoint
  async testSimple() {
    try {
      const response = await fetch(`${API_BASE_URL}/debug/test-simple`);
      return await response.json();
    } catch (error) {
      console.error('Simple test failed:', error);
      throw error;
    }
  }
};

