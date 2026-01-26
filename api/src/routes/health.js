const express = require('express');
const router = express.Router();
const inferenceService = require('../services/inferenceService');

/**
 * GET /api/health
 * Overall system health check
 */
router.get('/', async (req, res) => {
  const nodeStatus = {
    status: 'healthy',
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    timestamp: new Date().toISOString()
  };

  let inferenceStatus;
  try {
    inferenceStatus = await inferenceService.checkHealth();
    inferenceStatus.reachable = true;
  } catch (error) {
    inferenceStatus = {
      reachable: false,
      error: error.message,
      status: 'unavailable'
    };
  }

  const overallStatus = inferenceStatus.reachable ? 'healthy' : 'degraded';

  res.json({
    status: overallStatus,
    services: {
      api: nodeStatus,
      inference: inferenceStatus
    },
    message: overallStatus === 'healthy' 
      ? 'All systems operational' 
      : 'Inference server unavailable - some features may not work'
  });
});

/**
 * GET /api/health/inference
 * Detailed inference server health check
 */
router.get('/inference', async (req, res) => {
  try {
    const health = await inferenceService.checkHealth();
    
    res.json({
      status: 'healthy',
      inference: health,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(503).json({
      status: 'unavailable',
      error: error.message,
      message: 'Inference server is not reachable',
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/health/rag
 * RAG system status from inference server
 */
router.get('/rag', async (req, res) => {
  try {
    const ragStatus = await inferenceService.getRagStatus();
    
    res.json({
      status: 'healthy',
      rag: ragStatus,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(503).json({
      status: 'unavailable',
      error: error.message,
      message: 'RAG system status unavailable',
      timestamp: new Date().toISOString()
    });
  }
});

module.exports = router;
