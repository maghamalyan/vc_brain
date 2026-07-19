<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../api/client';
  import type { CandidateDetailResponse, EvidenceEvent, Memo } from '../api/types';
  import { navigate } from '../router';
  import Sparkline from '../components/Sparkline.svelte';
  import ClaimChip from '../components/ClaimChip.svelte';

  export let login: string;
  let detail: CandidateDetailResponse | null = null;
  let memo: Memo | null = null;
  let evidence: EvidenceEvent[] = [];
  let selectedType = 'all';
  let loading = true;
  let error = '';
  let startingDive = false;
  let diveError = '';

  const titleCase = (value: string) => value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
  const dateLabel = (value: string) => new Intl.DateTimeFormat('en', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(value));
  const axisLabel: Record<string, string> = { founder: 'Founder', market: 'Market', idea_vs_market: 'Idea ↔ market' };
  const founderName = (value: string | null) => value?.replace(' (fixture)', '') ?? login.replace('-fixture', '');

  async function startDeepDive(): Promise<void> {
    startingDive = true;
    diveError = '';
    try {
      const run = await api.startDeepDive({
        entity_type: 'founder',
        entity_id: login,
        dimensions: ['founder', 'market', 'idea_vs_market']
      });
      navigate(`/runs/${encodeURIComponent(run.run_id)}`);
    } catch (reason) {
      diveError = reason instanceof Error ? reason.message : 'Unable to start deep dive';
      startingDive = false;
    }
  }

  onMount(async () => {
    try {
      detail = await api.getCandidate(login);
      const [eventResponse, memoResponse] = await Promise.all([
        api.getEvidence(login),
        detail.memo_available ? api.getMemo(login) : Promise.resolve(null)
      ]);
      evidence = eventResponse.items;
      memo = memoResponse;
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Unable to load founder record';
    } finally { loading = false; }
  });

  $: eventTypes = [...new Set(evidence.map((event) => event.event_type))];
  $: filteredEvidence = selectedType === 'all' ? evidence : evidence.filter((event) => event.event_type === selectedType);
  $: timelineMonths = [...new Set(filteredEvidence.map((event) => event.ts.slice(0, 7)))];
  $: detectionMonth = detail?.candidate.first_detection_month ?? detail?.trajectory[0]?.month ?? '';
</script>

