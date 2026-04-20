import React, { useState, useEffect, useRef } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const BACKEND_URL = 'http://localhost:8000';
const ML_URL = 'http://localhost:8001';

function App() {
  const [pods, setPods] = useState(2);
  const [cpuData, setCpuData] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [mlStatus, setMlStatus] = useState('checking');
  const [decisions, setDecisions] = useState([]);
  const [currentCpu, setCurrentCpu] = useState(0);
  const cpuRef = useRef([]);

  const fetchData = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/metrics/current`, { timeout: 5000 });
      const metrics = res.data;
      setCurrentCpu(metrics.cpu_percent);
      setBackendStatus('online');
      const newPoint = {
        time: new Date().toLocaleTimeString(),
        cpu: metrics.cpu_percent,
      };
      setCpuData(prev => {
        const updated = [...prev, newPoint].slice(-20);
        cpuRef.current = updated.map(d => d.cpu);
        return updated;
      });
      try {
        const history = cpuRef.current;
        if (history.length >= 3) {
          const mlRes = await axios.post(`${ML_URL}/predict`, {
            cpu_values: history,
            horizon_minutes: 30
          }, { timeout: 5000 });
          setPrediction(mlRes.data);
          setMlStatus('online');
          setPods(prev => {
            if (mlRes.data.recommended_replicas !== prev) {
              setDecisions(d => [{
                time: new Date().toLocaleTimeString(),
                from: prev,
                to: mlRes.data.recommended_replicas,
                cpu: mlRes.data.predicted_cpu,
                trend: mlRes.data.trend
              }, ...d].slice(0, 10));
            }
            return mlRes.data.recommended_replicas;
          });
        }
      } catch { setMlStatus('offline'); }
    } catch { setBackendStatus('offline'); }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const Badge = ({ status, label }) => (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '4px 12px', borderRadius: 99, fontSize: 12, fontWeight: 500,
      background: status === 'online' ? '#d1fae5' : '#fee2e2',
      color: status === 'online' ? '#065f46' : '#991b1b'
    }}>
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: status === 'online' ? '#10b981' : '#ef4444' }}/>
      {label}: {status}
    </span>
  );

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', color: 'white', fontFamily: 'system-ui, sans-serif', padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>🚀 Auto-Scaling Dashboard</h1>
        <p style={{ color: '#94a3b8', fontSize: 14, margin: '4px 0 12px' }}>ISP Projet — Kubernetes + ML Prédictif</p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <Badge status={backendStatus} label="Backend API" />
          <Badge status={mlStatus} label="ML Service" />
          <Badge status="online" label="Controller" />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Pods actifs', value: pods, color: '#3b82f6' },
          { label: 'CPU actuel', value: `${currentCpu}%`, color: currentCpu > 70 ? '#ef4444' : '#10b981' },
          { label: 'CPU prédit 30min', value: prediction ? `${prediction.predicted_cpu}%` : '...', color: '#8b5cf6' },
          { label: 'Tendance', value: prediction ? prediction.trend : '...', color: '#f59e0b' },
          { label: 'Confiance ML', value: prediction ? prediction.confidence : '...', color: '#0ea5e9' },
        ].map((card, i) => (
          <div key={i} style={{ background: '#1e293b', borderRadius: 12, padding: 16, border: `1px solid ${card.color}33` }}>
            <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8 }}>{card.label}</div>
            <div style={{ fontSize: 26, fontWeight: 700, color: card.color }}>{card.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
        <div style={{ background: '#1e293b', borderRadius: 12, padding: 20 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: '#e2e8f0' }}>📈 CPU Usage temps réel</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={cpuData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} interval="preserveStartEnd" />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748b' }} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }} />
              <Area type="monotone" dataKey="cpu" stroke="#3b82f6" fill="#3b82f633" strokeWidth={2} name="CPU %" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div style={{ background: '#1e293b', borderRadius: 12, padding: 20 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: '#e2e8f0' }}>🐳 Pods recommandés par ML</h3>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 80, fontWeight: 800, color: '#3b82f6', lineHeight: 1 }}>{pods}</div>
              <div style={{ fontSize: 14, color: '#94a3b8', marginTop: 8 }}>pods recommandés</div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>min: 2 — max: 10</div>
              {prediction && (
                <div style={{
                  marginTop: 12, padding: '4px 14px', borderRadius: 99, fontSize: 12, fontWeight: 500,
                  display: 'inline-block',
                  background: prediction.trend === 'montante' ? '#fee2e2' : prediction.trend === 'descendante' ? '#d1fae5' : '#fef3c7',
                  color: prediction.trend === 'montante' ? '#991b1b' : prediction.trend === 'descendante' ? '#065f46' : '#92400e'
                }}>Tendance {prediction.trend}</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {prediction && (
        <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, marginBottom: 24, border: '1px solid #8b5cf633' }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: '#e2e8f0' }}>🤖 Dernière prédiction ML</h3>
          <div style={{ fontSize: 13, color: '#94a3b8', fontFamily: 'monospace', background: '#0f172a', padding: 12, borderRadius: 8 }}>
            {prediction.reasoning}
          </div>
        </div>
      )}

      <div style={{ background: '#1e293b', borderRadius: 12, padding: 20 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: '#e2e8f0' }}>📋 Historique des décisions</h3>
        {decisions.length === 0 ? (
          <div style={{ color: '#64748b', fontSize: 13 }}>En attente de décisions...</div>
        ) : decisions.map((d, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 12px', borderRadius: 8, background: '#0f172a', fontSize: 13, marginBottom: 6 }}>
            <span style={{ color: '#64748b', minWidth: 70 }}>{d.time}</span>
            <span style={{ color: '#94a3b8' }}>{d.from} pods</span>
            <span style={{ color: '#3b82f6' }}>→</span>
            <span style={{ color: 'white', fontWeight: 600 }}>{d.to} pods</span>
            <span style={{ color: '#64748b' }}>CPU prédit: {d.cpu}%</span>
            <span style={{ marginLeft: 'auto', padding: '2px 8px', borderRadius: 99, fontSize: 11,
              background: d.trend === 'montante' ? '#fee2e2' : '#d1fae5',
              color: d.trend === 'montante' ? '#991b1b' : '#065f46'
            }}>{d.trend}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
