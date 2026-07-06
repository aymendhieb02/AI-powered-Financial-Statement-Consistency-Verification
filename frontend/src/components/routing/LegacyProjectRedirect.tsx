import { Navigate, useLocation } from 'react-router-dom';
import { useProject } from '../../context/ProjectContext';

export function LegacyProjectRedirect({ subpath }: { subpath: string }) {
  const { projectId } = useProject();
  const location = useLocation();
  if (!projectId) return <Navigate to="/projects" replace state={{ from: location.pathname }} />;
  return <Navigate to={`/projects/${projectId}/${subpath}`} replace />;
}
