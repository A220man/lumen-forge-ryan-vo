import { useEffect, useState } from "react";

interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

interface HealthState {
  data: HealthResponse | null;
  loading: boolean;
  error: string | null;
}

function App() {
  const [health, setHealth] = useState<HealthState>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    async function fetchHealth() {
      try {
        const response = await fetch("/api/health");
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        setHealth({ data, loading: false, error: null });
      } catch (err) {
        setHealth({
          data: null,
          loading: false,
          error: err instanceof Error ? err.message : "Unknown error",
        });
      }
    }

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app">
      <header>
        <h1>lumen-forge-ryan-vo</h1>
        <span>AI/ML Developer Tools</span>
      </header>
      <main>
        <div className="health-card">
          <h2>Service Health</h2>
          {health.loading && <p>Loading...</p>}
          {health.error && (
            <p className="status-error">Error: {health.error}</p>
          )}
          {health.data && (
            <div>
              <div className="info-row">
                <span className="info-label">Status</span>
                <span className="info-value status-ok">{health.data.status}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Service</span>
                <span className="info-value">{health.data.service}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Version</span>
                <span className="info-value">{health.data.version}</span>
              </div>
            </div>
          )}
        </div>
      </main>
      <footer>
        lumen-forge-ryan-vo &copy; 2025 Ryan Vo{" "}
        <span>{"ryandtvo@gmail.com"}</span>
      </footer>
    </div>
  );
}

export default App;