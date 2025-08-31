const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const port = process.env.PORT || 3000;

// CORS headers pour toutes les requêtes
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, HEAD');
  res.header('Access-Control-Allow-Headers', '*');
  
  // Gérer les requêtes HEAD
  if (req.method === 'HEAD') {
    res.status(200).end();
    return;
  }
  
  // Gérer les requêtes OPTIONS (CORS preflight)
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  
  next();
});

// 🚀 PROXY API - Solution temporaire pour contourner le problème Kubernetes
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:8001',
  changeOrigin: true,
  pathRewrite: {
    '^/api': '/api', // Garder le préfixe /api
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`🔄 Proxy API: ${req.method} ${req.url} → http://localhost:8001${req.url}`);
  },
  onProxyRes: (proxyRes, req, res) => {
    console.log(`✅ Proxy API: ${req.method} ${req.url} → ${proxyRes.statusCode}`);
  },
  onError: (err, req, res) => {
    console.error(`❌ Proxy API Error: ${req.method} ${req.url} → ${err.message}`);
    res.status(500).json({ error: 'Backend connection failed', details: err.message });
  }
}));

// Servir les fichiers statiques
app.use(express.static(path.join(__dirname, 'build')));

// Route catch-all pour React Router
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'build/index.html'));
});

app.listen(port, '0.0.0.0', () => {
  console.log(`✅ Frontend server running on port ${port}`);
  console.log(`🔗 Accessible at: http://localhost:${port}`);
  console.log(`🚀 API Proxy enabled: /api/* → http://localhost:8001/api/*`);
});