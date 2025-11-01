import { useEffect, useState } from "react";
import { fetchConfig, postTestAlert } from "../api/client.js";

export default function Settings() {
  const [config, setConfig] = useState(null);
  const [status, setStatus] = useState({ loading: true, error: null });
  const [alertStatus, setAlertStatus] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const cfg = await fetchConfig();
        setConfig(cfg);
        setStatus({ loading: false, error: null });
      } catch (error) {
        setStatus({ loading: false, error: "Failed to load config" });
      }
    };
    load();
  }, []);

  const sendTestAlert = async () => {
    try {
      setAlertStatus({ loading: true });
      const result = await postTestAlert({});
      setAlertStatus({ loading: false, success: result.dispatched });
    } catch (error) {
      setAlertStatus({ loading: false, error: "Failed to dispatch test alert" });
    }
  };

  return (
    <section className="view">
      {status.error && <div className="card error">{status.error}</div>}
      {status.loading && <div className="card muted">Loading configuration…</div>}

      {!status.loading && !status.error && config && (
        <div className="card">
          <h3>Runtime configuration</h3>
          <dl className="config-grid">
            <dt>DB URL</dt>
            <dd>{config.db_url}</dd>
            <dt>Redis URL</dt>
            <dd>{config.redis_url}</dd>
            <dt>Error rate threshold</dt>
            <dd>{config.alert_error_rate_threshold}</dd>
            <dt>p95 latency threshold</dt>
            <dd>{config.alert_p95_latency_ms} ms</dd>
            <dt>Alert lookback (min)</dt>
            <dd>{config.alert_lookback_min}</dd>
            <dt>Channels</dt>
            <dd>{config.alert_channels.join(", ") || "—"}</dd>
            <dt>Services</dt>
            <dd>{config.services.join(", ") || "—"}</dd>
          </dl>
          <button onClick={sendTestAlert} disabled={alertStatus?.loading}>
            {alertStatus?.loading ? "Sending…" : "Send Test Alert"}
          </button>
          {alertStatus?.success && (
            <div className="muted small">
              Dispatched via:{" "}
              {alertStatus.success.map((item) => item.channel).join(", ") || "none"}
            </div>
          )}
          {alertStatus?.error && <div className="error small">{alertStatus.error}</div>}
        </div>
      )}
    </section>
  );
}

