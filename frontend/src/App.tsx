import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { AdvancedPage } from './pages/AdvancedPage';
import { AnomaliesPage } from './pages/AnomaliesPage';
import { CompareDocumentsPage } from './pages/CompareDocumentsPage';
import { ReportsPage } from './pages/ReportsPage';
import { ResultsPage } from './pages/ResultsPage';

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <CompareDocumentsPage /> },
      { path: 'compare', element: <CompareDocumentsPage /> },
      { path: 'results/:runId', element: <ResultsPage /> },
      { path: 'anomalies/:runId', element: <AnomaliesPage /> },
      { path: 'reports/:runId', element: <ReportsPage /> },
      { path: 'advanced', element: <AdvancedPage /> },
      { path: 'projects', element: <Navigate to="/compare" replace /> },
      { path: 'project', element: <Navigate to="/compare" replace /> },
      { path: 'upload', element: <Navigate to="/compare" replace /> },
      { path: 'verification', element: <Navigate to="/compare" replace /> },
      { path: 'anomalies', element: <Navigate to="/compare" replace /> },
      { path: 'reports', element: <Navigate to="/compare" replace /> },
      { path: 'rules', element: <Navigate to="/advanced" replace /> },
      { path: 'evidence', element: <Navigate to="/advanced" replace /> },
      { path: 'history', element: <Navigate to="/advanced" replace /> },
      { path: 'settings', element: <Navigate to="/advanced" replace /> },
      { path: 'confidence', element: <Navigate to="/advanced" replace /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
