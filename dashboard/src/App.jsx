import { useCallback, useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

function App() {
  const [gateway, setGateway] = useState("checking");
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [latency, setLatency] = useState("--");
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [healthResponse, usersResponse] = await Promise.all([
        fetch(`${API_URL}/health`),
        fetch(`${API_URL}/api/users`),
      ]);

      if (!healthResponse.ok || !usersResponse.ok) {
        throw new Error("Gateway returned an unsuccessful response");
      }

      const healthData = await healthResponse.json();
      const usersData = await usersResponse.json();

      setGateway(healthData.status);
      setUsers(usersData.users || []);
      setLatency(
        usersResponse.headers.get("X-GateFlow-Latency") || "--"
      );

    } catch (err) {
      setGateway("offline");
      setUsers([]);
      setLatency("--");
      setError(err.message);

    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return (
    <div className="dashboard">

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">G</div>
          <span>GateFlow</span>
        </div>

        <p className="sidebar-label">WORKSPACE</p>

        <nav>
          <a className="nav-item active" href="#overview">
            <span>◈</span> Overview
          </a>

          <a className="nav-item" href="#services">
            <span>▣</span> Services
          </a>

          <a className="nav-item" href="#requests">
            <span>⇄</span> Requests
          </a>
        </nav>

        <div className="sidebar-bottom">
          <span className="status-dot" />
          Development Environment
        </div>
      </aside>

      <main className="main-content">

        <header className="topbar">
          <div>
            <p className="breadcrumb">Workspace / Overview</p>
            <h1>Gateway Overview</h1>
          </div>

          <button
            className="refresh-button"
            onClick={loadDashboard}
            disabled={loading}
          >
            ↻ {loading ? "Refreshing..." : "Refresh"}
          </button>
        </header>

        <section className="welcome">
          <div>
            <span className="eyebrow">GATEFLOW CONTROL PLANE</span>
            <h2>Your infrastructure, one gateway.</h2>
            <p>
              Monitor services and manage your API traffic
              from one centralized platform.
            </p>
          </div>

          <div className="welcome-symbol">G</div>
        </section>

        {error && (
          <div className="error-banner">
            Gateway connection failed: {error}
          </div>
        )}

        <section id="overview" className="stats-grid">

          <StatCard
            label="Gateway Status"
            value={
              gateway === "healthy"
                ? "Online"
                : gateway === "offline"
                  ? "Offline"
                  : "Checking"
            }
            status={gateway === "healthy"}
            icon="◉"
          />

          <StatCard
            label="Registered Services"
            value="1"
            icon="▣"
          />

          <StatCard
            label="Loaded Users"
            value={users.length}
            icon="♙"
          />

          <StatCard
            label="Gateway Latency"
            value={latency}
            icon="◷"
          />

        </section>

        <section id="services" className="panel">

          <div className="panel-header">
            <div>
              <h3>Backend Services</h3>
              <p>Services connected to GateFlow</p>
            </div>

            <span className="tag">MILESTONE 1</span>
          </div>

          <div className="service-row">

            <div className="service-info">
              <div className="service-icon">U</div>

              <div>
                <h4>User Service</h4>
                <p>FastAPI · Port 8002</p>
              </div>
            </div>

            <span
              className={`service-status ${
                gateway === "healthy" ? "online" : "offline"
              }`}
            >
              <span className="status-dot" />
              {gateway === "healthy" ? "Connected" : "Unavailable"}
            </span>

          </div>

          <div className="service-endpoint">
            <span>Gateway endpoint</span>
            <code>GET /api/users</code>
          </div>

        </section>

        <section id="requests" className="panel">

          <div className="panel-header">
            <div>
              <h3>Live API Response</h3>
              <p>Data retrieved through your gateway</p>
            </div>

            <span className="tag success-tag">HTTP</span>
          </div>

          {loading ? (
            <p className="empty-state">Loading API data...</p>
          ) : users.length > 0 ? (
            <div className="user-list">
              {users.map((user) => (
                <div className="user-row" key={user.id}>
                  <div className="avatar">
                    {user.name.charAt(0)}
                  </div>

                  <div>
                    <strong>{user.name}</strong>
                    <p>{user.role}</p>
                  </div>

                  <span className="user-id">
                    ID #{user.id}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state">
              No data available. Check your gateway connection.
            </p>
          )}

        </section>

        <footer>
          GateFlow <span>v0.1.0</span> · Built for developers
        </footer>

      </main>
    </div>
  );
}


function StatCard({ label, value, icon, status }) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <span>{label}</span>
        <span className="stat-icon">{icon}</span>
      </div>

      <h2>{value}</h2>

      {status !== undefined && (
        <p className="stat-description">
          <span className="status-dot" />
          System health check
        </p>
      )}
    </div>
  );
}


export default App;
