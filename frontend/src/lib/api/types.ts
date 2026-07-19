export type VerificationStatus = 'verified' | 'single_source' | 'unverified' | 'not_disclosed';
export type AxisKey = 'founder' | 'market' | 'idea_vs_market';
export type CandidateSource = 'outbound_detector' | 'inbound_application';
export type CandidateStatus = 'candidate' | 'screened' | 'memo_ready';
export type SearchDocumentType = 'founder' | 'company' | 'claim' | 'evidence' | 'memo_section' | 'thesis_term';
export type RecognitionKind = 'yc_batch' | 'seed_round' | 'press';

export interface Recognition {
  month: string;
  kind: RecognitionKind;
  label: string;
}

export interface TrajectoryPoint {
  month: string;
  score: number;
}

export interface ScoreComponent {
  key: string;
  label: string;
  contribution: number;
}

export interface Candidate {
  gh_login: string;
  founder_name: string | null;
  company: string | null;
  source: CandidateSource;
  current_score: number;
  score_percentile: number;
  momentum_3mo: number;
  first_detection_month: string | null;
  status: CandidateStatus;
  has_memo: boolean;
  recognition?: Recognition | null;
  score_components?: ScoreComponent[];
  lead_time_months?: number | null;
  trajectory?: TrajectoryPoint[];
}

export interface Profile {
  sector: string;
  stage: string;
  geography: string;
  round_size_usd: number;
}

export interface AxisValue {
  score: number;
  trend: 'improving' | 'stable' | 'declining';
  claim_ids: string[];
}

export type ThreeAxis = Record<AxisKey, AxisValue>;

export interface EvidenceEvent {
  evidence_id: string;
  gh_login: string;
  ts: string;
  event_type: string;
  repo_name: string;
  detail: string;
  url: string;
  provenance?: 'backtest' | 'live';
}

export interface Claim {
  text: string;
  evidence_refs: string[];
  confidence: number;
  verification_status: VerificationStatus;
  contradictions: string[];
}

export interface MemoTextSection { text: string; claim_ids: string[] }
export interface SwotSection {
  strengths: MemoTextSection[];
  weaknesses: MemoTextSection[];
  opportunities: MemoTextSection[];
  risks: MemoTextSection[];
}
export interface MemoSections {
  company_snapshot: MemoTextSection;
  investment_hypotheses: MemoTextSection[];
  swot: SwotSection;
  problem_product: MemoTextSection;
  traction_kpis: MemoTextSection;
}
export interface Memo {
  company: string | null;
  founder_logins: string[];
  generated_at: string;
  sections: MemoSections;
  claims: Record<string, Claim>;
  gaps: string[];
  three_axis: ThreeAxis;
}

export interface Thesis {
  sectors: string[];
  stages: string[];
  geographies: string[];
  check_size_usd: [number, number];
  risk_appetite: string;
  notes: string;
}

export interface CandidateListResponse { items: Candidate[]; total: number }
export interface CandidateDetailResponse {
  candidate: Candidate;
  trajectory: TrajectoryPoint[];
  recognition?: Recognition | null;
  score_components?: ScoreComponent[];
  three_axis: ThreeAxis | null;
  memo_available: boolean;
  evidence_counts_by_type: Record<string, number>;
}
export interface EvidenceResponse { items: EvidenceEvent[]; total: number }
export interface ClaimResponse { claim: Claim; resolved_evidence: Array<EvidenceEvent | { url: string }> }
export interface SearchHit {
  doc_type: SearchDocumentType;
  doc_id: string;
  title: string;
  subtitle: string;
  snippet: string;
  route: string;
  score: number;
}
export interface SearchGroup { type: SearchDocumentType; hits: SearchHit[] }
export interface SearchResponse { groups: SearchGroup[] }

export interface HealthResponse {
  status: 'ok';
  index_built_at: string;
  counts: { candidates: number; events: number; claims: number };
}

export type RunStepKind = 'plan' | 'fetch' | 'sql' | 'evidence' | 'reason' | 'claim' | 'gap' | 'done' | 'error';
export interface RunStep {
  seq: number;
  kind: RunStepKind;
  label: string;
  detail: string;
  ts: string;
  payload?: Record<string, unknown>;
}
export type DeepDiveDimension = AxisKey;
export interface DeepDiveRequest {
  entity_type: 'founder';
  entity_id: string;
  dimensions: DeepDiveDimension[];
  mode?: 'live' | 'replay';
}
export interface DeepDiveAccepted { run_id: string }
export type DeepDiveOutcome = 'OK' | 'INSUFFICIENT_EVIDENCE' | 'ERROR';
export interface DeepDiveRunSummary {
  run_id: string;
  entity_id: string;
  started_at: string;
  finished_at: string | null;
  outcome: DeepDiveOutcome | null;
  claim_count: number;
}
export interface DeepDiveRun {
  run_id: string;
  entity_id: string;
  provenance: 'live';
  started_at: string;
  finished_at: string | null;
  steps: RunStep[];
  evidence: EvidenceEvent[];
  claims: Record<string, Claim>;
  dimension_notes: Partial<ThreeAxis>;
  gaps: string[];
  model: string;
  token_usage: Record<string, number>;
}

export interface CandidateQuery {
  source?: string;
  status?: string;
  sort?: 'score' | 'momentum';
  limit?: number;
  offset?: number;
}
export interface EvidenceQuery {
  type?: string;
  after?: string;
  before?: string;
  limit?: number;
}
