/**
 * API Service for Human-AI Text Checker
 * 
 * Communicates with the Node.js API server which proxies
 * inference requests to the FastAPI backend.
 */

// Node.js API server URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      throw {
        status: response.status,
        message: data.message || data.error || `HTTP error ${response.status}`,
        data,
      };
    }

    return data;
  } catch (error) {
    if (error.status) {
      throw error; // Re-throw API errors
    }
    // Network or parsing errors
    console.error('API request failed:', error);
    throw {
      status: 0,
      message: error.message || 'Network error - please check your connection',
      data: null,
    };
  }
}

export const apiService = {
  /**
   * Health check - get overall system status
   */
  async checkHealth() {
    return fetchAPI('/api/health');
  },

  /**
   * Check inference server status specifically
   */
  async checkInferenceHealth() {
    return fetchAPI('/api/health/inference');
  },

  /**
   * Get RAG system status
   */
  async checkRagStatus() {
    return fetchAPI('/api/health/rag');
  },

  /**
   * Analyze text using standard endpoint with RAG enhancement
   * @param {string} text - Text to analyze
   * @returns {Promise<Object>} Analysis result
   */
  async analyzeText(text) {
    return fetchAPI('/api/analysis/analyze', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  },

  /**
   * Analyze text using LangChain RAG system
   * @param {string} text - Text to analyze
   * @returns {Promise<Object>} Analysis result with LangChain context
   */
  async analyzeWithLangChain(text) {
    return fetchAPI('/api/analysis/langchain', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  },

  /**
   * Get analysis history
   * @param {Object} options - Pagination options
   * @param {number} options.limit - Number of results
   * @param {number} options.offset - Starting offset
   */
  async getHistory({ limit = 50, offset = 0 } = {}) {
    return fetchAPI(`/api/analysis/history?limit=${limit}&offset=${offset}`);
  },

  /**
   * Get specific analysis by ID
   * @param {string} id - Analysis ID
   */
  async getAnalysis(id) {
    return fetchAPI(`/api/analysis/${id}`);
  },

  /**
   * Delete analysis by ID
   * @param {string} id - Analysis ID
   */
  async deleteAnalysis(id) {
    return fetchAPI(`/api/analysis/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Legacy method - redirects to standard analysis
   * @deprecated Use analyzeText instead
   */
  async testSimple() {
    return this.checkHealth();
  }
};

export default apiService;
