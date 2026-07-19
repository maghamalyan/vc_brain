<script lang="ts">
  import { onMount } from 'svelte';
  import { flip } from 'svelte/animate';
  import { api } from '../api/client';
  import type { Candidate, CandidateDetailResponse, EvidenceEvent, Profile, Thesis } from '../api/types';
  import { navigate } from '../router';
  import Chip from '../components/Chip.svelte';
  import MiniArea from '../components/MiniArea.svelte';
  import MiniBars from '../components/MiniBars.svelte';

  type RankedCandidate = Candidate & {
    profile: Profile | null;
    adjusted: number;
    originalRank: number;
    rankDelta: number;
    evidenceCount: number;
  };

  let candidates: Candidate[] = [];
  let thesis: Thesis | null = null;
  let profiles: Record<string, Profile | null> = {};
  let evidence: Record<string, EvidenceEvent[]> = {};
  let details: Record<string, CandidateDetailResponse | null> = {};
  let loading = true;
  let selected = 0;
  let radarElement: HTMLElement;
  let signalWeight = 64;
  let momentumWeight = 22;
  let thesisWeight = 14;
  let sector = new URLSearchParams(location.search).get('sector') ?? '';
  let stage = '';
  let geography = '';
  let scrubberIndex = 23;
  let reducedMotion = false;

  const detailQueue: string[] = [];
  const queuedDetails = new Set<string>();
  const axisOrder = ['founder', 'market', 'idea_vs_market'] as const;
  const axisLabels = { founder: 'Founder', market: 'Market', idea_vs_market: 'Idea ↔ market' };
  let activeDetailLoads = 0;

  const months = Array.from({ length: 24 }, (_, index) => {
    const date = new Date(Date.UTC(2024, 7 + index, 1));
    return date.toISOString().slice(0, 7);
  });
  const years = months.reduce<Array<{ year: string; index: number }>>((items, month, index) => {
    const year = month.slice(0, 4);
    if (items.at(-1)?.year !== year) items.push({ year, index });
    return items;
  }, []);

  const monthLabel = (month: string) => new Intl.DateTimeFormat('en', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${month}-01T00:00:00Z`));
  const monthShort = (month: string) => new Intl.DateTimeFormat('en', { month: 'short', timeZone: 'UTC' }).format(new Date(`${month}-01T00:00:00Z`));
  const shortName = (name: string | null, login = 'Founder') => name?.replace(' (fixture)', '') ?? login.replace('-fixture', '');
  const sourceLabel = (source: string) => source === 'outbound_detector' ? 'Outbound signal' : 'Inbound deck';

  function scoreAtMonth(candidate: Candidate, month: string): number {
    const items = evidence[candidate.gh_login] ?? [];
    const total = items.length || 1;
    const visible = items.filter((event) => event.ts.slice(0, 7) <= month).length;
    const maturity = 0.58 + 0.42 * visible / total;
    return candidate.current_score * maturity;
  }

  function scoreColor(score: number): string {
    const start = [196, 205, 198];
    const end = [25, 79, 60];
    const scores = candidates.map((candidate) => scoreAtMonth(candidate, selectedMonth));
    const low = Math.min(...scores, score);
    const high = Math.max(...scores, score);
    const ratio = high - low < 0.01 ? 1 : Math.max(0, Math.min(1, (score - low) / (high - low)));
    return `rgb(${start.map((value, index) => Math.round(value + (end[index] - value) * ratio)).join(',')})`;
  }

  function trajectoryValues(candidate: Candidate, detail: CandidateDetailResponse | null): number[] {
    // `detail` is passed in (not read from `details` here) so the template
    // expression re-evaluates when the lazy per-row fetch resolves.
    const trajectory = detail?.trajectory ?? [];
    const visible = trajectory.filter((point) => point.month.slice(0, 7) <= selectedMonth).map((point) => point.score);
    return visible.length ? visible : [scoreAtMonth(candidate, selectedMonth)];
  }

  function toggle(current: string, value: string): string { return current === value ? '' : value; }

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

  $: selectedMonth = months[scrubberIndex];
  $: scrubberPosition = months.length > 1 ? scrubberIndex / (months.length - 1) * 100 : 0;
  $: monthEvidenceCounts = months.map((month) => Object.values(evidence).reduce((total, events) => total + events.filter((event) => event.ts.slice(0, 7) === month).length, 0));
  $: baseOrder = [...candidates].sort((a, b) => b.current_score - a.current_score);
  $: ranked = candidates.map((candidate): RankedCandidate => {
    const profile = profiles[candidate.gh_login] ?? null;
    const fitMatches = [!sector || profile?.sector === sector, !stage || profile?.stage === stage, !geography || profile?.geography === geography];
    const fit = fitMatches.filter(Boolean).length / 3;
    const adjusted = scoreAtMonth(candidate, selectedMonth) * signalWeight / 100 + Math.max(0, candidate.momentum_3mo * 4) * momentumWeight / 100 + fit * thesisWeight / 100;
    const originalRank = baseOrder.findIndex((item) => item.gh_login === candidate.gh_login) + 1;
    return { ...candidate, profile, adjusted, originalRank, rankDelta: 0, evidenceCount: (evidence[candidate.gh_login] ?? []).filter((event) => event.ts.slice(0, 7) <= selectedMonth).length };
  }).sort((a, b) => b.adjusted - a.adjusted).map((candidate, index) => ({ ...candidate, rankDelta: candidate.originalRank - (index + 1) }));
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
            <em>{index % 3 === 0 || index === months.length - 1 ? monthShort(month) : ''}</em>
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

<section class="radar-workspace shell">
  <aside class="thesis-controls" aria-labelledby="thesis-title">
    <div class="panel-heading"><div><p class="eyebrow">Investment lens</p><h2 id="thesis-title">Thesis controls</h2></div><span class="control-count">03</span></div>
    {#if thesis}
      <fieldset><legend>Sector preference</legend><div class="toggle-cloud">{#each thesis.sectors as item}<Chip variant="filter" label={item} active={sector === item} pressed={sector === item} onclick={() => sector = toggle(sector, item)} />{/each}</div></fieldset>
      <fieldset><legend>Stage</legend><div class="toggle-cloud">{#each thesis.stages as item}<Chip variant="filter" label={item} active={stage === item} pressed={stage === item} onclick={() => stage = toggle(stage, item)} />{/each}</div></fieldset>
      <fieldset><legend>Geography</legend><div class="toggle-cloud compact">{#each thesis.geographies as item}<Chip variant="filter" label={item} active={geography === item} pressed={geography === item} onclick={() => geography = toggle(geography, item)} />{/each}</div></fieldset>
      <div class="weight-block">
        <div class="weight-heading"><legend>Ranking weights</legend><span>{signalWeight + momentumWeight + thesisWeight} pts</span></div>
        <label><span>Signal strength <b>{signalWeight}</b></span><input aria-label="Signal strength weight" type="range" min="0" max="100" bind:value={signalWeight} /></label>
        <label><span>Momentum <b>{momentumWeight}</b></span><input aria-label="Momentum weight" type="range" min="0" max="100" bind:value={momentumWeight} /></label>
        <label><span>Thesis fit <b>{thesisWeight}</b></span><input aria-label="Thesis fit weight" type="range" min="0" max="100" bind:value={thesisWeight} /></label>
      </div>
      <p class="thesis-note">{thesis.risk_appetite}</p>
    {/if}
  </aside>

  <div class="radar-list-panel" bind:this={radarElement} tabindex="0" role="grid" aria-label="Ranked founder candidates" onkeydown={onRadarKeydown}>
    <header class="list-heading"><div><p class="eyebrow">{loading ? 'Loading signals' : `${ranked.length} candidates`}</p><h2>Founder radar</h2></div><div class="keyboard-hint"><kbd>J</kbd><kbd>K</kbd> move <kbd>↵</kbd> open</div></header>
    <div class="list-columns" aria-hidden="true"><span>Rank / opportunity</span><span>90-day trajectory</span><span>Independent axes</span><span>Velocity / evidence</span><span>Signal</span></div>
    {#if loading}
      <div class="loading-list" aria-live="polite">Calibrating the radar…</div>
    {:else}
      <div class="candidate-list">
        {#each ranked as candidate, index (candidate.gh_login)}
          {@const detail = details[candidate.gh_login]}
          {@const displayedScore = scoreAtMonth(candidate, selectedMonth)}
          <div
            animate:flip={{ duration: reducedMotion ? 0 : 280 }}
            class:selected={index === selected}
            class="candidate-row"
            role="row"
            aria-selected={index === selected}
            use:observeCandidate={candidate.gh_login}
            style:--score-color={scoreColor(displayedScore)}
          >
            <button class="candidate-main" type="button" onfocus={() => selected = index} onclick={() => navigate(`/candidate/${candidate.gh_login}`)} aria-label={`Open ${shortName(candidate.founder_name)} record`}>
              <span class="rank-number">{String(index + 1).padStart(2, '0')}</span>
              <span class="avatar" aria-hidden="true">{shortName(candidate.founder_name, candidate.gh_login).split(' ').map((part) => part[0]).slice(0,2).join('')}</span>
              <span class="candidate-name"><strong>{shortName(candidate.founder_name, candidate.gh_login)}</strong><small>{candidate.company ?? 'Company not disclosed'} · @{candidate.gh_login.replace('-fixture', '')}</small><span class="source-badge source-{candidate.source}">{sourceLabel(candidate.source)}</span></span>
            </button>
            <div class="trajectory-cell" style:--forest={scoreColor(displayedScore)}>
              <MiniArea values={trajectoryValues(candidate, detail)} width={90} height={30} label={`${shortName(candidate.founder_name)} signal trajectory through ${monthLabel(selectedMonth)}`} />
              <small>{detail?.trajectory.length ?? 0} observed months</small>
            </div>
            <div class="row-axes">
              {#if detail?.three_axis}
                {#each axisOrder as axis}
                  <div><span>{axisLabels[axis]}</span><MiniBars values={Array.from({ length: 10 }, (_, bar) => bar < Math.round(detail.three_axis?.[axis].score ?? 0) ? 1 : 0)} width={72} height={7} label={`${axisLabels[axis]} ${detail.three_axis[axis].score.toFixed(1)} out of 10`} segments /><strong>{detail.three_axis[axis].score.toFixed(1)}</strong></div>
                {/each}
              {:else}
                <span class="axes-pending">{candidate.status === 'memo_ready' ? 'Loading memo axes…' : 'Axes not yet observed'}</span>
              {/if}
              <small>{candidate.profile?.sector ?? 'Technical founder'} · {candidate.profile?.stage ?? 'Early stage'}</small>
            </div>
            <div class="row-chips">
              <span class:negative={candidate.momentum_3mo < 0}><Chip variant="event" label={`${candidate.momentum_3mo >= 0 ? '↑' : '↓'} ${Math.abs(candidate.momentum_3mo * 100).toFixed(0)}% · 3mo`} /></span>
              <Chip variant="event" label={`${candidate.evidenceCount} evidence`} />
            </div>
            <div class="score-cell"><strong>{Math.round(displayedScore * 100)}</strong><span>as of {monthShort(selectedMonth)}</span></div>
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
