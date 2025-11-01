export default function AlertList({ alerts }) {
  if (!alerts.length) {
    return <div className="card muted">No recent alerts</div>;
  }

  return (
    <div className="alert-list card">
      <h3>Recent Alerts</h3>
      <ul>
        {alerts.map((alert) => (
          <li key={alert.id} className={`alert-item ${alert.severity}`}>
            <div>
              <strong>{alert.service}</strong> • {alert.channel}
            </div>
            <div>{alert.message}</div>
            <time>{new Date(alert.ts).toLocaleString()}</time>
          </li>
        ))}
      </ul>
    </div>
  );
}

