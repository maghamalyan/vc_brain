import type {
  Candidate,
  CandidateDetailResponse,
  CandidateListResponse,
  CandidateQuery,
  ClaimResponse,
  DeepDiveAccepted,
  DeepDiveRun,
  DeepDiveRunSummary,
  DeepDiveRequest,
  EvidenceEvent,
  EvidenceQuery,
  EvidenceResponse,
  HealthResponse,
  Memo,
  Profile,
  SearchGroup,
  SearchHit,
  SearchDocumentType,
  SearchResponse,
  Thesis,
  ThreeAxis,
  TrajectoryPoint
} from './types';
import candidatesFixture from '../mocks/candidates.json';
import trajectoriesFixture from '../mocks/trajectories.json';
import eventsFixture from '../mocks/events.json';
import profilesFixture from '../mocks/profiles.json';
import thesisFixture from '../mocks/thesis.json';
import adaMemo from '../mocks/memos/ada-lovelace-fixture.json';
import graceMemo from '../mocks/memos/grace-hopper-fixture.json';
import katherineMemo from '../mocks/memos/katherine-johnson-fixture.json';
import adaDeepDive from '../mocks/deepdives/ada-lovelace-fixture.json';

export interface ApiClient {
  getHealth(): Promise<HealthResponse>;
  getThesis(): Promise<Thesis>;
  getCandidates(query?: CandidateQuery): Promise<CandidateListResponse>;
  getCandidate(login: string): Promise<CandidateDetailResponse>;
  getEvidence(login: string, query?: EvidenceQuery): Promise<EvidenceResponse>;
  getMemo(login: string): Promise<Memo>;
  getClaim(claimId: string): Promise<ClaimResponse>;
  search(query: string, types?: string[], limit?: number): Promise<SearchResponse>;
  getProfile(login: string): Promise<Profile | null>;
  getDeepDiveRuns(entityId: string): Promise<DeepDiveRunSummary[]>;
  getDeepDiveRun(runId: string): Promise<DeepDiveRun>;
  startDeepDive(body: DeepDiveRequest): Promise<DeepDiveAccepted>;
}

const API_ROOT = '/api/v1';

function params(values: Record<string, string | number | undefined>): string {
  const output = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) if (value !== undefined) output.set(key, String(value));
  const query = output.toString();
  return query ? `?${query}` : '';
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    headers: { Accept: 'application/json', ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...init?.headers }
  });
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json() as Promise<T>;
}

const realClient: ApiClient = {
  getHealth: () => request<HealthResponse>('/health'),
  getThesis: () => request<Thesis>('/thesis'),
  getCandidates: (query = {}) => request<CandidateListResponse>(`/candidates${params({ limit: 100, ...query })}`),
  getCandidate: (login) => request<CandidateDetailResponse>(`/candidates/${encodeURIComponent(login)}`),
  getEvidence: (login, query = {}) => request<EvidenceResponse>(`/candidates/${encodeURIComponent(login)}/evidence${params({ limit: 500, ...query })}`),
  getMemo: (login) => request<Memo>(`/candidates/${encodeURIComponent(login)}/memo`),
  getClaim: (claimId) => request<ClaimResponse>(`/claims/${encodeURIComponent(claimId)}`),
  search: (query, types, limit = 20) => request<SearchResponse>(`/search${params({ q: query, types: types?.join(','), limit })}`),
  getProfile: async () => null,
  getDeepDiveRuns: (entityId) => request<DeepDiveRunSummary[]>(`/deepdive/runs${params({ entity_id: entityId })}`),
  getDeepDiveRun: (runId) => request<DeepDiveRun>(`/deepdive/runs/${encodeURIComponent(runId)}`),
  startDeepDive: (body) => request<DeepDiveAccepted>('/deepdive', { method: 'POST', body: JSON.stringify(body) })
};

const candidates = (candidatesFixture as Omit<Candidate, 'has_memo'>[]).map((candidate) => ({
  ...candidate,
  has_memo: ['ada-lovelace-fixture', 'grace-hopper-fixture', 'katherine-johnson-fixture'].includes(candidate.gh_login)
}));
const trajectories = trajectoriesFixture as Array<TrajectoryPoint & { gh_login: string }>;
const events = eventsFixture as EvidenceEvent[];
const profiles = profilesFixture as Record<string, Profile>;
const thesis = thesisFixture as Thesis;
const mockDeepDives = [adaDeepDive as DeepDiveRun];
const memos: Record<string, Memo> = {
  'ada-lovelace-fixture': adaMemo as Memo,
  'grace-hopper-fixture': graceMemo as Memo,
  'katherine-johnson-fixture': katherineMemo as Memo
};

function countsFor(login: string): Record<string, number> {
  return events.filter((event) => event.gh_login === login).reduce<Record<string, number>>((counts, event) => {
    counts[event.event_type] = (counts[event.event_type] ?? 0) + 1;
    return counts;
  }, {});
}

function mark(value: string, query: string): string {
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return value.replace(new RegExp(`(${escaped})`, 'ig'), '<mark>$1</mark>');
}

