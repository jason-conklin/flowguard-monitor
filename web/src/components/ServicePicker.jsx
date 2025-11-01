export default function ServicePicker({ services, value, onChange }) {
  if (!services.length) {
    return <span className="muted">No services configured</span>;
  }
  return (
    <select value={value} onChange={(event) => onChange(event.target.value)}>
      {services.map((service) => (
        <option key={service} value={service}>
          {service}
        </option>
      ))}
    </select>
  );
}

