const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const dotenv = require('dotenv');
const fetch = require('node-fetch');

// Load environment variables
dotenv.config();
console.log('dotenv.config() executed.');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Ollama Configuration
const OLLAMA_API_URL = process.env.OLLAMA_API_URL || 'http://localhost:11434/api';

// Test Ollama connection
async function testOllamaConnection() {
  try {
    const response = await fetch(`${OLLAMA_API_URL}/tags`);
    const data = await response.json();
    console.log('Ollama connection successful. Available models:', data.models.map(m => m.name));
  } catch (error) {
    console.error('Ollama connection test failed:', error);
  }
}
testOllamaConnection();

// MongoDB Connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/hr-assistant')
  .then(() => console.log('Connected to MongoDB'))
  .catch(err => console.error('MongoDB connection error:', err));

// Routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api/employees', require('./routes/employees'));
app.use('/api/leave', require('./routes/leave'));
app.use('/api/documents', require('./routes/documents'));
app.use('/api/chat', require('./routes/chat'));
app.use('/api/ats', require('./routes/ats'));
console.log('Attempting to load interviews route...');
app.use('/api/interviews', require('./routes/interviews'));

// Global Error Handler
app.use((err, req, res, next) => {
  console.error('Global Error Caught:', err.stack || err.message);
  res.status(500).json({ error: 'Something went wrong on the server.' });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});