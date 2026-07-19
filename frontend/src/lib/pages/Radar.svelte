<script lang="ts">
  import { onMount } from 'svelte';
  import { flip } from 'svelte/animate';
  import { api } from '../api/client';
  import type { Candidate, CandidateDetailResponse, EvidenceEvent, Profile, RecognitionKind, Thesis, TrajectoryPoint } from '../api/types';
  import { navigate } from '../router';
  import Chip from '../components/Chip.svelte';
  import MiniArea from '../components/MiniArea.svelte';
  import MiniBars from '../components/MiniBars.svelte';
  import { setThesisFilter, setThesisWeight, thesisSettings, toggleThesisFilter } from '../thesisStore';

  type RankedCandidate = Candidate & {
    profile: Profile | null;
    adjusted: number;
    originalRank: number;
    rankDelta: number;
    evidenceCount: number;
    historicalScore: number;
    historicalMomentum: number;
    detected: boolean;
  };

  type ProofChart = {
    path: string;
    detectionX: number;
    detectionY: number;
    recognitionX: number;
    recognitionY: number;
  };

  let candidates: Candidate[] = [];
  let thesis: Thesis | null = null;
  let profiles: Record<string, Profile | null> = {};
  let evidence: Record<string, EvidenceEvent[]> = {};
  let details: Record<string, CandidateDetailResponse | null> = {};
  let loading = true;
  let selected = 0;
  let radarElement: HTMLElement;
  let scrubberIndex = Number.MAX_SAFE_INTEGER;
  let reducedMotion = false;
  let previousSelectedMonth = '';
  let detectionFlashes = new Set<string>();

  const detailQueue: string[] = [];
  const queuedDetails = new Set<string>();
  const axisOrder = ['founder', 'market', 'idea_vs_market'] as const;
  const axisLabels = { founder: 'Founder', market: 'Market', idea_vs_market: 'Idea ↔ market' };
  let activeDetailLoads = 0;

  const monthLabel = (month: string) => {
    const parsed = new Date(`${month}-01T00:00:00Z`);
    return Number.isNaN(parsed.valueOf()) ? '—' : new Intl.DateTimeFormat('en', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(parsed);
  };
  const monthShort = (month: string) => {
    const parsed = new Date(`${month}-01T00:00:00Z`);
    return Number.isNaN(parsed.valueOf()) ? '—' : new Intl.DateTimeFormat('en', { month: 'short', timeZone: 'UTC' }).format(parsed);
  };
  const shortName = (name: string | null, login = 'Founder') => name?.replace(' (fixture)', '') ?? login.replace('-fixture', '');
  const sourceLabel = (source: string) => source === 'outbound_detector' ? 'Outbound signal' : 'Inbound deck';

  function sortedTrajectory(candidate: Candidate): TrajectoryPoint[] {
    return [...(candidate.trajectory ?? [])].sort((a, b) => a.month.localeCompare(b.month));
  }

  function trajectoryPointAtMonth(candidate: Candidate, month: string): TrajectoryPoint {
    const trajectory = sortedTrajectory(candidate);
    // Trajectory is OPTIONAL upstream (D1 addendum) — degrade to the current
    // score rather than crashing the whole radar.
    if (!trajectory.length) return { month: `${month}-01`, score: candidate.current_score };
    const exact = trajectory.find((point) => point.month.slice(0, 7) === month);
    if (exact) return exact;
    if (month <= trajectory[0].month.slice(0, 7)) return trajectory[0];
    return trajectory.at(-1)!;
  }

  function trajectoryValueAtMonth(candidate: Candidate, month: string): number {
    return trajectoryPointAtMonth(candidate, month).score;
  }

  function momentumAtMonth(candidate: Candidate, month: string): number {
    const trajectory = sortedTrajectory(candidate);
    if (trajectory.length < 2) return 0;
    const target = trajectoryPointAtMonth(candidate, month);
    const targetIndex = Math.max(0, trajectory.findIndex((point) => point.month === target.month));
    const window = trajectory.slice(Math.max(0, targetIndex - 3), targetIndex + 1);
    return window.length < 2 ? 0 : (window.at(-1)!.score - window[0].score) / (window.length - 1);
  }

  function isDetectedAtMonth(candidate: Candidate, month: string): boolean {
    return Boolean(candidate.first_detection_month && candidate.first_detection_month.slice(0, 7) <= month);
  }

  function scoreColor(score: number): string {
    const start = [196, 205, 198];
    const end = [25, 79, 60];
    const scores = candidates.map((candidate) => trajectoryValueAtMonth(candidate, selectedMonth));
    const low = Math.min(...scores, score);
    const high = Math.max(...scores, score);
    const ratio = high - low < 0.01 ? 1 : Math.max(0, Math.min(1, (score - low) / (high - low)));
    return `rgb(${start.map((value, index) => Math.round(value + (end[index] - value) * ratio)).join(',')})`;
  }

  function trajectoryValues(candidate: Candidate): number[] {
    const trajectory = sortedTrajectory(candidate);
    const visible = trajectory.filter((point) => point.month.slice(0, 7) <= selectedMonth).map((point) => point.score);
    return visible.length ? visible : [trajectoryPointAtMonth(candidate, selectedMonth).score];
  }

  function shortRecognitionKind(kind: RecognitionKind): string {
    return kind === 'seed_round' ? 'seed' : kind === 'yc_batch' ? 'YC batch' : 'press';
  }

  function statusLabel(candidate: Candidate): string {
    if (candidate.recognition && (candidate.lead_time_months ?? 0) > 0) return `flagged ${candidate.lead_time_months} mo before ${shortRecognitionKind(candidate.recognition.kind)}`;
    if (!candidate.recognition) return 'still ahead of the market';
    return 'recognized before detection';
  }

  function evidenceHook(candidate: Candidate, items: EvidenceEvent[]): string {
    // `items` passed in so the template expression re-evaluates when the async
    // evidence load resolves (same hidden-dependency trap as trajectoryValues).
    const detectionMonth = candidate.first_detection_month?.slice(0, 7);
    return items.find((event) => event.ts.slice(0, 7) === detectionMonth)?.detail ?? items[0]?.detail ?? 'Evidence not yet observed.';
  }

  function proofChart(candidate: Candidate): ProofChart {
    const width = 280;
    const height = 82;
    const padding = 7;
    const trajectory = sortedTrajectory(candidate);
    const scores = trajectory.map((point) => point.score);
    const low = Math.min(...scores);
    const high = Math.max(...scores);
    const range = Math.max(high - low, 0.001);
    const xAt = (index: number) => padding + index / Math.max(trajectory.length - 1, 1) * (width - padding * 2);
    const yAt = (score: number) => height - padding - (score - low) / range * (height - padding * 2);
    const pointIndex = (month: string) => {
      const normalized = month.slice(0, 7);
      const exact = trajectory.findIndex((point) => point.month.slice(0, 7) === normalized);
      if (exact >= 0) return exact;
      if (normalized <= trajectory[0].month.slice(0, 7)) return 0;
      return trajectory.length - 1;
    };
    const detectionIndex = pointIndex(candidate.first_detection_month ?? trajectory[0].month);
    const recognitionIndex = pointIndex(candidate.recognition?.month ?? trajectory.at(-1)!.month);
    return {
      path: trajectory.map((point, index) => `${index ? 'L' : 'M'} ${xAt(index).toFixed(2)} ${yAt(point.score).toFixed(2)}`).join(' '),
      detectionX: xAt(detectionIndex),
      detectionY: yAt(trajectory[detectionIndex].score),
      recognitionX: xAt(recognitionIndex),
      recognitionY: yAt(trajectory[recognitionIndex].score)
    };
  }

  function markDetectionCrossings(month: string): void {
    if (!month) return;
    if (previousSelectedMonth && previousSelectedMonth !== month) {
      const crossed = candidates.filter((candidate) => {
        const detection = candidate.first_detection_month?.slice(0, 7);
        return detection && ((previousSelectedMonth < detection && month >= detection) || (previousSelectedMonth >= detection && month < detection));
      }).map((candidate) => candidate.gh_login);
      if (crossed.length) {
        detectionFlashes = new Set([...detectionFlashes, ...crossed]);
        window.setTimeout(() => {
          detectionFlashes = new Set([...detectionFlashes].filter((login) => !crossed.includes(login)));
        }, reducedMotion ? 80 : 760);
      }
    }
    previousSelectedMonth = month;
  }

  function pumpDetailQueue(): void {
    while (activeDetailLoads < 3 && detailQueue.length) {
      const login = detailQueue.shift();
      if (!login) return;
      activeDetailLoads += 1;
      void api.getCandidate(login)
        .then((detail) => { details = { ...details, [login]: detail }; })
        .catch(() => { details = { ...details, [login]: null }; })
        .finally(() => {
          activeDetailLoads -= 1;
          pumpDetailQueue();
        });
    }
  }

  function queueCandidateDetail(login: string): void {
    if (login in details || queuedDetails.has(login)) return;
    queuedDetails.add(login);
    detailQueue.push(login);
    pumpDetailQueue();
  }

  function observeCandidate(node: HTMLElement, login: string): { destroy: () => void } {
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        queueCandidateDetail(login);
        observer.disconnect();
      }
    }, { rootMargin: '240px 0px' });
    observer.observe(node);
    return { destroy: () => observer.disconnect() };
  }

  function onRadarKeydown(event: KeyboardEvent): void {
    const target = event.target as HTMLElement;
    if (['INPUT', 'BUTTON', 'SELECT'].includes(target.tagName)) return;
    if (event.key.toLowerCase() === 'j') { event.preventDefault(); selected = Math.min(selected + 1, ranked.length - 1); }
    if (event.key.toLowerCase() === 'k') { event.preventDefault(); selected = Math.max(selected - 1, 0); }
    if (event.key === 'Enter' && ranked[selected]) { event.preventDefault(); navigate(`/candidate/${ranked[selected].gh_login}`); }
  }

  onMount(async () => {
    reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const requestedSector = new URLSearchParams(location.search).get('sector');
    if (requestedSector) setThesisFilter('sector', requestedSector);
    const [candidateResponse, thesisResponse] = await Promise.all([api.getCandidates(), api.getThesis()]);
    candidates = candidateResponse.items;
    thesis = thesisResponse;
    const supportRows = await Promise.all(candidates.map(async (candidate) => {
      const [profile, eventResponse] = await Promise.all([api.getProfile(candidate.gh_login), api.getEvidence(candidate.gh_login)]);
      return [candidate.gh_login, profile, eventResponse.items] as const;
    }));
    profiles = Object.fromEntries(supportRows.map(([login, profile]) => [login, profile]));
    evidence = Object.fromEntries(supportRows.map(([login, , items]) => [login, items]));
    loading = false;
    requestAnimationFrame(() => radarElement?.focus({ preventScroll: true }));
  });

  $: months = Array.from(new Set(candidates.flatMap((candidate) => (candidate.trajectory ?? []).map((point) => point.month.slice(0, 7))))).sort();
  $: if (months.length && scrubberIndex >= months.length) scrubberIndex = months.length - 1;
  $: selectedMonth = months[scrubberIndex] ?? months.at(-1) ?? '';
  $: scrubberLabelStep = Math.max(1, Math.ceil(months.length / 12));
  $: years = months.reduce<Array<{ year: string; index: number }>>((items, month, index) => {
    const year = month.slice(0, 4);
    if (items.at(-1)?.year !== year) items.push({ year, index });
    return items;
  }, []);
  $: scrubberPosition = months.length > 1 ? scrubberIndex / (months.length - 1) * 100 : 0;
  $: monthEvidenceCounts = months.map((month) => Object.values(evidence).reduce((total, events) => total + events.filter((event) => event.ts.slice(0, 7) === month).length, 0));
  $: baseOrder = [...candidates].sort((a, b) => trajectoryValueAtMonth(b, selectedMonth) - trajectoryValueAtMonth(a, selectedMonth));
  $: ranked = candidates.map((candidate): RankedCandidate => {
    const profile = profiles[candidate.gh_login] ?? null;
    const fitMatches = [!$thesisSettings.sector || profile?.sector === $thesisSettings.sector, !$thesisSettings.stage || profile?.stage === $thesisSettings.stage, !$thesisSettings.geography || profile?.geography === $thesisSettings.geography];
    const fit = fitMatches.filter(Boolean).length / 3;
    const historicalScore = trajectoryValueAtMonth(candidate, selectedMonth);
    const historicalMomentum = momentumAtMonth(candidate, selectedMonth);
    const adjusted = historicalScore * $thesisSettings.signalWeight / 100 + Math.max(0, historicalMomentum * 4) * $thesisSettings.momentumWeight / 100 + fit * $thesisSettings.thesisWeight / 100;
    const originalRank = baseOrder.findIndex((item) => item.gh_login === candidate.gh_login) + 1;
    return { ...candidate, profile, adjusted, originalRank, rankDelta: 0, historicalScore, historicalMomentum, detected: isDetectedAtMonth(candidate, selectedMonth), evidenceCount: (evidence[candidate.gh_login] ?? []).filter((event) => event.ts.slice(0, 7) <= selectedMonth).length };
  }).sort((a, b) => b.adjusted - a.adjusted).map((candidate, index) => ({ ...candidate, rankDelta: candidate.originalRank - (index + 1) }));
  $: proofCases = candidates.filter((candidate) => (candidate.lead_time_months ?? 0) > 0 && candidate.recognition).sort((a, b) => (b.lead_time_months ?? 0) - (a.lead_time_months ?? 0)).slice(0, 3);
  $: honestMiss = candidates.find((candidate) => (candidate.lead_time_months ?? 0) < 0) ?? null;
  $: markDetectionCrossings(selectedMonth);
  $: if (selected >= ranked.length) selected = Math.max(0, ranked.length - 1);