{#if loading}
  <div class="page-state shell" aria-live="polite">Opening the founder health record…</div>
{:else if error || !detail}
  <div class="page-state shell"><p>{error}</p><button class="primary-button" onclick={() => navigate('/')}>Back to radar</button></div>
{:else}
  <section class="record-header shell">
    <div class="record-breadcrumb"><button onclick={() => navigate('/')} aria-label="Back to radar">←</button><span>Radar / Founder record</span><span class="record-status">Observed through Jul ’26</span></div>
    <div class="record-title-row">
      <div class="record-identity"><div class="record-avatar">{founderName(detail.candidate.founder_name).split(' ').map((part) => part[0]).slice(0,2).join('')}</div><div><p class="eyebrow">Founder health record · {detail.candidate.source.replaceAll('_', ' ')}</p><h1>{founderName(detail.candidate.founder_name)}</h1><p>{detail.candidate.company ?? 'Company not disclosed'} <span>·</span> @{detail.candidate.gh_login.replace('-fixture', '')}</p></div></div>
      <div class="deepdive-action"><button class="live-button" disabled={startingDive} onclick={startDeepDive}><i aria-hidden="true"></i>{startingDive ? 'Starting…' : 'Deep dive'} <span>↗</span></button>{#if diveError}<small role="alert">{diveError}</small>{/if}</div>
    </div>
    <div class="vitals-grid">
      <div class="score-vital"><span>Signal score</span><strong>{Math.round(detail.candidate.current_score * 100)}</strong><small>Top {Math.round(100 - detail.candidate.score_percentile + 1)}% of observed founders</small></div>
      <div class="axis-vital">
        <div class="vital-label"><span>Independent diligence axes</span><small>Never averaged</small></div>
        {#if detail.three_axis}
          <div class="axis-bars">
            {#each Object.entries(detail.three_axis) as [key, axis]}
              <div class="axis-row"><span>{axisLabel[key]}</span><div class="segmented-bar" aria-label={`${axisLabel[key]} ${axis.score} out of 10`}>{#each Array(10) as _, index}<i class:filled={index < Math.round(axis.score)}></i>{/each}</div><strong>{axis.score.toFixed(1)}</strong><small class:improving={axis.trend === 'improving'}>{axis.trend === 'improving' ? '↑' : '→'} {axis.trend}</small></div>
            {/each}
          </div>
        {:else}<p class="not-observed">Axes not observed.</p>{/if}
      </div>
      <div class="mini-vital"><span>Momentum · 3mo</span><strong class:negative={detail.candidate.momentum_3mo < 0}>{detail.candidate.momentum_3mo >= 0 ? '↑' : '↓'} {Math.abs(detail.candidate.momentum_3mo * 100).toFixed(0)}%</strong><small>Evidence velocity</small></div>
      <div class="mini-vital"><span>First detection</span><strong>{detail.candidate.first_detection_month ? dateLabel(detail.candidate.first_detection_month) : 'Not observed'}</strong><small>Signal crossed threshold</small></div>
    </div>
  </section>

  <section class="trajectory-section shell" aria-labelledby="trajectory-title">
    <div class="section-title"><div><p class="eyebrow">Longitudinal signal</p><h2 id="trajectory-title">Detection trajectory</h2></div><div class="chart-legend"><span><i class="legend-line"></i>Score trajectory</span><span><i class="legend-marker"></i>First detection</span></div></div>
    <div class="trajectory-chart"><Sparkline points={detail.trajectory} firstDetection={detectionMonth} labelledBy="trajectory-title" /><div class="chart-labels"><span>{dateLabel(detail.trajectory[0]?.month ?? detectionMonth)}</span><span>{detail.candidate.first_detection_month ? `${dateLabel(detail.candidate.first_detection_month)} · Detected` : 'Detection not observed'}</span><span>{dateLabel(detail.trajectory.at(-1)?.month ?? detectionMonth)}</span></div></div>
  </section>

  <section class="evidence-section shell" aria-labelledby="timeline-title">
    <div class="section-title timeline-heading"><div><p class="eyebrow">Source ledger · {filteredEvidence.length} observations</p><h2 id="timeline-title">Evidence timeline</h2></div><div class="event-filters" aria-label="Filter evidence event type"><button class:active={selectedType === 'all'} aria-pressed={selectedType === 'all'} onclick={() => selectedType = 'all'}>All events</button>{#each eventTypes as type}<button class:active={selectedType === type} aria-pressed={selectedType === type} onclick={() => selectedType = type}>{titleCase(type)}</button>{/each}</div></div>
    <!-- svelte-ignore a11y_no_noninteractive_tabindex (keyboard focus enables horizontal arrow-key scrolling) -->
    <div class="timeline-scroll" role="region" tabindex="0" aria-label="Scrollable evidence timeline">
      {#each timelineMonths as month}
        <div class="timeline-month"><div class="month-marker"><span>{dateLabel(`${month}-01`)}</span><i></i></div><div class="month-events">{#each filteredEvidence.filter((event) => event.ts.startsWith(month)) as event}<a class="event-card event-{event.event_type}" href={event.url} target="_blank" rel="noreferrer"><span>{titleCase(event.event_type)}</span><strong>{event.detail}</strong><small>{event.repo_name} ↗</small></a>{/each}</div></div>
      {/each}
    </div>
  </section>

  {#if memo}
    <section id="memo" class="memo-layout shell" aria-labelledby="memo-title">
      <div class="memo-main">
        <div class="section-title memo-heading"><div><p class="eyebrow">Investment memo · Generated {dateLabel(memo.generated_at)}</p><h2 id="memo-title">What the evidence supports</h2></div><span class="memo-stamp">Evidence-led</span></div>
        <article class="memo-section featured"><span class="section-number">01</span><div><h3>Company snapshot</h3><p>{memo.sections.company_snapshot.text}</p><div class="claim-row">{#each memo.sections.company_snapshot.claim_ids as id}<ClaimChip {id} claim={memo.claims[id]} {evidence} />{/each}</div></div></article>
        <article class="memo-section"><span class="section-number">02</span><div><h3>Investment hypotheses</h3>{#each memo.sections.investment_hypotheses as item}<div class="memo-item"><p>{item.text}</p><div class="claim-row">{#each item.claim_ids as id}<ClaimChip {id} claim={memo.claims[id]} {evidence} />{/each}</div></div>{/each}</div></article>
        <article class="memo-section"><span class="section-number">03</span><div><h3>Problem & product</h3><p>{memo.sections.problem_product.text}</p><div class="claim-row">{#each memo.sections.problem_product.claim_ids as id}<ClaimChip {id} claim={memo.claims[id]} {evidence} />{/each}</div></div></article>
        <article class="memo-section"><span class="section-number">04</span><div><h3>Traction & KPIs</h3><p>{memo.sections.traction_kpis.text}</p><div class="claim-row">{#each memo.sections.traction_kpis.claim_ids as id}<ClaimChip {id} claim={memo.claims[id]} {evidence} />{/each}</div></div></article>
        <article class="memo-section swot-section"><span class="section-number">05</span><div><h3>Evidence-grounded SWOT</h3><div class="swot-grid">{#each Object.entries(memo.sections.swot) as [label, items]}<div class="swot-cell swot-{label}"><h4>{titleCase(label)}</h4>{#each items as item}<div class="swot-item"><p>{item.text}</p><div class="claim-row">{#each item.claim_ids as id}<ClaimChip {id} claim={memo.claims[id]} {evidence} />{/each}</div></div>{/each}</div>{/each}</div></div></article>
      </div>
      <aside class="gaps-box" aria-labelledby="gaps-title"><div class="gaps-icon" aria-hidden="true">∅</div><p class="eyebrow">Honesty layer</p><h2 id="gaps-title">Not observed</h2><p>These gaps remain intentionally blank. No proxy data or assumptions have been used.</p><ul>{#each memo.gaps as gap}<li><span>—</span>{gap}</li>{/each}</ul><footer>Required before investment committee</footer></aside>
    </section>
  {:else}
    <section class="shell no-memo"><h2>Memo not observed</h2><p>This founder has a signal record, but no evidence-backed memo is available yet.</p></section>
  {/if}
{/if}
