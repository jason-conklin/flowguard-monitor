export default function TimeRangePicker({ value, onChange }) {
  return (
    <select value={value} onChange={(event) => onChange(event.target.value)}>
      <option value="1h">Last 1h</option>
      <option value="6h">Last 6h</option>
      <option value="24h">Last 24h</option>
      <option value="3d">Last 3d</option>
    </select>
  );
}

