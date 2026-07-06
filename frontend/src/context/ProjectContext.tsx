import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

const PROJECT_KEY = 'finverify_project_id';
const RUN_KEY = 'finverify_run_id';
const OLD_DOC_KEY = 'finverify_old_document_id';
const NEW_DOC_KEY = 'finverify_new_document_id';

type ProjectContextValue = {
  projectId: string | null;
  runId: string | null;
  oldDocumentId: string | null;
  newDocumentId: string | null;
  setProjectId: (id: string) => void;
  setRunId: (id: string | null) => void;
  setOldDocumentId: (id: string | null) => void;
  setNewDocumentId: (id: string | null) => void;
  projectPath: (subpath?: string) => string;
  openProject: (id: string, subpath?: string) => void;
};

const ProjectContext = createContext<ProjectContextValue | null>(null);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const params = useParams();
  const routeProjectId = params.projectId ?? null;

  const [projectId, setProjectIdState] = useState<string | null>(() => localStorage.getItem(PROJECT_KEY));
  const [runId, setRunIdState] = useState<string | null>(() => localStorage.getItem(RUN_KEY));
  const [oldDocumentId, setOldDocumentIdState] = useState<string | null>(() => localStorage.getItem(OLD_DOC_KEY));
  const [newDocumentId, setNewDocumentIdState] = useState<string | null>(() => localStorage.getItem(NEW_DOC_KEY));

  useEffect(() => {
    if (routeProjectId && routeProjectId !== projectId) {
      setProjectIdState(routeProjectId);
      localStorage.setItem(PROJECT_KEY, routeProjectId);
    }
  }, [routeProjectId, projectId]);

  const setProjectId = useCallback((id: string) => {
    setProjectIdState(id);
    localStorage.setItem(PROJECT_KEY, id);
  }, []);

  const setRunId = useCallback((id: string | null) => {
    setRunIdState(id);
    if (id) localStorage.setItem(RUN_KEY, id);
    else localStorage.removeItem(RUN_KEY);
  }, []);

  const setOldDocumentId = useCallback((id: string | null) => {
    setOldDocumentIdState(id);
    if (id) localStorage.setItem(OLD_DOC_KEY, id);
    else localStorage.removeItem(OLD_DOC_KEY);
  }, []);

  const setNewDocumentId = useCallback((id: string | null) => {
    setNewDocumentIdState(id);
    if (id) localStorage.setItem(NEW_DOC_KEY, id);
    else localStorage.removeItem(NEW_DOC_KEY);
  }, []);

  const projectPath = useCallback((subpath?: string) => {
    const id = routeProjectId ?? projectId;
    if (!id) return '/projects';
    return subpath ? `/projects/${id}/${subpath}` : `/projects/${id}`;
  }, [projectId, routeProjectId]);

  const openProject = useCallback((id: string, subpath?: string) => {
    setProjectId(id);
    navigate(subpath ? `/projects/${id}/${subpath}` : `/projects/${id}`);
  }, [navigate, setProjectId]);

  const value = useMemo(() => ({
    projectId: routeProjectId ?? projectId,
    runId,
    oldDocumentId,
    newDocumentId,
    setProjectId,
    setRunId,
    setOldDocumentId,
    setNewDocumentId,
    projectPath,
    openProject,
  }), [routeProjectId, projectId, runId, oldDocumentId, newDocumentId, setProjectId, setRunId, setOldDocumentId, setNewDocumentId, projectPath, openProject]);

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
}

export function useProject() {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error('useProject must be used within ProjectProvider');
  return ctx;
}
