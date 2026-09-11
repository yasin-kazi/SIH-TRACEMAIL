import { request } from './client';
import type { GmailMessageRow, GmailSearchResult, GmailStatus } from '../types';

export const getGmailStatus = () => request<GmailStatus>('/api/gmail/status');
export const getGmailAuthUrl = async () => (await request<{ auth_url: string }>('/api/gmail/auth/start')).auth_url;
export const searchGmail = async (query: string, pageToken?: string | null, maxResults = 20): Promise<GmailSearchResult> => {
  const params = new URLSearchParams();
  if (query) params.set('q', query);
  if (pageToken) params.set('page_token', pageToken);
  params.set('max_results', String(maxResults));
  return request<GmailSearchResult>(`/api/gmail/search?${params.toString()}`);
};
export const analyzeGmailMessage = async (messageId: string) => request<{ case_id: string; case_number: number; evidence_id: string; message: string }>('/api/gmail/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message_id: messageId }) });
export const revokeGmail = () => request<{ status: string }>('/api/gmail/revoke', { method: 'POST' });

export type { GmailMessageRow, GmailSearchResult, GmailStatus };