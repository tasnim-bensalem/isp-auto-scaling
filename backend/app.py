from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import time
import hashlib
import os
import random

app = FastAPI(
    title="ISP Auto-Scaling Backend API",
    description="Backend API pour projet ISP - Auto-Scaling Intelligent",
    version="1.0.0"
)

# CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Métriques Prometheus automatiques
Instrumentator().instrument(app).expose(app)

@app.get("/")
def root():
    """Point d'entrée principal"""
    return {
        "message": "ISP Auto-Scaling Backend API",
        "status": "running",
        "pod": os.getenv("HOSTNAME", "local"),
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    """Health check pour Kubernetes"""
    return {"status": "healthy"}

@app.get("/api/tasks")
def get_tasks():
    """Retourne une liste de tâches (exemple)"""
    return {
        "tasks": [
            {"id": 1, "title": "Setup Kubernetes", "status": "done", "priority": "high"},
            {"id": 2, "title": "Deploy Backend API", "status": "in_progress", "priority": "high"},
            {"id": 3, "title": "Create ML Service", "status": "todo", "priority": "medium"},
            {"id": 4, "title": "Implement Auto-Scaling", "status": "todo", "priority": "high"},
            {"id": 5, "title": "Setup Monitoring", "status": "done", "priority": "medium"},
        ]
    }

@app.post("/api/tasks")
def create_task(title: str, priority: str = "medium"):
    """Créer une nouvelle tâche"""
    return {
        "id": random.randint(100, 999),
        "title": title,
        "status": "todo",
        "priority": priority,
        "created_at": time.time()
    }

@app.get("/api/stress")
def generate_load(iterations: int = 500000):
    """
    Génère de la charge CPU pour tester l'auto-scaling.
    Query param: iterations (default: 500000)
    Plus iterations est élevé, plus ça consomme de CPU.
    """
    start = time.time()
    
    # Calcul intensif : hash itératif
    result = "isp-autoscaling-project"
    for i in range(iterations):
        result = hashlib.sha256(result.encode()).hexdigest()
    
    duration = time.time() - start
    
    return {
        "message": "CPU load generated successfully",
        "duration_seconds": round(duration, 3),
        "iterations": iterations,
        "pod": os.getenv("HOSTNAME", "local"),
        "cpu_intensive": True
    }

@app.get("/api/metrics/current")
def current_metrics():
    """
    Retourne métriques actuelles simulées.
    Dans une vraie app, ça viendrait de vraies métriques système.
    """
    return {
        "cpu_percent": random.randint(20, 80),
        "memory_mb": random.randint(100, 500),
        "requests_per_minute": random.randint(50, 300),
        "active_connections": random.randint(5, 50),
        "pod_name": os.getenv("HOSTNAME", "local"),
        "timestamp": time.time()
    }

@app.get("/api/info")
def api_info():
    """Informations sur l'API"""
    return {
        "name": "ISP Auto-Scaling Backend",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Root endpoint"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/api/tasks", "method": "GET", "description": "Get all tasks"},
            {"path": "/api/tasks", "method": "POST", "description": "Create task"},
            {"path": "/api/stress", "method": "GET", "description": "Generate CPU load"},
            {"path": "/api/metrics/current", "method": "GET", "description": "Current metrics"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
        "pod": os.getenv("HOSTNAME", "local")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
