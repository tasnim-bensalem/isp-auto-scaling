from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from typing import List
import numpy as np
import os
import time

app = FastAPI(
    title="ISP ML Prediction Service",
    description="Service de prédiction de charge pour auto-scaling intelligent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

class MetricsHistory(BaseModel):
    cpu_values: List[float]
    timestamps: List[float] = []
    horizon_minutes: int = 30

class PredictionResult(BaseModel):
    predicted_cpu: float
    recommended_replicas: int
    confidence: str
    trend: str
    reasoning: str

def cpu_to_replicas(cpu_percent: float) -> int:
    """Convertit % CPU prédit en nombre de replicas recommandé"""
    if cpu_percent < 20:
        return 2
    elif cpu_percent < 40:
        return 3
    elif cpu_percent < 60:
        return 5
    elif cpu_percent < 80:
        return 7
    else:
        return 10

def analyze_trend(values: List[float]) -> str:
    """Détecte la tendance : montante, descendante ou stable"""
    if len(values) < 3:
        return "stable"
    recent = values[-3:]
    older = values[:3]
    avg_recent = sum(recent) / len(recent)
    avg_older = sum(older) / len(older)
    diff = avg_recent - avg_older
    if diff > 10:
        return "montante"
    elif diff < -10:
        return "descendante"
    return "stable"

def simple_predict(values: List[float], horizon: int) -> float:
    """
    Prédiction par régression linéaire simple.
    En production: remplacer par Prophet ou LSTM.
    """
    if len(values) == 0:
        return 50.0
    if len(values) == 1:
        return values[0]

    n = len(values)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n

    numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return y_mean

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    future_x = n + horizon
    predicted = slope * future_x + intercept

    return max(0.0, min(100.0, predicted))

@app.get("/")
def root():
    return {
        "service": "ISP ML Prediction Service",
        "status": "running",
        "version": "1.0.0",
        "pod": os.getenv("HOSTNAME", "local")
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/predict", response_model=PredictionResult)
def predict(data: MetricsHistory):
    """
    Endpoint principal : reçoit historique CPU, retourne prédiction.
    """
    values = data.cpu_values
    horizon = data.horizon_minutes

    predicted_cpu = simple_predict(values, horizon)
    replicas = cpu_to_replicas(predicted_cpu)
    trend = analyze_trend(values) if len(values) >= 3 else "stable"

    if len(values) >= 10:
        confidence = "haute"
    elif len(values) >= 5:
        confidence = "moyenne"
    else:
        confidence = "faible"

    reasoning = (
        f"CPU actuel: {values[-1]:.1f}% | "
        f"Tendance: {trend} | "
        f"CPU prédit dans {horizon}min: {predicted_cpu:.1f}% | "
        f"Replicas recommandés: {replicas}"
    )

    return PredictionResult(
        predicted_cpu=round(predicted_cpu, 2),
        recommended_replicas=replicas,
        confidence=confidence,
        trend=trend,
        reasoning=reasoning
    )

@app.get("/predict/simple")
def predict_simple(current_cpu: float = 50.0, trend: str = "stable"):
    """Prédiction rapide sans historique — pour tests"""
    if trend == "montante":
        predicted = min(100, current_cpu * 1.4)
    elif trend == "descendante":
        predicted = max(0, current_cpu * 0.7)
    else:
        predicted = current_cpu

    replicas = cpu_to_replicas(predicted)
    return {
        "input_cpu": current_cpu,
        "trend": trend,
        "predicted_cpu": round(predicted, 1),
        "recommended_replicas": replicas,
        "pod": os.getenv("HOSTNAME", "local")
    }

@app.get("/api/info")
def info():
    return {
        "endpoints": [
            {"path": "/predict", "method": "POST", "desc": "Prédiction complète avec historique"},
            {"path": "/predict/simple", "method": "GET", "desc": "Prédiction rapide sans historique"},
            {"path": "/health", "method": "GET", "desc": "Health check K8s"},
            {"path": "/metrics", "method": "GET", "desc": "Métriques Prometheus"},
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
