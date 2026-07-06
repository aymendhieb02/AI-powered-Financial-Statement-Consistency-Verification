import { NavLink, useParams } from 'react-router-dom';

const tabs = [
  { slug: '', label: 'Overview' },
  { slug: 'documents', label: 'Documents' },
  { slug: 'verification', label: 'Verification' },
  { slug: 'anomalies', label: 'Anomalies' },
  { slug: 'reports', label: 'Reports' },
  { slug: 'rules', label: 'Rules' },
  { slug: 'evidence', label: 'Evidence' },
  { slug: 'history', label: 'History' },
];

export function ProjectWorkspaceNav() {
  const { projectId } = useParams();
  if (!projectId) return null;

  return (
    <div className="flex gap-1 overflow-x-auto border-b border-slate-200">
      {tabs.map((tab) => (
        <NavLink
          key={tab.slug || 'overview'}
          to={tab.slug ? `/projects/${projectId}/${tab.slug}` : `/projects/${projectId}`}
          end={!tab.slug}
          className={({ isActive }) =>
            'whitespace-nowrap px-3 py-2 text-sm font-medium transition ' +
            (isActive ? 'border-b-2 border-slate-950 text-slate-950' : 'text-slate-500 hover:text-slate-900')
          }
        >
          {tab.label}
        </NavLink>
      ))}
    </div>
  );
}
