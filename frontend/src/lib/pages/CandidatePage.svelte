<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { flip } from 'svelte/animate';
  import { api } from '../api/client';
  import type { CandidateDetailResponse, EvidenceEvent, Memo, TrajectoryPoint } from '../api/types';
  import { navigate } from '../router';
  import ClaimChip from '../components/ClaimChip.svelte';
  import Chip from '../components/Chip.svelte';
  import CircularIconButton from '../components/CircularIconButton.svelte';
  import MiniArea from '../components/MiniArea.svelte';
  import MiniBars from '../components/MiniBars.svelte';
  import ConfidenceArc from '../components/ConfidenceArc.svelte';

  type TimelineCluster = {
    month: string;
    events: EvidenceEvent[];
    typeCounts: Record<string, number>;
    dominantType: string;
    score: number;
  };

  export let login: string;
  let detail: CandidateDetailResponse | null = null;
  let memo: Memo | null = null;
  let evidence: EvidenceEvent[] = [];
  let selectedType = 'all';
  let loading = true;
  let error = '';
  let startingDive = false;
  let diveError = '';
  let timelineViewport: HTMLDivElement;
  let viewportLabel = 'Loading range';
  let activeMonthIndex = 0;
  let expandedMonth = '';
  let activeSection = 'overview';
  let dragging = false;
  let dragStartX = 0;
  let dragStartScroll = 0;
  let sectionObserver: IntersectionObserver | null = null;

  const MONTH_STEP = 236;
  const MONTH_OFFSET = 128;
  const SPINE_CENTER = 260;
  const sectionNav = [
    { id: 'overview', label: 'Overview', icon: '◎' },
    { id: 'timeline', label: 'Timeline', icon: '⌁' },
    { id: 'memo', label: 'Memo', icon: '▤' },
    { id: 'claims', label: 'Claims', icon: '✓' },
    { id: 'runs', label: 'Runs', icon: '↗' }
  ];
  const axisLabel: Record<string, string> = { founder: 'Founder', market: 'Market', idea_vs_market: 'Idea ↔ market' };
  const eventIcon: Record<string, string> = {
    commit_burst: '↟', star_milestone: '★', release_published: '◇', readme_updated: '≡',
    org_created: '◉', repo_created: '＋', contributor_joined: '↗', issue_closed: '✓'
  };

  const titleCase = (value: string) => value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
  const founderName = (value: string | null) => value?.replace(' (fixture)', '') ?? login.replace('-fixture', '');
  const dateLabel = (value: string) => {
    const parsed = new Date(value.length === 7 ? `${value}-01T00:00:00Z` : value);
    return Number.isNaN(parsed.valueOf()) ? 'Not observed' : new Intl.DateTimeFormat('en', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(parsed);
  };
  const monthShort = (value: string) => new Intl.DateTimeFormat('en', { month: 'short', timeZone: 'UTC' }).format(new Date(`${value}-01T00:00:00Z`));
  const parseInteger = (value: string) => Number.parseInt(value.replaceAll(',', ''), 10);
  const numberWord: Record<string, number> = { one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10 };

  function scoreForMonth(month: string, trajectory: TrajectoryPoint[]): number {
    if (!trajectory.length) return 0;
    const exact = trajectory.find((point) => point.month.slice(0, 7) === month);
    if (exact) return exact.score;
    const target = new Date(`${month}-01T00:00:00Z`).valueOf();
    return trajectory.reduce((closest, point) => {
      const distance = Math.abs(new Date(point.month).valueOf() - target);
      return distance < closest.distance ? { score: point.score, distance } : closest;
    }, { score: trajectory[0].score, distance: Number.POSITIVE_INFINITY }).score;
  }

  function buildClusters(items: EvidenceEvent[], trajectory: TrajectoryPoint[]): TimelineCluster[] {
    const grouped = new Map<string, EvidenceEvent[]>();
    for (const event of [...items].sort((a, b) => a.ts.localeCompare(b.ts))) {
      const month = event.ts.slice(0, 7);
      grouped.set(month, [...(grouped.get(month) ?? []), event]);
    }
    return [...grouped.entries()].map(([month, events]) => {
      const typeCounts = events.reduce<Record<string, number>>((counts, event) => {
        counts[event.event_type] = (counts[event.event_type] ?? 0) + 1;
        return counts;
      }, {});
      const dominantType = Object.entries(typeCounts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0]?.[0] ?? 'event';
      return { month, events, typeCounts, dominantType, score: scoreForMonth(month, trajectory) };
    });
  }

  function parsedEventNumber(event: EvidenceEvent): number | null {
    const patterns = event.event_type === 'commit_burst'
      ? [/(\d[\d,]*)\s+commits?/i]
      : event.event_type === 'star_milestone'
        ? [/(\d[\d,]*)\s+(?:public\s+)?stars?/i]
        : event.event_type === 'issue_closed'
          ? [/#(\d[\d,]*)/]
          : [];
    for (const pattern of patterns) {
      const match = event.detail.match(pattern);
      if (match) {
        const parsed = parseInteger(match[1]);
        if (Number.isFinite(parsed)) return parsed;
      }
    }
    return null;
  }

  function metricValue(events: EvidenceEvent[], type: string): number {
    const matching = events.filter((event) => event.event_type === type);
    if (!matching.length) return 0;
    const values = matching.map(parsedEventNumber);
    if (type === 'star_milestone') return Math.max(...values.map((value) => value ?? 1));
    return values.reduce<number>((total, value) => total + (value ?? 1), 0);
  }

  function typeSeries(cluster: TimelineCluster, type: string): number[] {
    const index = allClusters.findIndex((item) => item.month === cluster.month);
    return allClusters.slice(Math.max(0, index - 5), index + 1).map((item) => metricValue(item.events, type));
  }

  function dayCount(event: EvidenceEvent): number | null {
    const match = event.detail.match(/(?:across|over)\s+(?:a\s+)?(\d+|one|two|three|four|five|six|seven|eight|nine|ten)[-\s]?day/i);
    if (!match) return null;
    return /^\d+$/.test(match[1]) ? Number.parseInt(match[1], 10) : numberWord[match[1].toLowerCase()] ?? null;
  }

  function metricLabel(cluster: TimelineCluster): string {
    const typeEvents = cluster.events.filter((event) => event.event_type === cluster.dominantType);
    if (cluster.dominantType === 'commit_burst') {
      const parsed = typeEvents.map(parsedEventNumber);
      const commits = parsed.some((value) => value !== null) ? parsed.reduce<number>((sum, value) => sum + (value ?? 1), 0) : typeEvents.length;
      const days = typeEvents.map(dayCount).find((value) => value !== null);
      return `${commits} commits${days ? ` · ${days}d` : ''}`;
    }
    if (cluster.dominantType === 'star_milestone') {
      const stars = Math.max(...typeEvents.map((event) => parsedEventNumber(event) ?? 1));
      return `${stars.toLocaleString('en-US')} ★`;
    }
    if (cluster.dominantType === 'release_published') {
      const versions = typeEvents.flatMap((event) => event.detail.match(/\bv?\d+(?:\.\d+)+(?:[-\w.]*)?/gi) ?? []).map((version) => version.startsWith('v') ? version : `v${version}`);
      return versions.length ? versions.join(' · ') : `${typeEvents.length} ${typeEvents.length === 1 ? 'release' : 'releases'}`;
    }
    return `${typeEvents.length} ${typeEvents.length === 1 ? 'event' : 'events'}`;
  }

  function spineY(score: number): number {
    return SPINE_CENTER + (0.58 - Math.max(0, Math.min(1, score))) * 90;
  }

  function scoreColor(score: number): string {
    const start = [154, 163, 156];
    const end = [25, 79, 60];
    const ratio = Math.max(0, Math.min(1, score));
    return `rgb(${start.map((value, index) => Math.round(value + (end[index] - value) * ratio)).join(',')})`;
  }

  function setFilter(type: string): void {
    selectedType = type;
    activeMonthIndex = 0;
    expandedMonth = '';
    void tick().then(() => {
      timelineViewport?.scrollTo({ left: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
      updateViewportRange();
    });
  }

  function updateViewportRange(): void {
    if (!timelineViewport || !timelineClusters.length) {
      viewportLabel = 'No matching months';
      return;
    }
    const left = timelineViewport.scrollLeft;
    const right = left + timelineViewport.clientWidth;
    const inView = timelineClusters.filter((_, index) => {
      const x = MONTH_OFFSET + index * MONTH_STEP;
      return x >= left - 40 && x <= right + 40;
    });
    const visible = inView.length ? inView : [timelineClusters[Math.min(activeMonthIndex, timelineClusters.length - 1)]];
    viewportLabel = visible.length === 1 ? dateLabel(visible[0].month) : `${dateLabel(visible[0].month)} — ${dateLabel(visible.at(-1)?.month ?? visible[0].month)}`;
  }

  function stepMonth(delta: number): void {
    if (!timelineClusters.length || !timelineViewport) return;
    activeMonthIndex = Math.max(0, Math.min(timelineClusters.length - 1, activeMonthIndex + delta));
    const x = MONTH_OFFSET + activeMonthIndex * MONTH_STEP;
    timelineViewport.scrollTo({ left: Math.max(0, x - timelineViewport.clientWidth / 2), behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    expandedMonth = timelineClusters[activeMonthIndex].month;
  }

  function handleTimelineKey(event: KeyboardEvent): void {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      stepMonth(event.key === 'ArrowLeft' ? -1 : 1);
    } else if (event.key === 'Enter' && timelineClusters[activeMonthIndex]) {
      event.preventDefault();
      const month = timelineClusters[activeMonthIndex].month;
      expandedMonth = expandedMonth === month ? '' : month;
      document.getElementById(`timeline-card-${month}`)?.focus();
    }
  }

  function startDrag(event: PointerEvent): void {
    if (event.button !== 0 || !timelineViewport) return;
    dragging = true;
    dragStartX = event.clientX;
    dragStartScroll = timelineViewport.scrollLeft;
    timelineViewport.setPointerCapture(event.pointerId);
  }

  function dragTimeline(event: PointerEvent): void {
    if (dragging && timelineViewport) timelineViewport.scrollLeft = dragStartScroll - (event.clientX - dragStartX);
  }

  function endDrag(event: PointerEvent): void {
    dragging = false;
    if (timelineViewport?.hasPointerCapture(event.pointerId)) timelineViewport.releasePointerCapture(event.pointerId);
  }

  function scrollToSection(id: string): void {
    document.getElementById(id)?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
  }

  function observeSections(): void {
    sectionObserver?.disconnect();
    sectionObserver = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible) activeSection = visible.target.id;
    }, { rootMargin: '-20% 0px -55% 0px', threshold: [0, .2, .5] });
    for (const item of sectionNav) {
      const element = document.getElementById(item.id);
      if (element) sectionObserver.observe(element);
    }
  }

  async function startDeepDive(): Promise<void> {
    startingDive = true;
    diveError = '';
    try {
      const run = await api.startDeepDive({ entity_type: 'founder', entity_id: login, dimensions: ['founder', 'market', 'idea_vs_market'] });
      navigate(`/runs/${encodeURIComponent(run.run_id)}`);
    } catch (reason) {
      diveError = reason instanceof Error ? reason.message : 'Unable to start deep dive';
      startingDive = false;
    }
  }

  onMount(() => {
    let disposed = false;
    void (async () => {
      try {
        detail = await api.getCandidate(login);
        const [eventResponse, memoResponse] = await Promise.all([
          api.getEvidence(login),
          detail.memo_available ? api.getMemo(login) : Promise.resolve(null)
        ]);
        if (!disposed) {
          evidence = eventResponse.items;
          memo = memoResponse;
        }
      } catch (reason) {
        if (!disposed) error = reason instanceof Error ? reason.message : 'Unable to load founder record';
      } finally {
        if (!disposed) {
          loading = false;
          await tick();
          updateViewportRange();
          observeSections();
        }
      }
    })();
    return () => { disposed = true; sectionObserver?.disconnect(); };
  });

  $: allClusters = buildClusters(evidence, detail?.trajectory ?? []);
  $: timelineClusters = selectedType === 'all' ? allClusters : allClusters.filter((cluster) => cluster.events.some((event) => event.event_type === selectedType));
  $: eventTypes = [...new Set(evidence.map((event) => event.event_type))].sort();
  $: eventCounts = evidence.reduce<Record<string, number>>((counts, event) => { counts[event.event_type] = (counts[event.event_type] ?? 0) + 1; return counts; }, {});
  $: detectionMonth = detail?.candidate.first_detection_month?.slice(0, 7) ?? '';
  $: latestObserved = [...evidence.map((event) => event.ts), ...(detail?.trajectory.map((point) => point.month) ?? [])].sort().at(-1) ?? '';
  $: timelineWidth = Math.max(900, MONTH_OFFSET * 2 + Math.max(0, timelineClusters.length - 1) * MONTH_STEP);
</script>

{#if loading}
  <div class="page-state shell" aria-live="polite">Opening the founder record…</div>
{:else if error || !detail}
  <div class="page-state shell"><p>{error}</p><button class="primary-button" onclick={() => navigate('/')}>Back to radar</button></div>
{:else}
  <section id="overview" class="record-header shell" aria-labelledby="founder-name">
    <div class="record-breadcrumb">
      <CircularIconButton icon="back" label="Back to radar" onclick={() => navigate('/')} />
      <span>Radar / Founder record</span>
      <Chip variant="status" tone="forest" label={`Observed through ${dateLabel(latestObserved)}`} icon="●" />
    </div>
    <div class="record-title-row">
      <div class="record-identity">
        <div class="record-avatar">{founderName(detail.candidate.founder_name).split(' ').map((part) => part[0]).slice(0, 2).join('')}</div>
        <div>
          <p class="eyebrow">Founder intelligence record</p>
          <h1 id="founder-name">{founderName(detail.candidate.founder_name)}</h1>
          <div class="identity-chips">
            <Chip variant="status" tone="blue" label={`@${detail.candidate.gh_login.replace('-fixture', '')}`} icon="@" />
            <Chip variant="status" tone="forest" label={detail.candidate.company ?? 'Company not disclosed'} icon="◇" />
            <Chip variant="status" tone="amber" label={titleCase(detail.candidate.source)} icon="◎" />
          </div>
        </div>
      </div>
      <div class="deepdive-action">
        <button class="live-button" disabled={startingDive} onclick={startDeepDive}><i aria-hidden="true"></i>{startingDive ? 'Starting…' : 'Deep dive'} <span>↗</span></button>
        {#if diveError}<small role="alert">{diveError}</small>{/if}
      </div>
    </div>

    <nav class="record-section-nav" aria-label="Founder record sections">
      {#each sectionNav as item}
        <Chip variant="nav" label={item.label} icon={item.icon} active={activeSection === item.id} pressed={activeSection === item.id} onclick={() => scrollToSection(item.id)} />
      {/each}
    </nav>

    <div class="vitals-strip" aria-label="Founder signal vitals">
      <div class="signal-vital"><span>Signal</span><strong>{Math.round(detail.candidate.current_score * 100)}</strong><small>Top {Math.max(1, Math.round(100 - detail.candidate.score_percentile + 1))}%</small></div>
      <div class="momentum-vital"><span>Momentum · 3mo</span><strong class:negative={detail.candidate.momentum_3mo < 0}>{detail.candidate.momentum_3mo >= 0 ? '↑' : '↓'}{Math.abs(detail.candidate.momentum_3mo * 100).toFixed(0)}%</strong><small>Evidence velocity</small></div>
      <div class="axes-vital">
        <div><span>Three independent axes</span><small>Never averaged</small></div>
        {#if detail.three_axis}
          <div class="axis-micro-grid">
            {#each Object.entries(detail.three_axis) as [key, axis]}
              <div class="axis-micro"><span>{axisLabel[key]}</span><MiniBars values={Array.from({ length: 10 }, (_, index) => index < Math.round(axis.score) ? 1 : 0)} width={76} height={12} label={`${axisLabel[key]} ${axis.score.toFixed(1)} out of 10`} segments /><strong>{axis.score.toFixed(1)}</strong></div>
            {/each}
          </div>
        {:else}<p class="not-observed">Axes not observed.</p>{/if}
      </div>
      <div class="detection-vital"><span>First detection</span><strong>{detail.candidate.first_detection_month ? dateLabel(detail.candidate.first_detection_month) : 'Not observed'}</strong><small>Threshold crossing</small></div>
    </div>
  </section>

  <section id="timeline" class="timeline-panel shell" aria-labelledby="timeline-title">
    <header class="timeline-panel-header">
      <div><p class="eyebrow">Longitudinal source ledger · {evidence.length} observations</p><h2 id="timeline-title">Evidence trajectory</h2></div>
      <div class="timeline-range"><span>Viewport</span><strong aria-live="polite">{viewportLabel}</strong></div>
    </header>
    <div class="timeline-tools">
      <div class="timeline-filters" aria-label="Filter evidence event type">
        <Chip variant="filter" label="All events" icon="◎" count={evidence.length} active={selectedType === 'all'} pressed={selectedType === 'all'} onclick={() => setFilter('all')} />
        {#each eventTypes as type}
          <span data-event-type={type}><Chip variant="filter" label={titleCase(type)} icon={eventIcon[type] ?? '•'} count={eventCounts[type]} active={selectedType === type} pressed={selectedType === type} onclick={() => setFilter(type)} /></span>
        {/each}
      </div>
      <div class="timeline-controls">
        <span><kbd>←</kbd><kbd>→</kbd> month · <kbd>↵</kbd> open</span>
        <CircularIconButton icon="arrow-left" label="Previous month" disabled={activeMonthIndex === 0} onclick={() => stepMonth(-1)} />
        <CircularIconButton icon="arrow-right" label="Next month" disabled={activeMonthIndex >= timelineClusters.length - 1} onclick={() => stepMonth(1)} />
      </div>
    </div>

    <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
      class="timeline-viewport"
      class:dragging
      bind:this={timelineViewport}
      role="region"
      tabindex="0"
      aria-label="Scrollable evidence timeline"
      onscroll={updateViewportRange}
      onkeydown={handleTimelineKey}
      onpointerdown={startDrag}
      onpointermove={dragTimeline}
      onpointerup={endDrag}
      onpointercancel={endDrag}
    >
      {#if timelineClusters.length}
        <div class="timeline-stage" style:width={`${timelineWidth}px`}>
          <svg class="timeline-wiring" width={timelineWidth} height="580" aria-hidden="true">
            {#each timelineClusters.slice(0, -1) as cluster, index}
              {@const next = timelineClusters[index + 1]}
              <path d={`M ${MONTH_OFFSET + index * MONTH_STEP} ${spineY(cluster.score)} L ${MONTH_OFFSET + (index + 1) * MONTH_STEP} ${spineY(next.score)}`} stroke={scoreColor((cluster.score + next.score) / 2)} class="spine-segment" />
            {/each}
            {#each timelineClusters as cluster, index}
              {@const x = MONTH_OFFSET + index * MONTH_STEP}
              {@const y = spineY(cluster.score)}
              {@const upper = index % 2 === 0}
              <path class="branch-connector" d={upper ? `M ${x} ${y - 7} V 207 Q ${x} 198 ${x - 9} 198 H ${x - 92}` : `M ${x} ${y + 7} V 326 Q ${x} 335 ${x + 9} 335 H ${x + 92}`} />
            {/each}
          </svg>

          {#each timelineClusters as cluster, index (cluster.month)}
            {@const x = MONTH_OFFSET + index * MONTH_STEP}
            {@const y = spineY(cluster.score)}
            <div
              class="timeline-node"
              class:active={activeMonthIndex === index}
              class:detection={cluster.month === detectionMonth}
              data-testid="timeline-month-node"
              data-month={cluster.month}
              data-event-types={Object.keys(cluster.typeCounts).join(',')}
              style:left={`${x}px`}
              style:top={`${y}px`}
              style:--node-size={`${Math.min(18, 8 + cluster.events.length * 2)}px`}
              animate:flip={{ duration: 240 }}
            >
              <button aria-label={`${dateLabel(cluster.month)}, ${cluster.events.length} evidence events, score ${Math.round(cluster.score * 100)}`} onclick={() => { activeMonthIndex = index; expandedMonth = expandedMonth === cluster.month ? '' : cluster.month; }}><i></i></button>
              <span>{monthShort(cluster.month)}</span>
              {#if index === 0 || cluster.month.slice(0, 4) !== timelineClusters[index - 1]?.month.slice(0, 4)}<strong>{cluster.month.slice(0, 4)}</strong>{/if}
            </div>
          {/each}

          {#each timelineClusters as cluster, index (cluster.month)}
            {@const x = MONTH_OFFSET + index * MONTH_STEP}
            {@const upper = index % 2 === 0}
            <article
              id={`timeline-card-${cluster.month}`}
              class="timeline-card"
              class:upper
              class:expanded={expandedMonth === cluster.month}
              style:left={`${x - 104}px`}
              style:top={upper ? '26px' : '342px'}
              tabindex="-1"
              animate:flip={{ duration: 240 }}
            >
              <header>
                <div><span>{dateLabel(cluster.month)}</span><strong>{titleCase(cluster.dominantType)}</strong></div>
                <b>{cluster.events.length}</b>
              </header>
              <p>{cluster.events.find((event) => event.event_type === cluster.dominantType)?.detail}</p>
              {#if cluster.dominantType === 'commit_burst'}
                <MiniArea values={typeSeries(cluster, cluster.dominantType)} label={`Monthly commit volume through ${dateLabel(cluster.month)}`} />
              {:else if cluster.dominantType === 'star_milestone'}
                <MiniBars values={typeSeries(cluster, cluster.dominantType)} label={`Star milestones through ${dateLabel(cluster.month)}`} />
              {:else if cluster.dominantType === 'release_published'}
                <div class="release-versions"><Chip variant="event" icon="◇" label={metricLabel(cluster)} /></div>
              {:else}
                <div class="event-one-liner"><span aria-hidden="true">{eventIcon[cluster.dominantType] ?? '•'}</span>{metricLabel(cluster)}</div>
              {/if}
              {#if cluster.dominantType !== 'release_published'}<Chip variant="event" icon={eventIcon[cluster.dominantType] ?? '•'} label={metricLabel(cluster)} />{/if}
              <div class="mixed-types">
                {#each Object.entries(cluster.typeCounts) as [type, count]}<Chip variant="event" icon={eventIcon[type] ?? '•'} label={titleCase(type)} {count} />{/each}
              </div>
              {#if expandedMonth === cluster.month && cluster.events.length > 1}
                <ul class="event-stack">{#each cluster.events as event}<li><span>{titleCase(event.event_type)}</span>{event.detail}</li>{/each}</ul>
              {/if}
              <footer><span>{cluster.events[0].repo_name}</span><CircularIconButton icon="external" label={`Open ${cluster.events[0].repo_name}`} href={cluster.events[0].url} target="_blank" /></footer>
            </article>
          {/each}
        </div>
      {:else}
        <div class="timeline-empty">No evidence matches this filter.</div>
      {/if}
    </div>
  </section>

  {#if memo}
    <section id="memo" class="memo-layout shell" aria-labelledby="memo-title">
      <div class="memo-main">
        <div class="section-title memo-heading"><div><p class="eyebrow">Investment memo · Generated {dateLabel(memo.generated_at)}</p><h2 id="memo-title">What the evidence supports</h2></div><Chip variant="status" tone="forest" label="Evidence-led" icon="✓" /></div>
        <article id="claims" class="memo-section featured"><span class="section-number">01</span><div><h3>Company snapshot</h3><p>{memo.sections.company_snapshot.text}</p><div class="claim-row">{#each memo.sections.company_snapshot.claim_ids as id}<span class="claim-with-confidence"><ConfidenceArc value={memo.claims[id].confidence} label={`Claim ${id} confidence`} /><ClaimChip {id} claim={memo.claims[id]} {evidence} /></span>{/each}</div></div></article>
        <article class="memo-section"><span class="section-number">02</span><div><h3>Investment hypotheses</h3>{#each memo.sections.investment_hypotheses as item}<div class="memo-item"><p>{item.text}</p><div class="claim-row">{#each item.claim_ids as id}<span class="claim-with-confidence"><ConfidenceArc value={memo.claims[id].confidence} label={`Claim ${id} confidence`} /><ClaimChip {id} claim={memo.claims[id]} {evidence} /></span>{/each}</div></div>{/each}</div></article>
        <article class="memo-section"><span class="section-number">03</span><div><h3>Problem & product</h3><p>{memo.sections.problem_product.text}</p><div class="claim-row">{#each memo.sections.problem_product.claim_ids as id}<span class="claim-with-confidence"><ConfidenceArc value={memo.claims[id].confidence} label={`Claim ${id} confidence`} /><ClaimChip {id} claim={memo.claims[id]} {evidence} /></span>{/each}</div></div></article>
        <article class="memo-section"><span class="section-number">04</span><div><h3>Traction & KPIs</h3><p>{memo.sections.traction_kpis.text}</p><div class="claim-row">{#each memo.sections.traction_kpis.claim_ids as id}<span class="claim-with-confidence"><ConfidenceArc value={memo.claims[id].confidence} label={`Claim ${id} confidence`} /><ClaimChip {id} claim={memo.claims[id]} {evidence} /></span>{/each}</div></div></article>
        <article class="memo-section swot-section"><span class="section-number">05</span><div><h3>Evidence-grounded SWOT</h3><div class="swot-grid">{#each Object.entries(memo.sections.swot) as [label, items]}<div class="swot-cell swot-{label}"><h4>{titleCase(label)}</h4>{#each items as item}<div class="swot-item"><p>{item.text}</p><div class="claim-row">{#each item.claim_ids as id}<span class="claim-with-confidence"><ConfidenceArc value={memo.claims[id].confidence} label={`Claim ${id} confidence`} /><ClaimChip {id} claim={memo.claims[id]} {evidence} /></span>{/each}</div></div>{/each}</div>{/each}</div></div></article>
      </div>
      <aside class="gaps-box" aria-labelledby="gaps-title"><div class="gaps-icon" aria-hidden="true">∅</div><p class="eyebrow">Honesty layer</p><h2 id="gaps-title">Not observed</h2><p>These gaps remain intentionally blank. No proxy data or assumptions have been used.</p><ul>{#each memo.gaps as gap}<li><span>—</span>{gap}</li>{/each}</ul><footer>Required before investment committee</footer></aside>
    </section>
  {:else}
    <section id="memo" class="shell no-memo"><h2>Memo not observed</h2><p>This founder has a signal record, but no evidence-backed memo is available yet.</p></section>
  {/if}

  <section id="runs" class="run-launch shell" aria-labelledby="runs-title">
    <div><p class="eyebrow">Live diligence workspace</p><h2 id="runs-title">Turn this record into an auditable run.</h2><p>Investigate the same source-linked evidence across founder, market, and idea-to-market dimensions.</p></div>
    <div class="deepdive-action"><button class="live-button" disabled={startingDive} onclick={startDeepDive}><i aria-hidden="true"></i>{startingDive ? 'Starting…' : 'Start deep dive'} <span>↗</span></button>{#if diveError}<small role="alert">{diveError}</small>{/if}</div>
  </section>
{/if}
