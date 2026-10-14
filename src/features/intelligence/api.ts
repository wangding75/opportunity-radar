import { request, RequestOptions } from '@/api/client';

export interface ObservationUserState {
  bookmarked: boolean;
  dismissed: boolean;
  dismissed_at: string | null;
  notes: string;
  updated_at: string;
}

export interface ObservationItem {
  id: number;
  public_id: string;
  source_id: string;
  query: string;
  item_type: string;
  title: string;
  text: string;
  source_url: string | null;
  evidence_quality: 'A' | 'B' | 'C' | 'D' | 'E';
  acquisition_method: string;
  observed_at: string;
  /** null = 当前用户没有该观察的状态（未登录或从未写入）。不得伪造默认收藏值。 */
  user_state: ObservationUserState | null;
}

export interface ObservationDetail extends ObservationItem {
  external_id: string | null;
  acquisition_risk: string;
}

export interface ObservationStatePatch {
  bookmarked?: boolean;
  dismissed?: boolean;
  notes?: string;
}

// RequestOptions.body 需要 Record<string, unknown>；接口允许显式展开。
export type ObservationStatePatchBody = Record<string, unknown>;

export interface ObservationStateResponse {
  observation_public_id: string;
  user_id: number;
  user_state: ObservationUserState | null;
  request_id?: string;
}

export interface ObservationPage {
  total: number;
  offset: number | null;
  limit: number;
  next_cursor: string | null;
  has_more: boolean;
  items: ObservationItem[];
}

export interface ObservationQuery {
  q?: string;
  sourceId?: string;
  itemType?: string;
  observedAfter?: string;
  limit?: number;
  signal?: AbortSignal;
}

export function listObservations(query: ObservationQuery = {}): Promise<ObservationPage> {
  const params = new URLSearchParams();
  if (query.q?.trim()) params.set('q', query.q.trim());
  if (query.sourceId && query.sourceId !== 'ALL') params.set('source_id', query.sourceId);
  if (query.itemType && query.itemType !== 'ALL') params.set('item_type', query.itemType);
  if (query.observedAfter) params.set('observed_after', query.observedAfter);
  params.set('limit', String(query.limit || 50));
  const options: RequestOptions = { signal: query.signal };
  return request<ObservationPage>(`/api/v1/observations?${params.toString()}`, options);
}

export function getObservationDetail(publicId: string, signal?: AbortSignal): Promise<ObservationDetail> {
  return request<ObservationDetail>(`/api/v1/observations/${encodeURIComponent(publicId)}`, { signal });
}

export function getObservationState(publicId: string, signal?: AbortSignal): Promise<ObservationStateResponse> {
  return request<ObservationStateResponse>(`/api/v1/observations/${encodeURIComponent(publicId)}/state`, { signal });
}

export function putObservationState(publicId: string, patch: ObservationStatePatch): Promise<ObservationStateResponse> {
  const body: ObservationStatePatchBody = { ...patch };
  return request<ObservationStateResponse>(`/api/v1/observations/${encodeURIComponent(publicId)}/state`, {
    method: 'PUT',
    body,
  });
}

export function deleteObservationState(publicId: string): Promise<ObservationStateResponse> {
  return request<ObservationStateResponse>(`/api/v1/observations/${encodeURIComponent(publicId)}/state`, {
    method: 'DELETE',
  });
}
