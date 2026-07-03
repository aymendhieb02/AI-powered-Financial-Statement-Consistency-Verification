import { Database, HardDrive, Moon, Server, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';
import { getSettings } from '../api/settings';
import type { BackendSettings } from '../types/api';
import { PageHeader } from '../components/ui/Cards';
import { Badge } from '../components/ui/Badge';
import { Card, CardContent } from '../components/ui/card';

const sections = [
  { title: 'General', icon: Server, text: 'Workspace defaults, company profile, tolerances' },
  { title: 'Storage', icon: HardDrive, text: 'Local JSON now, MinIO-ready adapter configuration' },
  { title: 'AI', icon: Sparkles, text: 'Semantic explanations only; numerical checks stay deterministic' },
  { title: 'Theme', icon: Moon, text: 'Light, dark, and high-contrast audit modes' },
];

export function SettingsPage() {
  const [settings, setSettings] = useState<BackendSettings | null>(null);
  useEffect(() => { getSettings().then(setSettings).catch(() => undefined); }, []);
  return (
    <section className="space-y-6">
      <PageHeader eyebrow="Administration" title="Settings" description="Operational settings are grouped for future SaaS deployment while preserving the local modular monolith." />
      <div className="grid gap-4 md:grid-cols-2">
        {sections.map((section) => {
          const Icon = section.icon;
          return (
            <Card key={section.title}>
              <CardContent className="p-5">
                <div className="flex items-start gap-3">
                  <div className="rounded-md bg-slate-100 p-2 text-slate-600"><Icon size={18} /></div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-950">{section.title}</h3>
                    <p className="mt-1 text-sm text-slate-500">{section.text}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      <Card>
        <CardContent className="p-5">
          <div className="section-title mb-4">System information</div>
          <div className="grid gap-3 text-sm md:grid-cols-4">
            <div>
              <div className="text-slate-500">Storage backend</div>
              <Badge tone="success"><Database size={12} /> {settings?.storage_backend || 'local'}</Badge>
            </div>
            <div>
              <div className="text-slate-500">MinIO</div>
              <Badge tone={settings?.minio_configured ? 'success' : 'neutral'}>{settings?.minio_configured ? 'Configured' : 'Not configured'}</Badge>
            </div>
            <div>
              <div className="text-slate-500">AI</div>
              <Badge tone={settings?.ai_enabled ? 'success' : 'neutral'}>{settings?.ai_enabled ? 'Enabled' : 'Disabled'}</Badge>
            </div>
            <div>
              <div className="text-slate-500">Model</div>
              <span className="font-medium text-slate-900">{settings?.ollama_model || 'n/a'}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
