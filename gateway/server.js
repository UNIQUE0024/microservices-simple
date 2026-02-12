const express = require('express');
const axios = require('axios');
const rateLimit = require('express-rate-limit');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

const PORT = process.env.PORT || 8080;
const AUTH_SERVICE = process.env.AUTH_SERVICE || 'http://localhost:8001';
const PRODUCT_SERVICE = process.env.PRODUCT_SERVICE || 'http://localhost:8002';

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // 100 requests per window
});
app.use(limiter);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'api-gateway' });
});

// Auth routes
app.post('/api/auth/register', async (req, res) => {
  try {
    const response = await axios.post(`${AUTH_SERVICE}/api/auth/register`, req.body);
    res.status(response.status).json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(
      error.response?.data || { error: 'Service unavailable' }
    );
  }
});

app.post('/api/auth/login', async (req, res) => {
  try {
    const response = await axios.post(`${AUTH_SERVICE}/api/auth/login`, req.body);
    res.status(response.status).json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(
      error.response?.data || { error: 'Service unavailable' }
    );
  }
});

// Product routes
app.get('/api/products', async (req, res) => {
  try {
    const response = await axios.get(`${PRODUCT_SERVICE}/api/products`);
    res.status(response.status).json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(
      error.response?.data || { error: 'Service unavailable' }
    );
  }
});

app.get('/api/products/:id', async (req, res) => {
  try {
    const response = await axios.get(`${PRODUCT_SERVICE}/api/products/${req.params.id}`);
    res.status(response.status).json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(
      error.response?.data || { error: 'Service unavailable' }
    );
  }
});

app.post('/api/products', async (req, res) => {
  try {
    const token = req.headers.authorization;
    const response = await axios.post(
      `${PRODUCT_SERVICE}/api/products`,
      req.body,
      { headers: { Authorization: token } }
    );
    res.status(response.status).json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(
      error.response?.data || { error: 'Service unavailable' }
    );
  }
});

app.listen(PORT, () => {
  console.log(`API Gateway running on port ${PORT}`);
});
