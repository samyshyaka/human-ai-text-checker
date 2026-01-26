const express = require('express');
const router = express.Router();
const inferenceService = require('../services/inferenceService');
const { v4: uuidv4 } = require('uuid');

// In-memory storage for analysis history (replace with database in production)
const analysisHistory = new Map();

/**
 * POST /api/analysis/analyze
 * Analyze text using FastAPI inference with RAG enhancement
 */
router.post('/analyze', async (req, res, next) => {
  try {
    const { text } = req.body;

    if (!text || typeof text !== 'string') {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Text field is required and must be a string'
      });
    }

    const trimmedText = text.trim();
    if (trimmedText.length === 0) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Text cannot be empty'
      });
    }

    if (trimmedText.length > 50000) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Text exceeds maximum length of 50,000 characters'
      });
    }

    // Call FastAPI inference server
    const result = await inferenceService.analyzeText(trimmedText);

    // Create analysis record
    const analysisId = uuidv4();
    const analysis = {
      id: analysisId,
      text: trimmedText.substring(0, 500) + (trimmedText.length > 500 ? '...' : ''),
      textLength: trimmedText.length,
      result,
      createdAt: new Date().toISOString(),
      method: 'standard'
    };

    // Store in history
    analysisHistory.set(analysisId, analysis);

    res.json({
      success: true,
      analysisId,
      ...result
    });

  } catch (error) {
    console.error('Analysis error:', error);
    
    if (error.response) {
      // FastAPI returned an error
      return res.status(error.response.status || 500).json({
        error: 'Inference Error',
        message: error.response.data?.detail || 'Inference server error',
        source: 'inference'
      });
    }

    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({
        error: 'Service Unavailable',
        message: 'Inference server is not available. Please ensure FastAPI is running.',
        source: 'connection'
      });
    }

    next(error);
  }
});

/**
 * POST /api/analysis/langchain
 * Analyze text using LangChain RAG system
 */
router.post('/langchain', async (req, res, next) => {
  try {
    const { text } = req.body;

    if (!text || typeof text !== 'string') {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Text field is required and must be a string'
      });
    }

    const trimmedText = text.trim();
    if (trimmedText.length === 0) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Text cannot be empty'
      });
    }

    // Call FastAPI LangChain endpoint
    const result = await inferenceService.analyzeLangChain(trimmedText);

    // Create analysis record
    const analysisId = uuidv4();
    const analysis = {
      id: analysisId,
      text: trimmedText.substring(0, 500) + (trimmedText.length > 500 ? '...' : ''),
      textLength: trimmedText.length,
      result,
      createdAt: new Date().toISOString(),
      method: 'langchain'
    };

    // Store in history
    analysisHistory.set(analysisId, analysis);

    res.json({
      success: true,
      analysisId,
      ...result
    });

  } catch (error) {
    console.error('LangChain analysis error:', error);
    
    if (error.response) {
      return res.status(error.response.status || 500).json({
        error: 'Inference Error',
        message: error.response.data?.detail || 'LangChain inference error',
        source: 'langchain'
      });
    }

    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({
        error: 'Service Unavailable',
        message: 'Inference server is not available',
        source: 'connection'
      });
    }

    next(error);
  }
});

/**
 * GET /api/analysis/history
 * Get analysis history
 */
router.get('/history', (req, res) => {
  const { limit = 50, offset = 0 } = req.query;
  
  const historyArray = Array.from(analysisHistory.values())
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(Number(offset), Number(offset) + Number(limit));

  res.json({
    success: true,
    total: analysisHistory.size,
    limit: Number(limit),
    offset: Number(offset),
    data: historyArray
  });
});

/**
 * GET /api/analysis/:id
 * Get specific analysis by ID
 */
router.get('/:id', (req, res) => {
  const { id } = req.params;
  const analysis = analysisHistory.get(id);

  if (!analysis) {
    return res.status(404).json({
      error: 'Not Found',
      message: 'Analysis not found'
    });
  }

  res.json({
    success: true,
    data: analysis
  });
});

/**
 * DELETE /api/analysis/:id
 * Delete specific analysis
 */
router.delete('/:id', (req, res) => {
  const { id } = req.params;
  
  if (!analysisHistory.has(id)) {
    return res.status(404).json({
      error: 'Not Found',
      message: 'Analysis not found'
    });
  }

  analysisHistory.delete(id);

  res.json({
    success: true,
    message: 'Analysis deleted successfully'
  });
});

module.exports = router;
