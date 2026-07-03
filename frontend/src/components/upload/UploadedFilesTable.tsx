import type { UploadedDocument } from '../../types/api';

export function UploadedFilesTable({ files }: { files: UploadedDocument[] }) {
  return <div className="overflow-hidden rounded-lg border border-audit-line bg-white">
    <table className="w-full text-left text-sm">
      <thead className="bg-audit-panel text-audit-muted"><tr><th className="px-4 py-3">Filename</th><th>Year</th><th>Size</th><th>Status</th></tr></thead>
      <tbody>{files.map((file) => <tr key={file.filename} className="border-t border-audit-line"><td className="px-4 py-3 font-medium">{file.filename}</td><td>{file.detected_year ?? '-'}</td><td>{Math.round(file.size / 1024)} KB</td><td>{file.status}</td></tr>)}</tbody>
    </table>
  </div>;
}