</script>

<section class="scrubber-ribbon" aria-label="Evidence time scrubber">
  <div class="shell scrubber-inner">
    <div class="scrubber-copy"><span class="eyebrow">Intelligence as of</span><strong aria-live="polite">{monthLabel(selectedMonth)}</strong></div>
    <div class="scrubber-control">
      <div class="scrubber-years" aria-hidden="true">
        {#each years as item}<span style:left={`${item.index / (months.length - 1) * 100}%`}>{item.year}</span>{/each}
        <small>Badges count evidence events across candidates</small>
      </div>
      <div class="scrubber-ticks" aria-hidden="true">
        {#each months as month, index}
          <span class="scrubber-month" data-testid="scrubber-month-tick" style:left={`${index / (months.length - 1) * 100}%`}>
            {#if monthEvidenceCounts[index] > 0}<b title={`${monthEvidenceCounts[index]} evidence events across candidates`}>{monthEvidenceCounts[index]}</b>{/if}
            <i class:major={month.endsWith('-01')}></i>
            <em>{index % scrubberLabelStep === 0 || index === months.length - 1 ? monthShort(month) : ''}</em>
          </span>
        {/each}
      </div>
      <input
        aria-label="Filter evidence by month"
        aria-valuetext={monthLabel(selectedMonth)}
        data-testid="radar-scrubber"
        type="range"
        min="0"
        max={months.length - 1}
        bind:value={scrubberIndex}
      />
      <span class="scrubber-knob" aria-hidden="true" style:left={`${scrubberPosition}%`}></span>
      {#if scrubberIndex < months.length - 1}<span class="scrubber-honesty" style:left={`${scrubberPosition}%`}>Future evidence hidden</span>{/if}
    </div>
  </div>
</section>

<section class="radar-hero shell">
  <div>
    <p class="eyebrow"><span>Live thesis radar</span> · Evidence-weighted</p>
    <h1>See the founder<br />before the round.</h1>
  </div>
  <div class="hero-note"><span>FIELD NOTE / 07</span><p>Ranked signals are a starting point, not a verdict. Every movement stays traceable to thesis weights and observed evidence.</p></div>
</section>

<section class="foresight-strip shell" id="proof" aria-labelledby="proof-title">
  <header class="proof-heading">
    <div><p class="eyebrow">Foresight proof · observed outcomes</p><h2 id="proof-title">The signal arrived before the market.</h2></div>
    <p>Detection and recognition are separate timestamps. The space between them is the result—not a backfilled claim.</p>
  </header>
  <div class="proof-grid">
    {#each proofCases as candidate}
      {@const chart = proofChart(candidate)}
      <a class="proof-card" href={`/candidate/${candidate.gh_login}`} onclick={(event) => { event.preventDefault(); navigate(`/candidate/${candidate.gh_login}`); }}>
        <div class="proof-number"><strong>{candidate.lead_time_months}</strong><span>months early</span></div>
        <svg class="proof-trajectory" viewBox="0 0 280 82" role="img" aria-label={`${shortName(candidate.founder_name)} trajectory from detection to ${candidate.recognition?.label}`} preserveAspectRatio="none">
          <rect class="lead-band" x={chart.detectionX} y="0" width={Math.max(0, chart.recognitionX - chart.detectionX)} height="82" />
          <path d={chart.path} />
          <line class="detection-marker" x1={chart.detectionX} x2={chart.detectionX} y1="0" y2="82" />
          <circle class="detection-dot" cx={chart.detectionX} cy={chart.detectionY} r="4" />
          <line class="recognition-marker" x1={chart.recognitionX} x2={chart.recognitionX} y1="0" y2="82" />
          <circle class="recognition-dot" cx={chart.recognitionX} cy={chart.recognitionY} r="3" />
        </svg>
        <div class="proof-legend"><span><i class="detection"></i>Detected {monthShort(candidate.first_detection_month!.slice(0, 7))}</span><span><i class="recognition"></i>{shortRecognitionKind(candidate.recognition!.kind)} {monthShort(candidate.recognition!.month)}</span></div>
        <h3>{shortName(candidate.founder_name)} <span>· {candidate.company}</span></h3>
        <p>{evidenceHook(candidate, evidence[candidate.gh_login] ?? [])}</p>
        <span class="proof-open">Open evidence record <b aria-hidden="true">↗</b></span>
      </a>
    {/each}
  </div>
  {#if honestMiss}
    <a class="honest-miss" href={`/candidate/${honestMiss.gh_login}`} onclick={(event) => { event.preventDefault(); navigate(`/candidate/${honestMiss.gh_login}`); }}>
      <span>Honest miss</span><p><strong>What we miss, we show</strong> — {shortName(honestMiss.founder_name)} was recognized before our detector fired.</p><b aria-hidden="true">↗</b>
    </a>
  {/if}
</section>

<section class="radar-workspace shell">
  <aside class="thesis-controls" aria-labelledby="thesis-title">
    <div class="panel-heading"><div><p class="eyebrow">Investment lens</p><h2 id="thesis-title">Thesis controls</h2></div><span class="control-count">03</span></div>
    {#if thesis}
      <fieldset><legend>Sector preference</legend><div class="toggle-cloud">{#each thesis.sectors as item}<Chip variant="filter" label={item} active={$thesisSettings.sector === item} pressed={$thesisSettings.sector === item} onclick={() => toggleThesisFilter('sector', item)} />{/each}</div></fieldset>
      <fieldset><legend>Stage</legend><div class="toggle-cloud">{#each thesis.stages as item}<Chip variant="filter" label={item} active={$thesisSettings.stage === item} pressed={$thesisSettings.stage === item} onclick={() => toggleThesisFilter('stage', item)} />{/each}</div></fieldset>
      <fieldset><legend>Geography</legend><div class="toggle-cloud compact">{#each thesis.geographies as item}<Chip variant="filter" label={item} active={$thesisSettings.geography === item} pressed={$thesisSettings.geography === item} onclick={() => toggleThesisFilter('geography', item)} />{/each}</div></fieldset>
      <div class="weight-block">
        <div class="weight-heading"><legend>Ranking weights</legend><span>{$thesisSettings.signalWeight + $thesisSettings.momentumWeight + $thesisSettings.thesisWeight} pts</span></div>
        <label><span>Signal strength <b>{$thesisSettings.signalWeight}</b></span><input aria-label="Signal strength weight" type="range" min="0" max="100" value={$thesisSettings.signalWeight} oninput={(event) => setThesisWeight('signalWeight', Number(event.currentTarget.value))} /></label>
        <label><span>Momentum <b>{$thesisSettings.momentumWeight}</b></span><input aria-label="Momentum weight" type="range" min="0" max="100" value={$thesisSettings.momentumWeight} oninput={(event) => setThesisWeight('momentumWeight', Number(event.currentTarget.value))} /></label>
        <label><span>Thesis fit <b>{$thesisSettings.thesisWeight}</b></span><input aria-label="Thesis fit weight" type="range" min="0" max="100" value={$thesisSettings.thesisWeight} oninput={(event) => setThesisWeight('thesisWeight', Number(event.currentTarget.value))} /></label>
      </div>
      <p class="thesis-note">{thesis.risk_appetite}</p>
    {/if}
  </aside>

  <div class="radar-list-panel" bind:this={radarElement} tabindex="0" role="grid" aria-label="Ranked founder candidates" onkeydown={onRadarKeydown}>
    <header class="list-heading"><div><p class="eyebrow">{loading ? 'Loading signals' : `${ranked.length} candidates`}</p><h2>Founder radar</h2></div><div class="keyboard-hint"><kbd>J</kbd><kbd>K</kbd> move <kbd>↵</kbd> open</div></header>
    <div class="list-columns" aria-hidden="true"><span>Rank / opportunity</span><span>Trajectory to cutoff</span><span>Independent axes</span><span>Velocity / evidence</span><span>Signal</span></div>
    {#if loading}
      <div class="loading-list" aria-live="polite">Calibrating the radar…</div>
    {:else}
      <div class="candidate-list">
        {#each ranked as candidate, index (candidate.gh_login)}
          {@const detail = details[candidate.gh_login]}
          <div
            animate:flip={{ duration: reducedMotion ? 0 : 280 }}
            class:selected={index === selected}
            class:not-yet-detected={!candidate.detected}
            class:detection-crossing={detectionFlashes.has(candidate.gh_login)}
            class="candidate-row"
            role="row"
            aria-selected={index === selected}
            data-login={candidate.gh_login}
            data-trajectory-score={candidate.historicalScore}
            use:observeCandidate={candidate.gh_login}
            style:--score-color={scoreColor(candidate.historicalScore)}
          >
            <button class="candidate-main" type="button" onfocus={() => selected = index} onclick={() => navigate(`/candidate/${candidate.gh_login}`)} aria-label={`Open ${shortName(candidate.founder_name)} record; ${candidate.has_memo ? 'memo available' : 'no memo available'}`}>
              <span class="rank-number">{String(index + 1).padStart(2, '0')}</span>
              <span class="avatar" aria-hidden="true">{shortName(candidate.founder_name, candidate.gh_login).split(' ').map((part) => part[0]).slice(0,2).join('')}</span>
              <span class="candidate-name">
                <strong>{shortName(candidate.founder_name, candidate.gh_login)}</strong>
                <small>{candidate.company ?? 'Company not disclosed'} · @{candidate.gh_login.replace('-fixture', '')}</small>
                <span class="candidate-badges">
                  <span class="source-badge source-{candidate.source}">{sourceLabel(candidate.source)}</span>
                  <span class="memo-badge memo-{candidate.has_memo ? 'available' : 'unavailable'}" data-testid="memo-status" data-state={candidate.has_memo ? 'available' : 'unavailable'}>{candidate.has_memo ? 'Memo available' : 'No memo'}</span>
                </span>
              </span>
            </button>
            <div class="trajectory-cell" style:--forest={scoreColor(candidate.historicalScore)}>
              <MiniArea values={trajectoryValues(candidate)} width={90} height={30} label={`${shortName(candidate.founder_name)} signal trajectory through ${monthLabel(selectedMonth)}`} />
              <small>{trajectoryValues(candidate).length} observed months</small>
            </div>
            <div class="row-axes">
              {#if detail?.three_axis}
                {#each axisOrder as axis}
                  <div><span>{axisLabels[axis]}</span><MiniBars values={Array.from({ length: 10 }, (_, bar) => bar < Math.round(detail.three_axis?.[axis].score ?? 0) ? 1 : 0)} width={72} height={7} label={`${axisLabels[axis]} ${detail.three_axis[axis].score.toFixed(1)} out of 10`} segments /><strong>{detail.three_axis[axis].score.toFixed(1)}</strong></div>
                {/each}
              {:else}
                <span class="axes-pending">{candidate.has_memo ? 'Loading memo axes…' : 'Axes not yet observed'}</span>
              {/if}
              <small>{candidate.profile?.sector ?? 'Technical founder'} · {candidate.profile?.stage ?? 'Early stage'}</small>
            </div>
            <div class="row-chips">
              <span class:negative={candidate.historicalMomentum < 0}><Chip variant="event" label={`${candidate.historicalMomentum >= 0 ? '↑' : '↓'} ${Math.abs(candidate.historicalMomentum * 100).toFixed(1)}% · 3mo slope`} /></span>
              <Chip variant="event" label={`${candidate.evidenceCount} evidence`} />
            </div>
            <div class="score-cell">
              {#if candidate.detected}<strong data-testid="historical-score">{Math.round(candidate.historicalScore * 100)}</strong><span>as of {monthShort(selectedMonth)}</span>
              {:else}<small>Not yet detected</small>{/if}
            </div>
            <span class:lead-positive={(candidate.lead_time_months ?? 0) > 0} class:lead-live={!candidate.recognition} class:lead-miss={(candidate.lead_time_months ?? 0) < 0} class="lead-time-chip"><Chip variant="status" tone={!candidate.recognition ? 'live' : (candidate.lead_time_months ?? 0) > 0 ? 'forest' : ''} label={statusLabel(candidate)} /></span>
            <div class:up={candidate.rankDelta > 0} class:down={candidate.rankDelta < 0} class="rank-reason">
              {#if candidate.rankDelta > 0}↑ Moved {candidate.rankDelta} {candidate.rankDelta === 1 ? 'place' : 'places'} on thesis fit
              {:else if candidate.rankDelta < 0}↓ Moved {Math.abs(candidate.rankDelta)} on current weights
              {:else}— Holding baseline rank{/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</section>
