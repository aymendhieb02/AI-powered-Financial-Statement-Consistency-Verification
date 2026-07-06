import { useParams } from 'react-router-dom';
import { Card, CardContent } from '../components/ui/card';

export function EvidenceViewerPage() {
  const { projectId } = useParams();

  if (!projectId) {
    return <Card className="p-4 text-sm text-slate-500">Select a project to review evidence.</Card>;
  }

  return (
    <Card>
      <CardContent className="p-6 text-sm text-slate-500">
        Evidence trace for this project will appear here after verification runs. Open an anomaly detail drawer to review line-level evidence for flagged accounts.
      </CardContent>
    </Card>
  );
}
