import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export const client = axios.create({
  baseURL,
  timeout: 10000
});

export const fetchConfig = async () => {
  const { data } = await client.get("/api/config");
  return data;
};

export const fetchHealth = async () => {
  const { data } = await client.get("/api/health");
  return data;
};

export const fetchLogs = async (params) => {
  const { data } = await client.get("/api/logs", { params });
  return data.items;
};

export const fetchMetrics = async (params) => {
  const { data } = await client.get("/api/metrics", { params });
  return data.items;
};

export const fetchKpis = async (params) => {
  const { data } = await client.get("/api/kpis", { params });
  return data;
};

export const fetchAlerts = async (params) => {
  const { data } = await client.get("/api/alerts", { params });
  return data.items;
};

export const postTestAlert = async (payload) => {
  const { data } = await client.post("/api/test-alert", payload);
  return data;
};

