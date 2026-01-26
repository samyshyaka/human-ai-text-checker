const axios = require('axios');

// FastAPI inference server URL
const INFERENCE_URL = process.env.INFERENCE_URL || 'http://localhost:8000';

// Create axios instance with default config
const inferenceClient = axios.create({
  baseURL: INFERENCE_URL,
  timeout: 60000, // 60 seconds timeout for inference
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * Inference Service
 * Handles all communication with the FastAPI inference server
 */
const inferenceService = {
  /**
   * Analyze text using the standard endpoint with RAG enhancement
   * @param {string} text - Text to analyze
   * @returns {Promise<Object>} Analysis result
   */
  async analyzeText(text) {
    try {
      const response = await inferenceClient.post('/analyze', { text });
      return response.data;
    } catch (error) {
      console.error('Inference analyzeText error:', error.message);
      throw error;
    }
  },

  /**
   * Analyze text using LangChain RAG system
   * @param {string} text - Text to analyze
   * @returns {Promise<Object>} Analysis result with LangChain context
   */
  async analyzeLangChain(text) {
    try {
      const response = await inferenceClient.post('/analyze/langchain', { text });
      return response.data;
    } catch (error) {
      console.error('Inference analyzeLangChain error:', error.message);
      throw error;
    }
  },

  /**
   * Check inference server health
   * @returns {Promise<Object>} Health status
   */
  async checkHealth() {
    try {
      const response = await inferenceClient.get('/health', { timeout: 5000 });
      return response.data;
    } catch (error) {
      console.error('Inference health check error:', error.message);
      throw error;
    }
  },

  /**
   * Get RAG system status
   * @returns {Promise<Object>} RAG system status
   */
  async getRagStatus() {
    try {
      const response = await inferenceClient.get('/rag/status', { timeout: 5000 });
      return response.data;
    } catch (error) {
      console.error('RAG status check error:', error.message);
      throw error;
    }
  },

  /**
   * Test RAG system with sample queries
   * @returns {Promise<Object>} RAG test results
   */
  async testRag() {
    try {
      const response = await inferenceClient.get('/rag/test', { timeout: 30000 });
      return response.data;
    } catch (error) {
      console.error('RAG test error:', error.message);
      throw error;
    }
  }
};

module.exports = inferenceService;
