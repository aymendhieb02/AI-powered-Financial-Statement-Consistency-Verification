import { useEffect, useState } from 'react';
import { getHealth, getSettings } from '../api/settings';
import type { BackendSettings, Health } from '../types/api';

export function SettingsPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [settings, setSettings] = useState<BackendSettings | null>(null);
  useEffect(() => { getHealth().then(setHealth).catch(() => undefined); getSettings().then(setSettings).catch(() => undefined); }, []);
  return <section className="space-y-5"><h1 className="text-2xl font-semibold">Settings</h1><div className="grid gap-4 md:grid-cols-2"><div className="rounded-lg border border-audit-line bg-white p-5"><h2 className="font-semibold">Backend health</h2><p>Status: {health?.status ?? 'Unavailable'}</p><p>Storage: {health?.storage_backend ?? '-'}</p></div><div className="rounded-lg border border-audit-line bg-white p-5"><h2 className="font-semibold">Configuration</h2><p>AI: {settings?.ai_enabled ? 'Enabled' : 'Disabled'}</p><p>Ollama model: {settings?.ollama_model ?? '-'}</p><p>MinIO configured: {settings?.minio_configured ? 'Yes' : 'No'}</p></div></div></section>;
}
