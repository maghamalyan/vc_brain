<script lang="ts">
  import { onMount } from 'svelte';
  import { flip } from 'svelte/animate';
  import { api } from '../api/client';
  import type { Candidate, EvidenceEvent, Profile, Thesis } from '../api/types';
  import { navigate } from '../router';

  type RankedCandidate = Candidate & { profile: Profile | null; adjusted: number; originalRank: number; rankDelta: number; evidenceCount: number };
  let candidates: Candidate[] = [];
  let thesis: Thesis | null = null;
  let profiles: Record<string, Profile | null> = {};
  let evidence: Record<string, EvidenceEvent[]> = {};
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

  const months = Array.from({ length: 24 }, (_, index) => {
    const date = new Date(Date.UTC(2024, 7 + index, 1));
    return date.toISOString().slice(0, 7);
  });

  const monthLabel = (month: string) => new Intl.DateTimeFormat('en', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${month}-01T00:00:00Z`));
  const shortName = (name: string | null, login = 'Founder') => name?.replace(' (fixture)', '') ?? login.replace('-fixture', '');
  const sourceLabel = (source: string) => source === 'outbound_detector' ? 'Outbound signal' : 'Inbound deck';
  const scoreAtMonth = (candidate: Candidate, month: string): number => {
    const items = evidence[candidate.gh_login] ?? [];
    const total = items.length || 1;
    const visible = items.filter((event) => event.ts.slice(0, 7) <= month).length;
    const maturity = 0.58 + 0.42 * visible / total;
    return candidate.current_score * maturity;
  };

  function toggle(current: string, value: string): string { return current === value ? '' : value; }

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
    const detailRows = await Promise.all(candidates.map(async (candidate) => {
      const [profile, eventResponse] = await Promise.all([api.getProfile(candidate.gh_login), api.getEvidence(candidate.gh_login)]);
      return [candidate.gh_login, profile, eventResponse.items] as const;
    }));
    profiles = Object.fromEntries(detailRows.map(([login, profile]) => [login, profile]));
    evidence = Object.fromEntries(detailRows.map(([login, , items]) => [login, items]));
    loading = false;
    requestAnimationFrame(() => radarElement?.focus());
  });

  $: selectedMonth = months[scrubberIndex];
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
    <div class="scrubber-copy"><span class="eyebrow">Intelligence as of</span><strong>{monthLabel(selectedMonth)}</strong></div>
    <div class="scrubber-control">
      <div class="scrubber-years" aria-hidden="true"><span>2024</span><span>2025</span><span>2026</span></div>
      <input aria-label="Filter evidence by month" type="range" min="0" max={months.length - 1} bind:value={scrubberIndex} />
      <div class="scrubber-ticks" aria-hidden="true">{#each months as _, index}<i class:major={index % 6 === 0}></i>{/each}</div>
    </div>
    <span class="scrubber-honesty">Future evidence hidden</span>
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
      <fieldset><legend>Sector preference</legend><div class="toggle-cloud">{#each thesis.sectors as item}<button class:active={sector === item} type="button" aria-pressed={sector === item} onclick={() => sector = toggle(sector, item)}>{item}</button>{/each}</div></fieldset>
      <fieldset><legend>Stage</legend><div class="toggle-cloud">{#each thesis.stages as item}<button class:active={stage === item} type="button" aria-pressed={stage === item} onclick={() => stage = toggle(stage, item)}>{item}</button>{/each}</div></fieldset>
      <fieldset><legend>Geography</legend><div class="toggle-cloud compact">{#each thesis.geographies as item}<button class:active={geography === item} type="button" aria-pressed={geography === item} onclick={() => geography = toggle(geography, item)}>{item}</button>{/each}</div></fieldset>
      <div class="weight-block">
        <div class="weight-heading"><legend>Ranking weights</legend><span>{signalWeight + momentumWeight + thesisWeight} pts</span></div>
        <label><span>Signal strength <b>{signalWeight}</b></span><input type="range" min="0" max="100" bind:value={signalWeight} /></label>
        <label><span>Momentum <b>{momentumWeight}</b></span><input type="range" min="0" max="100" bind:value={momentumWeight} /></label>
        <label><span>Thesis fit <b>{thesisWeight}</b></span><input type="range" min="0" max="100" bind:value={thesisWeight} /></label>
      </div>
      <p class="thesis-note">{thesis.risk_appetite}</p>
    {/if}
  </aside>

  <div class="radar-list-panel" bind:this={radarElement} tabindex="0" role="grid" aria-label="Ranked founder candidates" onkeydown={onRadarKeydown}>
    <header class="list-heading"><div><p class="eyebrow">{loading ? 'Loading signals' : `${ranked.length} candidates`}</p><h2>Founder radar</h2></div><div class="keyboard-hint"><kbd>J</kbd><kbd>K</kbd> move <kbd>↵</kbd> open</div></header>
    <div class="list-columns" aria-hidden="true"><span>Rank / opportunity</span><span>Thesis fit</span><span>Momentum</span><span>Signal</span></div>
    {#if loading}
      <div class="loading-list" aria-live="polite">Calibrating the radar…</div>
    {:else}
      <div class="candidate-list">
        {#each ranked as candidate, index (candidate.gh_login)}
          <div animate:flip={{ duration: reducedMotion ? 0 : 280 }} class:selected={index === selected} class="candidate-row" role="row" aria-selected={index === selected}>
            <button class="candidate-main" type="button" onfocus={() => selected = index} onclick={() => navigate(`/candidate/${candidate.gh_login}`)} aria-label={`Open ${shortName(candidate.founder_name)} record`}>
              <span class="rank-number">{String(index + 1).padStart(2, '0')}</span>
              <span class="avatar" aria-hidden="true">{shortName(candidate.founder_name, candidate.gh_login).split(' ').map((part) => part[0]).slice(0,2).join('')}</span>
              <span class="candidate-name"><strong>{shortName(candidate.founder_name, candidate.gh_login)}</strong><small>{candidate.company ?? 'Company not disclosed'} · @{candidate.gh_login.replace('-fixture', '')}</small><span class="source-badge source-{candidate.source}">{sourceLabel(candidate.source)}</span></span>
            </button>
            <div class="fit-cell"><strong>{candidate.profile?.sector ?? 'Technical founder'}</strong><span>{candidate.profile?.stage ?? 'Early stage'} · {candidate.profile?.geography ?? 'Global'}</span></div>
            <div class:negative={candidate.momentum_3mo < 0} class="momentum-cell"><strong>{candidate.momentum_3mo >= 0 ? '↑' : '↓'} {Math.abs(candidate.momentum_3mo * 100).toFixed(0)}%</strong><span>3 month</span></div>
            <div class="score-cell"><strong>{Math.round(scoreAtMonth(candidate, selectedMonth) * 100)}</strong><span class="evidence-badge">{candidate.evidenceCount} refs</span></div>
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
