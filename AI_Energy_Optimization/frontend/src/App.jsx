import { useState, useEffect } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'
import './App.css'

const API_BASE = "http://localhost:8000/api"

function App() {
  const [buildings, setBuildings] = useState([])
  const [selectedBuilding, setSelectedBuilding] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)

  // Simulation State
  const [simParams, setSimParams] = useState({
    occupancy_level: 'Low',
    temperature: 24,
    humidity: 50
  })
  const [simResult, setSimResult] = useState(null)
  const [predictionResult, setPredictionResult] = useState(null)

  // Chat State
  const [chatOpen, setChatOpen] = useState(false)
  const [messages, setMessages] = useState([
    { sender: 'ai', text: 'Hello! I am Voltix AI. How can I help you save energy today?' }
  ])
  const [input, setInput] = useState('')

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { sender: 'user', text: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')

    try {
      const context = dashboardData ? {
        energy_kwh: dashboardData.current_status.energy_kwh,
        occupancy: dashboardData.current_status.occupancy,
        temperature: dashboardData.current_status.temperature,
        building_type: dashboardData.building_meta.building_type
      } : {}

      const res = await axios.post(`${API_BASE}/chat`, {
        message: userMsg.text,
        context: context
      })

      setMessages(prev => [...prev, { sender: 'ai', text: res.data.response }])
    } catch (err) {
      console.error(err)
      setMessages(prev => [...prev, { sender: 'ai', text: 'Sorry, I encountered an error connecting to Gemini.' }])
    }
  }

  // Load Buildings
  useEffect(() => {
    axios.get(`${API_BASE}/buildings`)
      .then(res => {
        setBuildings(res.data)
        if (res.data.length > 0) setSelectedBuilding(res.data[0].building_id)
      })
      .catch(err => console.error(err))
  }, [])

  // Load Data
  useEffect(() => {
    if (!selectedBuilding) return;
    setLoading(true)
    axios.get(`${API_BASE}/dashboard-data`, { params: { building_id: selectedBuilding } })
      .then(res => {
        setDashboardData(res.data)
        setSimParams({
          occupancy_level: res.data.current_status.occupancy,
          temperature: res.data.current_status.temperature,
          humidity: res.data.current_status.humidity
        })
        setSimResult(null)
        setLoading(false)
      })
      .catch(err => { console.error(err); setLoading(false); })
  }, [selectedBuilding])

  const handleSimulate = async () => {
    if (!dashboardData) return;
    const meta = dashboardData.building_meta
    const payload = {
      building_type: meta.building_type,
      area_sq_m: meta.area_sq_m,
      temperature: parseFloat(simParams.temperature),
      humidity: parseFloat(simParams.humidity),
      occupancy_level: simParams.occupancy_level,
      hour: 14,
      day_of_week: 2
    }
    try {
      const res = await axios.post(`${API_BASE}/simulate`, payload)
      setSimResult(res.data)
    } catch (err) {
      console.error("Simulation error", err)
    }
  }

  if (!selectedBuilding || loading) return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-gradient)' }}>
      <h2 style={{ color: 'var(--accent-color)' }}>Initializing Voltix AI...</h2>
    </div>
  )

  if (!dashboardData || !dashboardData.current_status) return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-gradient)' }}>
      <h2 style={{ color: 'var(--accent-color)' }}>Initializing Voltix AI...</h2>
      <p style={{ marginLeft: '1rem', color: '#fff' }}>Connecting to backend...</p>
    </div>
  )

  const { current_status, chart_data, recommendations, total_kwh_month, co2_emissions, ai_confidence, building_meta } = dashboardData

  return (
    <>
      <header>
        <div className="brand">
          <span style={{ fontSize: '2rem' }}>⚡</span>
          <h1>Voltix AI</h1>
        </div>
        <div className="controls">
          <select value={selectedBuilding} onChange={(e) => setSelectedBuilding(e.target.value)}>
            {buildings.map(b => (
              <option key={b.building_id} value={b.building_id}>
                {b.building_id} • {b.building_type}
              </option>
            ))}
          </select>
        </div>
      </header>

      <div className="container">
        {/* KPI Grid */}
        <div className="dashboard-grid">
          <div className="kpi-card">
            <span className="kpi-title">Current Consumption</span>
            <span className="kpi-value">{current_status.energy_kwh} <span style={{ fontSize: '1rem', opacity: 0.6 }}>kWh</span></span>
          </div>
          <div className="kpi-card">
            <span className="kpi-title">Occupancy Level</span>
            <span className="kpi-value" style={{ color: current_status.occupancy === 'High' ? 'var(--warning)' : 'var(--text-primary)' }}>
              {current_status.occupancy}
            </span>
          </div>
          <div className="kpi-card">
            <span className="kpi-title">Avg Temperature</span>
            <span className="kpi-value">{current_status.temperature}°C</span>
          </div>
          <div className="kpi-card">
            <span className="kpi-title">Humidity</span>
            <span className="kpi-value">{current_status.humidity}%</span>
          </div>
        </div>

        <div className="content-split">
          <div className="left-col">
            {/* Chart */}
            <div className="panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2>📈 Energy Forecast</h2>
                <div style={{ background: '#f1f5f9', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.85rem' }}>
                  AI Confidence: <strong>{dashboardData.ai_confidence}%</strong>
                </div>
              </div>
              <div style={{ width: '100%', height: 400 }}>
                <ResponsiveContainer>
                  <AreaChart data={chart_data}>
                    <defs>
                      <linearGradient id="colorPv" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={t => {
                        const d = new Date(t);
                        return `${d.getDate()} ${d.toLocaleString('default', { month: 'short' })} ${d.getHours()}:00`;
                      }}
                      minTickGap={50}
                      tick={{ fill: '#64748b', fontSize: 11 }}
                    />
                    <YAxis axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }} labelFormatter={t => new Date(t).toLocaleString()} />
                    <Legend wrapperStyle={{ paddingTop: '1rem' }} />
                    <Area type="monotone" dataKey="energy_kwh" stroke="#3b82f6" fillOpacity={1} fill="url(#colorPv)" strokeWidth={3} name="Actual Usage" />
                    <Line type="monotone" dataKey="predicted_kwh" stroke="#f59e0b" strokeWidth={3} dot={false} strokeDasharray="5 5" name="AI Prediction" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Recommendations */}
            <div className="panel">
              <h2>💡 Optimization Insights</h2>
              {recommendations.map((rec, i) => (
                <div key={i} className="rec-item">
                  <div className="rec-icon">⚡</div>
                  <div className="rec-content">
                    <span className="rec-title">{rec.action}</span>
                    <div className="rec-meta">Impact: <span style={{ color: 'var(--success)', fontWeight: '700' }}>{rec.impact}</span> • Comfort: {rec.comfort}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="right-col">
            {/* Simulator */}
            <div className="panel simulator-container">
              <h2>🎮 Interactive Simulator</h2>
              <p style={{ marginBottom: '1.5rem', opacity: 0.7, fontSize: '0.9rem' }}>Adjust parameters to see AI-predicted impact on peak hour consumption.</p>

              <div className="simulator-form">
                <div className="form-group">
                  <label>Occupancy Mode</label>
                  <select value={simParams.occupancy_level} onChange={e => setSimParams({ ...simParams, occupancy_level: e.target.value })}>
                    <option value="Low">Low (Eco Mode)</option>
                    <option value="Medium">Medium (Balanced)</option>
                    <option value="High">High (Performance)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Setpoint Temperature (°C)</label>
                  <input type="number" value={simParams.temperature} onChange={e => setSimParams({ ...simParams, temperature: e.target.value })} />
                </div>
                <button className="btn-simulate" onClick={handleSimulate}>
                  Run Scenario
                </button>
              </div>

              {simResult && (
                <div className="sim-result">
                  <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Predicted Outcome</div>
                  <div style={{ fontSize: '2.5rem', fontWeight: '800', color: 'var(--accent-color)' }}>
                    {simResult.predicted_kwh} <span style={{ fontSize: '1.2rem', opacity: 0.7 }}>kWh</span>
                  </div>
                </div>
              )}
            </div>

            {/* Future Predictor */}
            <div className="panel simulator-container" style={{ marginTop: '1.5rem', borderLeft: '4px solid var(--accent-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2>🔮 Future Crystal Ball</h2>
                {predictionResult && (
                  <button onClick={() => {
                    // Simple print-to-pdf via browser print for robustness
                    const printContent = document.getElementById('prediction-card');
                    const win = window.open('', '', 'height=600,width=800');
                    win.document.write('<html><head><title>Voltix Future Forecast</title>');
                    win.document.write('<style>body{font-family:sans-serif; padding:2rem;} .card{border:1px solid #ccc; padding:2rem; border-radius:10px; background:#f9fafb;} h2{color:#0891b2;} .metric{font-size:1.5rem; font-weight:bold; color:#111827;} .label{color:#6b7280; font-size:0.9rem;} .rec-list{margin-top:1rem; padding-left:1.5rem;} li{margin-bottom:0.5rem;}</style>');
                    win.document.write('</head><body>');
                    win.document.write(printContent.innerHTML);
                    win.document.write('</body></html>');
                    win.document.close();
                    win.print();
                  }} style={{ background: 'none', border: '1px solid var(--accent-color)', color: 'var(--accent-color)', padding: '0.2rem 0.6rem', fontSize: '0.8rem', borderRadius: '4px', cursor: 'pointer' }}>
                    📥 Save PDF
                  </button>
                )}
              </div>
              <p style={{ marginBottom: '1rem', opacity: 0.7, fontSize: '0.9rem' }}>Pick a future date & time to forecast demand.</p>

              <div className="simulator-form" style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                <input type="datetime-local" id="future-picker" style={{ flex: 1, padding: '0.5rem', borderRadius: '6px', border: '1px solid #ddd' }} />
                <button className="btn-simulate" onClick={async () => {
                  const val = document.getElementById('future-picker').value;
                  if (!val) return;
                  try {
                    const res = await axios.post(`${API_BASE}/predict-future`, {
                      building_id: selectedBuilding,
                      target_time: val
                    });
                    setPredictionResult(res.data);
                  } catch (e) { console.error(e); alert("Prediction Failed"); }
                }}>Predict</button>
              </div>

              {predictionResult && (
                <div id="prediction-card" className="sim-result" style={{ textAlign: 'left', animation: 'fadeIn 0.5s' }}>
                  <h3 style={{ marginTop: 0, color: 'var(--accent-color)' }}>📊 Forecast Result</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                    <div>
                      <div className="label">Predicted Demand</div>
                      <div className="metric">{predictionResult.predicted_kwh} kWh</div>
                    </div>
                    <div>
                      <div className="label">Est. Temperature</div>
                      <div className="metric">{predictionResult.estimated_temp}°C</div>
                    </div>
                  </div>
                  <div className="label">Recommendations:</div>
                  <ul className="rec-list">
                    {predictionResult.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                    {predictionResult.recommendations.length === 0 && <li>✅ System operating efficiently.</li>}
                  </ul>
                  <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: '#6b7280', borderTop: '1px solid #eee', paddingTop: '0.5rem' }}>
                    Generated by Voltix AI for Building {selectedBuilding}
                  </div>
                </div>
              )}
            </div>

            {/* Sustainability */}
            <div className="panel sus-card">
              <h2>🌱 Sustainability Index</h2>
              <div className="sus-metric">
                <span className="sus-label">Monthly Energy</span>
                <span className="sus-val">{total_kwh_month} kWh</span>
              </div>
              <div className="sus-metric">
                <span className="sus-label">Carbon Footprint</span>
                <span className="sus-val">{co2_emissions} kg</span>
              </div>
              <div style={{ marginTop: '1.5rem', fontSize: '0.9rem', opacity: 0.9, textAlign: 'center' }}>
                You've helped offset the carbon equivalent of driving <strong>{(co2_emissions / 0.12).toFixed(0)} km</strong>!
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Component */}
      <button className="chat-fab" onClick={() => setChatOpen(!chatOpen)}>
        💬
      </button>

      {chatOpen && (
        <div className="chat-window">
          <div className="chat-header">
            <span>Voltix Assistant</span>
            <span style={{ cursor: 'pointer' }} onClick={() => setChatOpen(false)}>×</span>
          </div>
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`message ${m.sender}`}>
                {m.text}
              </div>
            ))}
          </div>
          <div className="chat-input-area">
            <input
              type="text"
              placeholder="Ask about energy..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyPress={e => e.key === 'Enter' && sendMessage()}
            />
            <button onClick={sendMessage}>➤</button>
          </div>
        </div>
      )}
    </>
  )
}

export default App
