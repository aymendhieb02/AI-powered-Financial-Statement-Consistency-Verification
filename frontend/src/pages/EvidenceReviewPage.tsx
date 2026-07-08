import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  CircleDashed,
  FileSearch,
  ScanLine,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getApiErrorMessage } from '../api/client';
import { getDocumentPage, getEvidenceDetail } from '../api/verification';
import { Badge, SeverityBadge, StatusBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { EmptyState, PageHeader } from '../components/ui/Cards';
import type { ComparisonEvidence, DocumentPageResponse, EvidenceReference } from '../types/api';

function money(value?: number | null) {
  return typeof value === 'number' ? new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 }).format(value) : 'Not detected';
}

function percent(value?: number | null) {
  return typeof value === 'number' ? `${value.toFixed(2)}%` : 'Not detected';
}

function humanizeLabel(value?: string | null) {
  if (!value) return 'Not detected';
  return value
    .split('__')
    .pop()
    ?.replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/(^|\s)\S/g, (letter) => letter.toUpperCase()) ?? value;
}

function issueTone(issueType?: string) {
  if (issueType === 'financial_mismatch') return 'danger' as const;
  if (issueType === 'ok') return 'success' as const;
  if (issueType === 'duplicate_label' || issueType === 'polluted_label') return 'info' as const;
  return 'warning' as const;
}

function evidenceStatusCopy(item?: ComparisonEvidence | null) {
  switch (item?.status_group) {
    case 'matched':
      return 'Matched evidence';
    case 'financial':
      return 'Financial difference';
    case 'structural':
      return 'Structural review';
    default:
      return 'Extraction review';
  }
}

function viewerAccent(issueType?: string) {
  switch (issueType) {
    case 'financial_mismatch':
      return 'border-red-200 bg-red-50 text-red-700';
    case 'ok':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'duplicate_label':
      return 'border-violet-200 bg-violet-50 text-violet-700';
    case 'polluted_label':
      return 'border-orange-200 bg-orange-50 text-orange-700';
    default:
      return 'border-amber-200 bg-amber-50 text-amber-700';
  }
}

function EvidenceImage({ title, page, bbox, issueType }: { title: string; page?: DocumentPageResponse | null; bbox?: number[] | null; issueType?: string }) {
  const [failed, setFailed] = useState(false);
  const imageUrl = page?.image_url;
  const canOverlay = !failed && imageUrl && bbox?.length === 4 && page?.page_width && page?.page_height;
  const [x0, y0, x1, y1] = bbox ?? [];
  const overlayStyle = canOverlay
    ? {
        left: `${(Math.max(0, x0) / page.page_width!) * 100}%`,
        top: `${(Math.max(0, y0) / page.page_height!) * 100}%`,
        width: `${(Math.max(0, x1 - x0) / page.page_width!) * 100}%`,
        height: `${(Math.max(0, y1 - y0) / page.page_height!) * 100}%`,
      }
    : undefined;

  return (
    <div className='overflow-hidden rounded-lg border border-slate-200 bg-white'>
      {imageUrl && !failed ? (
        <div className='relative'>
          <img src={imageUrl} alt={title} className='w-full bg-white' onError={() => setFailed(true)} />
          {canOverlay ? <div className={'absolute border-2 shadow-[0_0_0_9999px_rgba(15,23,42,0.06)] ' + viewerAccent(issueType)} style={overlayStyle} /> : null}
          {!canOverlay ? <div className='absolute bottom-3 right-3 rounded-md border border-slate-200 bg-white/90 px-2 py-1 text-xs text-slate-600'>Exact highlight unavailable</div> : null}
        </div>
      ) : (
        <div className='flex min-h-[420px] flex-col items-center justify-center gap-3 bg-slate-50 p-8 text-center text-sm text-slate-500'>
          <FileSearch size={18} className='text-slate-400' />
          <div>
            <div className='font-medium text-slate-700'>Visual preview not available for this page yet.</div>
            <div className='mt-1'>The page reference and extracted row details are still available below.</div>
          </div>
        </div>
      )}
    </div>
  );
}

