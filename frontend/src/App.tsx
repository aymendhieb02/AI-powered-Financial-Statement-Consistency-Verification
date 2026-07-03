import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { AnomaliesPage } from './pages/AnomaliesPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProjectDetailPage } from './pages/ProjectDetailPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { ReportsPage } from './pages/ReportsPage';
import { RulesPage } from './pages/RulesPage';
import { VerificationHistoryPage } from './pages/VerificationHistoryPage';
import { EvidenceViewerPage } from './pages/EvidenceViewerPage';
import { ConfidenceDashboardPage } from './pages/ConfidenceDashboardPage';
import { SettingsPage } from './pages/SettingsPage';
import { UploadPage } from './pages/UploadPage';
import { VerificationPage } from './pages/VerificationPage';

const router = createBrowserRouter([{ path: '/', element: <AppLayout />, children: [
  { index: true, element: <DashboardPage /> },
  { path: 'projects', element: <ProjectsPage /> },
  { path: 'project', element: <ProjectDetailPage /> },
  { path: 'upload', element: <UploadPage /> },
  { path: 'verification', element: <VerificationPage /> },
  { path: 'anomalies', element: <AnomaliesPage /> },
  { path: 'reports', element: <ReportsPage /> },
  { path: 'rules', element: <RulesPage /> },
  { path: 'history', element: <VerificationHistoryPage /> },
  { path: 'evidence', element: <EvidenceViewerPage /> },
  { path: 'confidence', element: <ConfidenceDashboardPage /> },
  { path: 'settings', element: <SettingsPage /> },
] }]);

export default function App() { return <RouterProvider router={router} />; }
