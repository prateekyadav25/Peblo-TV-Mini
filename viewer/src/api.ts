const BASE_URL = import.meta.env.VITE_API_URL || '';

// We now fetch directly from the statically served JSON file, bypassing the FastAPI backend logic!
export async function fetchCatalogue() {
  const res = await fetch(`${BASE_URL}/api/storage/catalogue/live.json`);
  if (!res.ok) throw new Error('Failed to fetch catalogue');
  return res.json();
}

export async function searchCatalogue(params: Record<string, string>) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE_URL}/api/catalog/search?${qs}`);
  if (!res.ok) throw new Error('Search failed');
  return res.json();
}
