import { useCallback, useEffect, useRef, useState } from 'react';
import { analyzeGmailMessage, getGmailAuthUrl, getGmailStatus, revokeGmail, searchGmail } from '../api/gmail';
import type { GmailMessageRow, GmailSearchResult, GmailStatus } from '../api/gmail';

type PaneView = 'idle' | 'connecting';

export default function GmailPane({ onAnalyzed }: { onAnalyzed: (caseId: string) => void }) {
  const [status, setStatus] = useState<GmailStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [view, setView] = useState<PaneView>('idle');
  const [connectError, setConnectError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [search, setSearch] = useState<GmailSearchResult | null>(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [pageStack, setPageStack] = useState<(string | null)[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = null;
  }, []);

  const connected = !!status?.connected;

  const beginConnect = async () => {
    setConnectError(null);
    setView('connecting');
    try {
      const url = await getGmailAuthUrl();
      window.open(url, '_blank', 'noopener,noreferrer');
      pollRef.current = setInterval(async () => {
        const s = await getGmailStatus().catch(() => null);
        if (s?.connected) {
          stopPolling();
          setStatus(s);
          runSearch('');
        }
      }, 1600);
    } catch (err: any) {
      setConnectError(err.message ?? 'Unable to start Gmail sign-in');
      setView('idle');
    }
  };

  const disconnect = async () => {
    if (!window.confirm('Disconnect Gmail? This removes the saved connection from the server.')) return;
    setConnectError(null);
    try {
      await revokeGmail();
      setStatus(await getGmailStatus());
      setView('idle');
      setSearch(null);
    } catch (err: any) {
      setConnectError(err.message ?? 'Unable to disconnect Gmail');
    }
  };

  const runSearch = useCallback(async (q: string, token?: string | null, refreshList = false) => {
    setSearching(true);
    setSearchError(null);
    setAnalyzeError(null);
    setPageStack((stack) => refreshList || !token ? [] : [...stack, token]);
    try {
      setSearch(await searchGmail(q, token ?? null));
      if (refreshList) setQuery(q);
    } catch (err: any) {
      setSearchError(err.message ?? 'Unable to search Gmail');
    } finally {
      setSearching(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    getGmailStatus()
      .then((s) => {
        if (!active) return;
        setStatus(s);
        setStatusError(null);
        if (s.connected) runSearch('');
      })
      .catch((err: any) => active && setStatusError(err.message ?? 'Unable to check Gmail connection'));
    return () => { active = false; stopPolling(); };
  }, [runSearch, stopPolling]);

  const nextPage = () => search?.nextPageToken && runSearch(query, search.nextPageToken);
  const prevPage = () => {
    const stack = [...pageStack];
    const token = stack.pop() ?? null;
    setPageStack(stack);
    runSearch(query, token);
  };

  const analyze = async (message: GmailMessageRow) => {
    setAnalyzingId(message.id);
    setAnalyzeError(null);
    try {
      const result = await analyzeGmailMessage(message.id);
      onAnalyzed(result.case_id);
    } catch (err: any) {
      setAnalyzeError(err.message ?? 'Analysis failed');
    } finally {
      setAnalyzingId(null);
    }
  };

  if (statusError && !status) {
    return (
      <div className="p-4 rounded-xl bg-surface-container-low text-on-surface-variant">
        <p className="font-body-sm text-body-sm">Unable to check Gmail connection: {statusError}</p>
      </div>
    );
  }

  if (!connected) {
    return (
      <div className="p-4 rounded-xl border border-dashed border-outline-variant">
        <div className="flex items-center gap-space-sm mb-3">
          <span className="material-symbols-outlined text-[22px] text-primary">mail</span>
          <div>
            <p className="font-title-sm text-title-sm text-on-surface">Gmail</p>
            <p className="font-body-sm text-body-sm text-on-surface-variant">Acquire a message from your Gmail inbox</p>
          </div>
        </div>
        {view === 'connecting' ? (
          <div className="flex items-center gap-space-sm text-on-surface-variant font-body-sm text-body-sm">
            <span className="material-symbols-outlined text-[18px] text-primary animate-spin">progress_activity</span>
            <span>Waiting for Google sign-in… complete the flow in the new tab.</span>
          </div>
        ) : (
          <button
            onClick={beginConnect}
            className="w-full py-space-sm rounded-xl bg-primary text-on-primary hover:bg-primary-container font-title-sm text-title-sm shadow-sm transition-colors flex items-center justify-center gap-space-xs"
          >
            <span className="material-symbols-outlined text-[18px]">login</span>
            Connect Gmail
          </button>
        )}
        <p className="font-label-mono-sm text-label-mono-sm text-outline mt-2">OAuth 2.0 · read-only (gmail.readonly) · no tokens stored in the browser</p>
        {connectError && <p className="text-error text-sm mt-2">{connectError}</p>}
        {status?.status === 'revoked' && <p className="text-error text-sm mt-2">The previous connection was revoked by the provider. Connect again to continue.</p>}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-space-md">
      <div className="flex items-center justify-between p-4 rounded-xl bg-primary-container/40">
        <div className="flex items-center gap-space-sm min-w-0">
          <span className="material-symbols-outlined text-[22px] text-primary">verified_user</span>
          <div className="min-w-0">
            <p className="font-title-sm text-title-sm text-on-surface truncate">Connected to {status.account || 'Gmail'}</p>
            <p className="font-body-sm text-body-sm text-on-surface-variant">Select a message to acquire and analyze</p>
          </div>
        </div>
        <button onClick={disconnect} className="flex items-center gap-space-2xs px-space-sm py-space-2xs rounded-lg bg-surface-container-low text-on-surface-variant hover:text-error transition-colors shrink-0">
          <span className="material-symbols-outlined text-[16px]">link_off</span>
          <span className="font-body-sm text-body-sm">Disconnect</span>
        </button>
      </div>

<div className="flex gap-space-sm">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && runSearch(query, null, true)}
          placeholder="Search (e.g. from:paypal, subject:invoice)"
          className="flex-1 px-space-md py-space-xs rounded-xl border border-outline-variant bg-surface-container-lowest text-on-surface font-body-sm text-body-sm focus:border-primary focus:outline-none"
        />
        <button onClick={() => runSearch(query, null, true)} disabled={searching} className="px-space-md py-space-xs rounded-xl bg-surface-container-high text-on-surface hover:bg-surface-container transition-colors font-title-sm text-body-sm flex items-center gap-space-2xs">
          <span className="material-symbols-outlined text-[18px]">search</span>
          Search
        </button>
      </div>

      {searchError && <p className="text-error text-sm">{searchError}</p>}
      {analyzeError && <p className="text-error text-sm">{analyzeError}</p>}

          {searching ? (
            <p className="text-on-surface-variant font-body-sm text-body-sm">Searching Gmail…</p>
          ) : search && search.messages.length > 0 ? (
            <div className="flex flex-col gap-space-sm max-h-80 overflow-y-auto pr-1">
              {search.messages.map((m) => (
                <div key={m.id} className="p-3 rounded-xl border border-outline-variant bg-surface-container-lowest">
                  <div className="flex items-start justify-between gap-space-sm">
                    <div className="min-w-0">
                      <p className="font-title-sm text-title-sm text-on-surface truncate">{m.subject || '(no subject)'}</p>
                      <p className="font-body-sm text-body-sm text-on-surface-variant truncate">From {m.fromAddress || 'Unknown'} · {m.date || 'no date'}</p>
                      {m.snippet && <p className="font-body-sm text-body-sm text-on-surface-variant/70 truncate mt-1">{m.snippet}</p>}
                    </div>
                    <button
                      onClick={() => analyze(m)}
                      disabled={analyzingId === m.id}
                      className="shrink-0 px-space-sm py-space-2xs rounded-lg bg-primary text-on-primary hover:bg-primary-container font-title-sm text-body-sm transition-colors flex items-center gap-space-2xs"
                    >
                      <span className="material-symbols-outlined text-[16px]">{analyzingId === m.id ? 'progress_activity animate-spin' : 'play_arrow'}</span>
                      {analyzingId === m.id ? 'Analyzing' : 'Analyze'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : search ? (
            <p className="text-on-surface-variant font-body-sm text-body-sm">No messages matched the search.</p>
          ) : null}

          {(search?.nextPageToken || pageStack.length > 0) && (
            <div className="flex items-center justify-between">
              <button onClick={prevPage} disabled={pageStack.length === 0} className="px-space-md py-space-2xs rounded-lg bg-surface-container-high text-on-surface disabled:opacity-40 font-body-sm text-body-sm">
                ← Previous
              </button>
              {search?.nextPageToken && (
                <button onClick={nextPage} className="px-space-md py-space-2xs rounded-lg bg-surface-container-high text-on-surface font-body-sm text-body-sm">
                  Next →
                </button>
              )}
            </div>
          )}

          <p className="font-label-mono-sm text-label-mono-sm text-outline">
        Metadata only; the raw RFC-822 message is fetched server-side at analysis time and preserved as evidence.
      </p>
    </div>
  );
}