function CandidateCard({ candidate, index }: { candidate: EvidenceReference; index: number }) {
  const value = candidate.current_value ?? candidate.previous_value ?? candidate.value;
  return (
    <div className='rounded-lg border border-slate-200 bg-slate-50 p-3'>
      <div className='flex items-center justify-between gap-3'>
        <div className='text-sm font-medium text-slate-900'>Candidate {index + 1}</div>
        <Badge tone='info'>Page {candidate.page ?? 'Not detected'}</Badge>
      </div>
      <div className='mt-2 grid gap-2 text-sm md:grid-cols-2'>
        <Fact label='Section' value={candidate.section_name || candidate.statement_name || 'Not detected'} />
        <Fact label='Amount' value={money(typeof value === 'number' ? value : undefined)} />
      </div>
      <div className='mt-2 rounded-md bg-white p-3 text-sm text-slate-700'>
        {candidate.raw_text || candidate.label_text || 'No extracted line captured.'}
      </div>
    </div>
  );
}

export function EvidenceReviewPage() {
  const { runId = '', evidenceId = '' } = useParams();
  const projectId = localStorage.getItem('finverify_project_id') ?? '';
  const [item, setItem] = useState<ComparisonEvidence | null>(null);
  const [oldPage, setOldPage] = useState<DocumentPageResponse | null>(null);
  const [newPage, setNewPage] = useState<DocumentPageResponse | null>(null);
  const [error, setError] = useState('');
  const decodedEvidenceId = useMemo(() => decodeURIComponent(evidenceId), [evidenceId]);

  useEffect(() => {
    async function load() {
      if (!projectId || !runId || !decodedEvidenceId) return;
      try {
        const evidence = await getEvidenceDetail(projectId, runId, decodedEvidenceId);
        setItem(evidence);
        const requests: Array<Promise<void>> = [];
        if (evidence.old_document_id && evidence.old_page) {
          requests.push(getDocumentPage(projectId, evidence.old_document_id, evidence.old_page, runId, decodedEvidenceId).then(setOldPage));
        }
        if (evidence.new_document_id && evidence.new_page) {
          requests.push(getDocumentPage(projectId, evidence.new_document_id, evidence.new_page, runId, decodedEvidenceId).then(setNewPage));
        }
        await Promise.all(requests);
      } catch (err) {
        setError(getApiErrorMessage(err, 'Failed to load evidence.'));
      }
    }
    load();
  }, [decodedEvidenceId, projectId, runId]);

  if (!projectId || runId === 'latest') {
    return <EmptyState title='No comparison has been executed yet.' description='Upload two annual financial statements and click Compare.' action={<Button asChild><Link to='/compare'>Go to Compare Documents</Link></Button>} />;
  }

  if (!item && !error) {
    return <section className='space-y-6'><PageHeader eyebrow='Evidence Review' title='Loading review evidence' description='FinVerify is preparing side-by-side evidence from both annual reports.' /></section>;
  }

  if (error && !item) {
    return <EmptyState title='Evidence not found' description={error} action={<Button asChild><Link to={'/anomalies/' + runId}>Back to anomalies</Link></Button>} />;
  }

  const displayLabel = item?.account_label_new || item?.account_label_old || item?.new_label || item?.old_label || humanizeLabel(item?.canonical_label);
  const duplicateCandidates = item?.duplicate_candidates ?? [];

  return (
    <section className='space-y-6'>
      <PageHeader
        eyebrow='Evidence Review'
        title={displayLabel}
        description='Inspect the old and new annual reports side by side before drawing an accounting conclusion.'
        actions={
          <>
            <Button asChild variant='secondary'>
              <Link to={'/anomalies/' + runId}><ArrowLeft size={16} /> Back to anomalies</Link>
            </Button>
            <Button asChild>
              <Link to={'/results/' + runId}>Return to results</Link>
            </Button>
          </>
        }
      />

      <Card>
        <CardContent className='grid gap-5 p-5 lg:grid-cols-[1.1fr_0.9fr]'>
          <div className='space-y-4'>
            <div className='flex flex-wrap items-center gap-2'>
              <SeverityBadge severity={item?.severity} />
              <StatusBadge status={item?.status} />
              <Badge tone={issueTone(item?.issue_type)}>{evidenceStatusCopy(item)}</Badge>
              {item?.issue_type ? <Badge tone='neutral'>{item.issue_type.replace(/_/g, ' ')}</Badge> : null}
            </div>
            <div className='grid gap-3 md:grid-cols-2 xl:grid-cols-3'>
              <Fact label='Statement' value={item?.statement_name || item?.statement || 'Not detected'} />
              <Fact label='Compared year' value={item?.compared_year ?? 'Not detected'} />
              <Fact label='Difference' value={money(item?.difference ?? item?.delta)} />
              <Fact label='Expected amount' value={money(item?.expected_value ?? item?.old_value)} />
              <Fact label='Reported amount' value={money(item?.actual_value ?? item?.new_value)} />
              <Fact label='Difference %' value={percent(item?.difference_percent)} />
            </div>
          </div>
          <div className='rounded-lg border border-slate-200 bg-slate-50 p-4'>
            <div className='text-xs font-semibold uppercase tracking-wide text-slate-500'>Accountant summary</div>
            <p className='mt-2 text-sm leading-6 text-slate-700'>{item?.accountant_reason || item?.explanation || 'Inspect both source rows and confirm the carry-forward line.'}</p>
            <div className='mt-4 space-y-3 text-sm'>
              <Fact label='Recommended action' value={item?.recommended_action || 'Inspect both report pages.'} />
              <Fact label='Evidence confidence' value={typeof item?.confidence === 'number' ? `${(item.confidence * 100).toFixed(1)}%` : 'Not calculated'} />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className='grid gap-5 xl:grid-cols-2'>
        <EvidenceCard
          title='Old annual report'
          documentId={item?.old_document_id}
          label={item?.account_label_old || item?.old_label}
          value={item?.old_current_value ?? item?.old_value}
          page={oldPage}
          rawLine={item?.old_raw_line || item?.old_line_text}
          bbox={item?.old_bbox}
          issueType={item?.issue_type}
          sectionFallback={item?.old_section || item?.statement_name || item?.statement}
        />
        <EvidenceCard
          title='New annual report'
          documentId={item?.new_document_id}
          label={item?.account_label_new || item?.new_label}
          value={item?.new_previous_value ?? item?.new_value}
          page={newPage}
          rawLine={item?.new_raw_line || item?.new_line_text}
          bbox={item?.new_bbox}
          issueType={item?.issue_type}
          sectionFallback={item?.new_section || item?.statement_name || item?.statement}
        />
      </div>

      {duplicateCandidates.length > 0 ? (
        <Card>
          <CardContent className='space-y-4 p-5'>
            <div className='flex items-center gap-2 text-sm font-semibold text-slate-950'>
              <ScanLine size={16} className='text-violet-600' /> Duplicate candidate evidence
            </div>
            <p className='text-sm text-slate-600'>FinVerify kept every candidate row instead of choosing one automatically. Review these lines to recover the missing parent context.</p>
            <div className='grid gap-3 lg:grid-cols-2'>
              {duplicateCandidates.map((candidate, index) => <CandidateCard key={`${candidate.document_id ?? 'candidate'}-${index}`} candidate={candidate} index={index} />)}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {error ? <Card className='border-red-200'><CardContent className='flex items-center gap-3 p-4 text-sm text-red-700'><AlertTriangle size={16} />{error}</CardContent></Card> : null}

      <Card>
        <CardContent className='grid gap-4 p-5 md:grid-cols-3'>
          <StatusItem title='Accounting interpretation' body={item?.issue_type === 'financial_mismatch' ? 'Potential real carry-forward difference detected.' : 'This item does not automatically mean the annual report fails accounting consistency.'} icon={<CheckCircle2 size={16} className='text-emerald-600' />} />
          <StatusItem title='Extraction interpretation' body={item?.status_group === 'structural' || item?.status_group === 'extraction' ? 'Extraction or normalization review is recommended before concluding on the underlying accounting.' : 'Evidence quality is sufficient for a direct old-versus-new value comparison.'} icon={<CircleDashed size={16} className='text-amber-600' />} />
          <StatusItem title='Evidence coverage' body={oldPage?.image_url || newPage?.image_url ? 'Page images are available for side-by-side inspection.' : 'Page references and extracted rows are available even when the visual preview is missing.'} icon={<FileSearch size={16} className='text-blue-600' />} />
        </CardContent>
      </Card>

      <details className='rounded-lg border border-slate-200 bg-white p-4'>
        <summary className='flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-semibold text-slate-900'>
          Technical details
          <ChevronDown size={16} className='text-slate-500' />
        </summary>
        <div className='mt-4 grid gap-4 md:grid-cols-2'>
          <Fact label='Canonical label' value={item?.canonical_label || 'Not detected'} />
          <Fact label='Hierarchy path' value={item?.hierarchy_path || 'Not detected'} />
          <Fact label='Matching method' value={item?.matching_method || 'Not detected'} />
          <Fact label='Technical reason' value={item?.technical_reason || 'Not detected'} />
          <Fact label='Old bounding box' value={item?.old_bbox?.length ? item.old_bbox.join(', ') : 'Not available'} />
          <Fact label='New bounding box' value={item?.new_bbox?.length ? item.new_bbox.join(', ') : 'Not available'} />
        </div>
      </details>
    </section>
  );
}

function EvidenceCard({ title, documentId, label, value, page, rawLine, bbox, issueType, sectionFallback }: { title: string; documentId?: string | null; label?: string | null; value?: number | null; page?: DocumentPageResponse | null; rawLine?: string | null; bbox?: number[] | null; issueType?: string; sectionFallback?: string | null }) {
  return (
    <Card>
      <CardContent className='space-y-4 p-5'>
        <div className='flex items-start justify-between gap-3'>
          <div>
            <div className='text-sm font-semibold text-slate-950'>{title}</div>
            <div className='mt-1 text-xs text-slate-500'>{documentId || 'Document not detected'}</div>
          </div>
          <Badge tone={issueTone(issueType)}>{page?.page_number ? `Page ${page.page_number}` : 'Page not detected'}</Badge>
        </div>

        <div className='grid gap-3 text-sm md:grid-cols-2'>
          <Fact label='Account label' value={label || 'Not detected'} />
          <Fact label='Amount' value={money(value)} />
          <Fact label='Section' value={page?.section || sectionFallback || 'Not detected'} />
          <Fact label='Evidence line' value={page?.raw_line || rawLine || 'Not detected'} />
        </div>

        <EvidenceImage title={title} page={page} bbox={bbox || page?.bounding_box} issueType={issueType} />
      </CardContent>
    </Card>
  );
}

function Fact({ label, value }: { label: string; value: string | number }) {
  return <div><div className='text-xs font-medium uppercase tracking-wide text-slate-500'>{label}</div><div className='mt-1 text-sm font-medium leading-6 text-slate-950'>{value}</div></div>;
}

function StatusItem({ title, body, icon }: { title: string; body: string; icon: ReactNode }) {
  return <div className='rounded-lg border border-slate-200 p-4'><div className='flex items-center gap-2 text-sm font-semibold text-slate-950'>{icon}{title}</div><p className='mt-2 text-sm leading-6 text-slate-600'>{body}</p></div>;
}
