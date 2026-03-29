const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function fetchEditais(filters = {}) {
  const params = new URLSearchParams();
  if (filters.fonte) params.set("fonte", filters.fonte);
  if (filters.min_score != null && filters.min_score !== "")
    params.set("min_score", filters.min_score);
  const res = await fetch(`${BASE}/editais?${params}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchEdital(id) {
  const res = await fetch(`${BASE}/editais/${id}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchEvaluationSummary() {
  const res = await fetch(`${BASE}/evaluation/summary`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function triggerPipeline() {
  const res = await fetch(`${BASE}/pipeline/run`, { method: "POST" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
