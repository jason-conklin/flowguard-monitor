import AutoSizer from "react-virtualized-auto-sizer";
import { FixedSizeList as List } from "react-window";

const LEVEL_CLASSES = {
  DEBUG: "badge-debug",
  INFO: "badge-info",
  WARN: "badge-warn",
  ERROR: "badge-error",
  CRITICAL: "badge-critical"
};

export default function LogTable({ logs }) {
  const Row = ({ index, style }) => {
    const log = logs[index];
    return (
      <div className="log-row" style={style}>
        <span className={`badge ${LEVEL_CLASSES[log.level] || ""}`}>{log.level}</span>
        <span className="log-service">{log.service}</span>
        <span className="log-message">{log.message}</span>
        <span className="log-meta">
          {log.latency_ms ? `${log.latency_ms}ms` : "-"} |{" "}
          {log.status_code || "-"}
        </span>
        <time>{new Date(log.ts).toLocaleTimeString()}</time>
      </div>
    );
  };

  return (
    <div className="log-table card">
      <h3>Log Stream</h3>
      <div className="log-header">
        <span>Level</span>
        <span>Service</span>
        <span>Message</span>
        <span>Latency / Status</span>
        <span>Timestamp</span>
      </div>
      <div style={{ height: 400 }}>
        <AutoSizer>
          {({ width, height }) => (
            <List height={height} itemCount={logs.length} itemSize={56} width={width}>
              {Row}
            </List>
          )}
        </AutoSizer>
      </div>
    </div>
  );
}
