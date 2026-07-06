import type { UploadedDocument } from '../../types/api';
import { Card, CardContent } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';

type Props = {
  documents: UploadedDocument[];
  oldDocumentId: string | null;
  newDocumentId: string | null;
  onOldChange: (filename: string) => void;
  onNewChange: (filename: string) => void;
};

export function CompareTwoDocuments({ documents, oldDocumentId, newDocumentId, onOldChange, onNewChange }: Props) {
  if (documents.length < 2) {
    return (
      <Card>
        <CardContent className="p-4 text-sm text-slate-500">
          Upload at least two annual PDFs to select an old document and a new document for comparison.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <div>
          <div className="section-title">Compare two documents</div>
          <p className="mt-1 text-sm text-slate-500">
            Select the prior-year PDF and the new annual PDF. FinVerify compares prior-year closing values against comparative values in the newer statement.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-600">Old document (prior year)</label>
            <Select value={oldDocumentId ?? ''} onValueChange={onOldChange}>
              <SelectTrigger><SelectValue placeholder="Select old PDF" /></SelectTrigger>
              <SelectContent>
                {documents.map((doc) => (
                  <SelectItem key={doc.filename} value={doc.filename}>
                    {doc.filename}{doc.detected_year ? ` (${doc.detected_year})` : ''}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-600">New document (current year)</label>
            <Select value={newDocumentId ?? ''} onValueChange={onNewChange}>
              <SelectTrigger><SelectValue placeholder="Select new PDF" /></SelectTrigger>
              <SelectContent>
                {documents.map((doc) => (
                  <SelectItem key={doc.filename} value={doc.filename}>
                    {doc.filename}{doc.detected_year ? ` (${doc.detected_year})` : ''}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        {oldDocumentId && newDocumentId && oldDocumentId === newDocumentId && (
          <p className="text-sm text-amber-700">Select two different documents to run a comparison.</p>
        )}
      </CardContent>
    </Card>
  );
}
