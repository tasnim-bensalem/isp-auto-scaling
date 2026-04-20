import requests
import time
import os
from datetime import datetime

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090")
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml-prediction-service.default.svc.cluster.local:80")
HPA_NAME = os.getenv("HPA_NAME", "backend-api-hpa")
NAMESPACE = os.getenv("NAMESPACE", "default")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
MIN_REPLICAS = int(os.getenv("MIN_REPLICAS", "2"))
MAX_REPLICAS = int(os.getenv("MAX_REPLICAS", "10"))

K8S_API = "https://kubernetes.default.svc"
SA_TOKEN_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/token"
SA_CA_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)

def get_k8s_token():
    try:
        with open(SA_TOKEN_PATH) as f:
            return f.read().strip()
    except Exception as e:
        log(f"Erreur token: {e}", "ERROR")
        return None

def get_cpu_history():
    try:
        query = 'avg(rate(container_cpu_usage_seconds_total{pod=~"backend-api.*"}[2m])) * 100'
        url = f"{PROMETHEUS_URL}/api/v1/query_range"
        params = {"query": query, "start": f"{int(time.time()) - 1800}", "end": f"{int(time.time())}", "step": "60"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data["status"] == "success" and data["data"]["result"]:
            values = [float(v[1]) for v in data["data"]["result"][0]["values"]]
            log(f"Prometheus: {len(values)} valeurs recuperees, CPU actuel: {values[-1]:.1f}%")
            return values
        log("Prometheus: pas de donnees", "WARN")
        return [50.0]
    except Exception as e:
        log(f"Erreur Prometheus: {e}", "ERROR")
        return [50.0]

def get_ml_prediction(cpu_values):
    try:
        payload = {"cpu_values": cpu_values, "horizon_minutes": 30}
        response = requests.post(f"{ML_SERVICE_URL}/predict", json=payload, timeout=10)
        result = response.json()
        log(f"ML Prediction: CPU predit={result['predicted_cpu']:.1f}% | Replicas recommandes={result['recommended_replicas']} | Tendance={result['trend']} | Confiance={result['confidence']}")
        return result
    except Exception as e:
        log(f"Erreur ML Service: {e}", "ERROR")
        return {"recommended_replicas": MIN_REPLICAS, "predicted_cpu": 0, "trend": "unknown", "confidence": "faible"}

def get_current_replicas():
    try:
        token = get_k8s_token()
        url = f"{K8S_API}/apis/autoscaling/v2/namespaces/{NAMESPACE}/horizontalpodautoscalers/{HPA_NAME}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, verify=SA_CA_PATH, timeout=10)
        data = response.json()
        replicas = data.get("status", {}).get("currentReplicas", MIN_REPLICAS)
        log(f"Replicas actuels: {replicas}")
        return replicas
    except Exception as e:
        log(f"Erreur get replicas: {e}", "ERROR")
        return MIN_REPLICAS

def apply_scaling(recommended_replicas):
    try:
        recommended = max(MIN_REPLICAS, min(MAX_REPLICAS, recommended_replicas))
        token = get_k8s_token()
        url = f"{K8S_API}/apis/autoscaling/v2/namespaces/{NAMESPACE}/horizontalpodautoscalers/{HPA_NAME}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/merge-patch+json"}
        patch = {"spec": {"minReplicas": recommended}}
        response = requests.patch(url, headers=headers, json=patch, verify=SA_CA_PATH, timeout=10)
        if response.status_code in [200, 201]:
            log(f"Scaling applique: minReplicas={recommended}", "SUCCESS")
            return True
        log(f"Erreur patch HPA: {response.status_code}", "ERROR")
        return False
    except Exception as e:
        log(f"Erreur scaling: {e}", "ERROR")
        return False

def control_loop():
    log("Auto-Scaling Controller demarre")
    log(f"Intervalle: {CHECK_INTERVAL}s | Min: {MIN_REPLICAS} | Max: {MAX_REPLICAS}")
    log("-" * 60)
    cycle = 0
    while True:
        cycle += 1
        log(f"=== Cycle #{cycle} ===")
        cpu_history = get_cpu_history()
        prediction = get_ml_prediction(cpu_history)
        current = get_current_replicas()
        recommended = prediction["recommended_replicas"]
        if recommended != current:
            log(f"Decision: {current} -> {recommended} pods")
            apply_scaling(recommended)
        else:
            log(f"Pas de changement: {current} pods suffisants")
        log(f"Prochain cycle dans {CHECK_INTERVAL}s...")
        log("-" * 60)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    control_loop()