function hit(docType: SearchDocumentType, docId: string, title: string, subtitle: string, body: string, route: string, query: string): SearchHit {
  return { doc_type: docType, doc_id: docId, title, subtitle, snippet: mark(body, query), route, score: 1 };
}

const mockClient: ApiClient = {
  async getHealth() { return { status: 'ok', index_built_at: '2026-07-19T00:00:00Z', counts: { candidates: candidates.length, events: events.length, claims: Object.values(memos).reduce((total, memo) => total + Object.keys(memo.claims).length, 0) } }; },
  async getThesis() { return structuredClone(thesis); },
  async getCandidates(query = {}) {
    let items = [...candidates];
    if (query.source) items = items.filter((item) => item.source === query.source);
    if (query.status) items = items.filter((item) => item.status === query.status);
    items.sort((a, b) => query.sort === 'momentum' ? b.momentum_3mo - a.momentum_3mo : b.current_score - a.current_score);
    const total = items.length;
    const start = query.offset ?? 0;
    return { items: items.slice(start, start + (query.limit ?? 100)), total };
  },
  async getCandidate(login) {
    const candidate = candidates.find((item) => item.gh_login === login);
    if (!candidate) throw new Error('Candidate not found');
    const memo = memos[login];
    return {
      candidate,
      trajectory: trajectories.filter((point) => point.gh_login === login).map(({ month, score }) => ({ month, score })),
      recognition: candidate.recognition ?? null,
      score_components: candidate.score_components ?? [],
      three_axis: memo?.three_axis as ThreeAxis ?? null,
      memo_available: Boolean(memo),
      evidence_counts_by_type: countsFor(login)
    };
  },
  async getEvidence(login, query = {}) {
    let items = events.filter((event) => event.gh_login === login);
    if (query.type) items = items.filter((event) => event.event_type === query.type);
    if (query.after) items = items.filter((event) => event.ts >= query.after!);
    if (query.before) items = items.filter((event) => event.ts <= query.before!);
    items.sort((a, b) => a.ts.localeCompare(b.ts));
    const total = items.length;
    return { items: items.slice(0, query.limit ?? 1000), total };
  },
  async getMemo(login) {
    const memo = memos[login];
    if (!memo) throw new Error('Memo not found');
    return structuredClone(memo);
  },
  async getClaim(claimId) {
    for (const memo of Object.values(memos)) {
      const claim = memo.claims[claimId];
      if (claim) return { claim, resolved_evidence: events.filter((event) => claim.evidence_refs.includes(event.evidence_id)) };
    }
    throw new Error('Claim not found');
  },
  async search(query, types, limit = 20) {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return { groups: [] };
    const groups: SearchGroup[] = [];
    const founderHits = candidates.filter((candidate) => `${candidate.founder_name} ${candidate.company} ${candidate.gh_login}`.toLowerCase().includes(normalized)).map((candidate) =>
      hit('founder', candidate.gh_login, candidate.founder_name?.replace(' (fixture)', '') ?? candidate.gh_login.replace('-fixture', ''), candidate.company ?? 'Company not disclosed', `${candidate.company ?? 'Company not disclosed'} · ${profiles[candidate.gh_login]?.sector ?? 'Founder'}`, `/candidate/${candidate.gh_login}`, query)
    );
    const claimHits = Object.entries(memos).flatMap(([login, memo]) => Object.entries(memo.claims).filter(([, claim]) => claim.text.toLowerCase().includes(normalized)).map(([id, claim]) =>
      hit('claim', id, memo.company ?? login.replace('-fixture', ''), 'Memo claim', claim.text, `/candidate/${login}#claim-${id}`, query)
    ));
    const sectorHits = thesis.sectors.filter((sector) => sector.toLowerCase().includes(normalized)).map((sector) =>
      hit('thesis_term', sector, sector, 'Thesis sector', `Filter radar to ${sector}`, `/?sector=${encodeURIComponent(sector)}`, query)
    );
    for (const [type, hits] of [['founder', founderHits], ['claim', claimHits], ['thesis_term', sectorHits]] as const) {
      if (hits.length && (!types || types.includes(type))) groups.push({ type, hits: hits.slice(0, limit) });
    }
    return { groups };
  },
  async getProfile(login) { return profiles[login] ?? null; },
  async getDeepDiveRuns(entityId) {
    return mockDeepDives.filter((run) => run.entity_id === entityId).map((run) => ({
      run_id: run.run_id,
      entity_id: run.entity_id,
      started_at: run.started_at,
      finished_at: run.finished_at,
      outcome: 'OK',
      claim_count: Object.keys(run.claims).length
    }));
  },
  async getDeepDiveRun(runId) {
    const run = mockDeepDives.find((item) => item.run_id === runId);
    if (!run) throw new Error('Deep-dive run not found');
    return structuredClone(run);
  },
  async startDeepDive(body) { return { run_id: `mock-${body.entity_id}` }; }
};

export const api: ApiClient = import.meta.env.VITE_MOCK === '1' ? mockClient : realClient;
export const isMockMode = import.meta.env.VITE_MOCK === '1';
export const isDeepDiveEnabled = import.meta.env.VITE_DEEPDIVE_ENABLED !== '0';
