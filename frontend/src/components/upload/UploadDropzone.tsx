import { UploadCloud } from 'lucide-react';

export function UploadDropzone({ onFiles }: { onFiles: (files: File[]) => void }) {
  return <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-audit-line bg-white p-8 text-center hover:bg-audit-panel">
    <UploadCloud className="mb-3 text-audit-accent" />
    <div className="font-medium">Upload annual SICAV PDFs</div>
    <div className="text-sm text-audit-muted">Select one or more financial statement PDFs.</div>
    <input className="hidden" type="file" multiple accept="application/pdf" onChange={(event) => onFiles(Array.from(event.target.files ?? []))} />
  </label>;
}
