import { request } from '@/api/client';

export interface OpportunityEvidence {
  source: string;
  title: string;
  observed_at: string;
  quality: string;
}

export interface OpportunityDetail {
  id: number;
  public_id: string;
  title: string;
  stage: string;
  score: number;
  risk_score: number;
  evidence_count: number;
  last_seen_at: string;
  analysis: { summary: string; risk_notes: string; status: string };
  keywords: Array<{ keyword: string; role: string; weight: number }>;
  research: { status: string; priority: number; notes: string };
  evidence: OpportunityEvidence[];
}

export const getOpportunity = (publicId: string, signal?: AbortSignal): Promise<OpportunityDetail> =>
  request<OpportunityDetail>(`/api/v1/opportunities/${encodeURIComponent(publicId)}`, { signal });
