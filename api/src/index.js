require('dotenv').config();

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');

// Import routes
const analysisRoutes = require('./routes/analysis');
const healthRoutes = require('./routes/health');

const app = express();
const PORT = process.env.PORT || 3001;

// Security middleware
app.use(helmet());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: { error: 'Too many requests, please try again later.' }
});
app.use('/api/', limiter);

// CORS configuration
app.use(cors({
  origin: [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    process.env.FRONTEND_URL
  ].filter(Boolean),
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Request logging
app.use(morgan('dev'));

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// API Routes
app.use('/api/analysis', analysisRoutes);
app.use('/api/health', healthRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'Human-AI Text Checker API',
    version: '1.0.0',
    description: 'Node.js API server with FastAPI inference backend',
    endpoints: {
      analysis: {
        analyze: 'POST /api/analysis/analyze - Analyze text for AI/Human detection',
        langchain: 'POST /api/analysis/langchain - LangChain RAG-enhanced analysis',
        history: 'GET /api/analysis/history - Get analysis history'
      },
      health: {
        status: 'GET /api/health - Get system health status',
        inference: 'GET /api/health/inference - Check inference server status'
      }
    }
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.method} ${req.path} not found`
  });
});

// Global error handler
app.use((err, req, res, next) => {
  console.error('Error:', err);
  
  const statusCode = err.statusCode || 500;
  const message = err.message || 'Internal Server Error';
  
  res.status(statusCode).json({
    error: statusCode === 500 ? 'Internal Server Error' : message,
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════════════════════════╗
║     Human-AI Text Checker - Node.js API Server             ║
╠════════════════════════════════════════════════════════════╣
║  Server running on: http://localhost:${PORT}                   ║
║  Inference server:  ${process.env.INFERENCE_URL || 'http://localhost:8000'}          ║
║  Environment:       ${process.env.NODE_ENV || 'development'}                        ║
╚════════════════════════════════════════════════════════════╝
  `);
});

module.exports = app;
