import { useParams } from 'react-router-dom';
import { useApiResource } from '../api/useApiResource';
import { getEvidence, getHeaders, getTransitHops, getMimeParts, getAttachments, getIOCs, getRelationships, getForensicSummary } from '../api/cases';
import type { ForensicSummary } from '../types';

function formatBytes(bytes: number): string {
  if (!bytes) return '0 bytes';
  const units = ['bytes', 'KB', 'MB'];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) { value /= 1024; unit += 1; }
  return `${value.toFixed(unit ? 1 : 0)} ${units[unit]}`;
}

export default function EvidencePage() {
  const { caseId = '' } = useParams();
  const summary = useApiResource<ForensicSummary>(() => getForensicSummary(caseId), `s${caseId}`);
  const evidence = useApiResource(() => getEvidence(caseId), `e${caseId}`);
  const headers = useApiResource(() => getHeaders(caseId), `h${caseId}`);
  const hops = useApiResource(() => getTransitHops(caseId), `t${caseId}`);
  const parts = useApiResource(() => getMimeParts(caseId), `m${caseId}`);
  const attachments = useApiResource(() => getAttachments(caseId), `a${caseId}`);
  const iocs = useApiResource(() => getIOCs(caseId), `i${caseId}`);
  const relationships = useApiResource(() => getRelationships(caseId), `r${caseId}`);
  const loading = summary.loading || evidence.loading || headers.loading || hops.loading || parts.loading || attachments.loading || iocs.loading || relationships.loading;
  const error = summary.error || evidence.error || headers.error || hops.error || parts.error || attachments.error || iocs.error || relationships.error;

  if (loading) return <p>Loading evidence…</p>;
  if (error) return <p className="text-error">{error}</p>;

  const s = summary.data;
  return <div className="space-y-5">
    <h1 className="font-headline-lg">Evidence</h1>
    <p className="text-on-surface-variant">Original email evidence is preserved separately from these parsed and derived observations. All values below come from persisted forensic records.</p>

    <section className="p-4 rounded-xl bg-surface-container-low">
      <h2>Original evidence</h2>
      {s?.evidenceId ? <dl className="grid md:grid-cols-2 gap-2 text-sm">
        <div><dt className="text-on-surface-variant">Source</dt><dd>{s.sourceType} ({s.acquisitionMethod || 'n/a'})</dd></div>
        <div><dt className="text-on-surface-variant">Identifier</dt><dd className="break-all">{s.sourceIdentifier || '—'}</dd></div>
        <div><dt className="text-on-surface-variant">Filename</dt><dd>{s.originalFilename || '—'}</dd></div>
        <div><dt className="text-on-surface-variant">Content type</dt><dd>{s.contentType || '—'}</dd></div>
        <div><dt className="text-on-surface-variant">Size</dt><dd>{formatBytes(s.size)}</dd></div>
        <div><dt className="text-on-surface-variant">Acquired</dt><dd>{s.acquisitionTimestamp ? new Date(s.acquisitionTimestamp).toLocaleString() : '—'}</dd></div>
        <div className="md:col-span-2"><dt className="text-on-surface-variant">SHA-256</dt><dd className="font-mono text-xs break-all">{s.sha256 || '—'}</dd></div>
      </dl> : <p>No preserved evidence record is available for this case.</p>}
    </section>

    <section className="p-4 rounded-xl bg-surface-container-low">
      <h3 className="mb-2">Forensic counts</h3>
      <p>MIME parts: {s?.mimeParts ?? 0} · Received hops: {s?.receivedHops ?? 0} · Attachments: {s?.attachments ?? 0} · Observables: {s?.iocs ?? 0}</p>
    </section>

    <section>
      <h2>Derived findings</h2>
      {evidence.data?.map(x => <article key={x.id} className="p-3 my-2 bg-surface-container-low rounded-xl"><strong>{x.title}</strong><p>{x.description}</p><small>{x.evidenceState} · {x.confidence}% · {x.source}</small></article>)}
      {!evidence.data?.length && <p>No derived findings are available.</p>}
    </section>

    <section>
      <h2>MIME structure</h2>
      {parts.data?.length ? parts.data.map(p => <article key={p.id} className="p-3 my-2 bg-surface-container-low rounded-xl text-sm">
        <p className="font-mono">{p.contentType}{p.isAttachment ? ' · attachment' : ''} {p.filename && `· ${p.filename}`}</p>
        <small className="text-on-surface-variant">part {p.partIndex}{p.parentId ? ` under ${p.parentId}` : ''} · depth {p.depth} · {p.disposition || 'inline'} · {formatBytes(p.size)}{p.transferEncoding && ` · ${p.transferEncoding}`}</small>
      </article>) : <p>No MIME parts were persisted.</p>}
    </section>

    <section>
      <h2>Received chain</h2>
      {hops.data?.length ? hops.data.map(h => <article key={`${h.sequence}-${h.ip}`} className="p-3 my-2 bg-surface-container-low rounded-xl text-sm">
        <p><strong>{h.label}</strong> · observed from {h.fromHost || 'unknown'} by {h.byHost || 'unknown'}</p>
        <small className="text-on-surface-variant">source IP {h.sourceIp || '—'} · {h.protocol || 'protocol unspecified'}{h.timestamp && ` · ${h.timestamp}`}</small>
        {h.rawHeader && <p className="font-mono text-xs mt-1 break-all">{h.rawHeader}</p>}
      </article>) : <p>No Received headers were observed in this email.</p>}
    </section>

    <section>
      <h2>Attachments</h2>
      {attachments.data?.length ? <div className="space-y-2">{attachments.data.map(a => <article key={a.id} className="p-3 bg-surface-container-low rounded-xl text-sm">
        <p className="break-all"><strong>{a.filename}</strong> · {a.contentType} · {formatBytes(a.size)}</p>
        <small className="font-mono text-xs break-all">SHA-256: {a.sha256 || '—'}</small>
      </article>)}</div> : <p>No attachments were found.</p>}
    </section>

    <section>
      <h2>Observables / IOCs</h2>
      {iocs.data?.length ? <div className="grid md:grid-cols-2 gap-2">{iocs.data.map(i => <article key={i.id} className="p-3 bg-surface-container-low rounded-xl text-sm break-all"><p><strong>{i.type}</strong> · {i.value}</p><small className="text-on-surface-variant">observed in {i.source}</small></article>)}</div> : <p>No observables were extracted.</p>}
    </section>

    <section>
      <h2>Evidence relationships</h2>
      {relationships.data?.length ? <div className="space-y-1 text-sm">{relationships.data.map(r => <p key={r.id} className="p-2 bg-surface-container-low rounded-lg font-mono text-xs break-all">{r.sourceType} ({r.sourceId}) {r.relationType} → {r.targetType} ({r.targetId})</p>)}</div> : <p>No relationships were persisted.</p>}
    </section>

    <section>
      <h2>Headers</h2>
      {headers.data?.headers.map((x, i) => <p key={i} className="font-mono text-sm break-all"><strong>{x.key}</strong> {x.value}</p>)}
    </section>
  </div>;
}