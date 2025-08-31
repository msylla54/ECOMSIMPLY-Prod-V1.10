#!/usr/bin/env python3
"""
Proxy API temporaire pour ECOMSIMPLY
Route les requêtes /api/* vers localhost:8001 en attendant la correction Kubernetes
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import json
import socket

class APIProxyHandler(BaseHTTPRequestHandler):
    """Handler pour proxy API"""
    
    def do_OPTIONS(self):
        """Gérer les requêtes CORS OPTIONS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """Proxy GET requests"""
        self.proxy_request('GET')
    
    def do_POST(self):
        """Proxy POST requests"""
        self.proxy_request('POST')
    
    def do_PUT(self):
        """Proxy PUT requests"""
        self.proxy_request('PUT')
    
    def do_DELETE(self):
        """Proxy DELETE requests"""
        self.proxy_request('DELETE')
    
    def proxy_request(self, method):
        """Proxy une requête vers le backend local"""
        try:
            # URL du backend local
            backend_url = f"http://localhost:8001{self.path}"
            
            # Headers de la requête originale (sauf Host)
            headers = {}
            for name, value in self.headers.items():
                if name.lower() not in ['host', 'connection']:
                    headers[name] = value
            
            # Corps de la requête pour POST/PUT
            content_length = self.headers.get('Content-Length')
            body = None
            if content_length:
                body = self.rfile.read(int(content_length))
            
            # Effectuer la requête proxy
            response = requests.request(
                method=method,
                url=backend_url,
                headers=headers,
                data=body,
                timeout=30
            )
            
            # Renvoyer la réponse
            self.send_response(response.status_code)
            
            # Headers CORS + headers originaux
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            
            for name, value in response.headers.items():
                if name.lower() not in ['connection', 'transfer-encoding']:
                    self.send_header(name, value)
            
            self.end_headers()
            
            # Corps de la réponse
            self.wfile.write(response.content)
            
            print(f"✅ {method} {self.path} → {response.status_code}")
            
        except Exception as e:
            print(f"❌ Erreur proxy {method} {self.path}: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = json.dumps({"error": f"Proxy error: {str(e)}"})
            self.wfile.write(error_response.encode())

def find_free_port():
    """Trouve un port libre"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def start_proxy():
    """Démarre le serveur proxy"""
    port = find_free_port()
    server = HTTPServer(('0.0.0.0', port), APIProxyHandler)
    
    print(f"🚀 Proxy API ECOMSIMPLY démarré")
    print(f"🌐 URL: http://localhost:{port}")
    print(f"📡 Proxy vers: http://localhost:8001")
    print(f"🎯 Usage: Remplacer REACT_APP_BACKEND_URL par http://localhost:{port}")
    print(f"⚠️  Solution temporaire en attendant correction Kubernetes")
    print()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du proxy API")
        server.shutdown()

if __name__ == "__main__":
    start_proxy()