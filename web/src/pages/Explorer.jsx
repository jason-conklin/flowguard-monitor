import { useEffect, useState } from "react";
import ServicePicker from "../components/ServicePicker.jsx";
import TimeRangePicker from "../components/TimeRangePicker.jsx";
import LogTable from "../components/LogTable.jsx";
import { fetchConfig, fetchLogs } from "../api/client.js";

const LEVELS = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"];

export default function Explorer() {
  const [services, setServices] = useState([]);
  const [service, setService] = useState("");
  const [range, setRange] = useState("1h");
  const [level, setLevel] = useState("");
  const [query, setQuery] = useState("");
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState({ loading: true, error: null });

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const cfg = await fetchConfig();
        setServices(cfg.services || []);
        if (!service && (cfg.services || []).length) {
          setService(cfg.services[0]);
        }
      } catch (error) {
        setStatus({ loading: false, error: "Failed to load config" });
      }
    };
    loadConfig();
  }, []);

  useEffect(() => {
    const loadLogs = async () => {
      if (!service) {
        setStatus({ loading: false, error: null });
        return;
      }
      setStatus({ loading: true, error: null });
      try {
        const items = await fetchLogs({
          service,
          range,
          level: level || undefined,
          q: query || undefined
        });
        setLogs(items);
        setStatus({ loading: false, error: null });
      } catch (error) {
        setStatus({ loading: false, error: "Failed to load logs" });
      }
    };
    loadLogs();
  }, [service, range, level, query]);

  return (
    <section className="view">
      <div className="controls">
        <ServicePicker services={services} value={service} onChange={setService} />
        <TimeRangePicker value={range} onChange={setRange} />
        <select value={level} onChange={(event) => setLevel(event.target.value)}>
          <option value="">All levels</option>
          {LEVELS.map((lvl) => (
            <option key={lvl} value={lvl}>
              {lvl}
            </option>
          ))}
        </select>
        <input
          type="search"
          placeholder="Search logs"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>

      {status.error && <div className="card error">{status.error}</div>}
      {status.loading && <div className="card muted">Loading logs…</div>}

      {!status.loading && !status.error && <LogTable logs={logs} />}
    </section>
  );
}

