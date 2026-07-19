<script lang="ts">
  import { onMount } from 'svelte';
  import type { Claim, RunStep } from '../api/types';
  import { isMockMode } from '../api/client';
  import { navigate } from '../router';
  import Chip from '../components/Chip.svelte';
  import CircularIconButton from '../components/CircularIconButton.svelte';
  import ConfidenceArc from '../components/ConfidenceArc.svelte';

  export let runId: string;

  const mockSteps: RunStep[] = [
    { seq: 1, kind: 'plan', label: 'Plan diligence dimensions', detail: 'Founder, market, and idea-vs-market will be evaluated independently.', ts: '2026-07-19T07:12:01Z' },
    { seq: 2, kind: 'fetch', label: 'Fetch public build record', detail: 'Collecting repository, release, issue, and contributor evidence.', ts: '2026-07-19T07:12:02Z', payload: { provider: 'GitHub', resources: ['repositories', 'releases', 'contributors'] } },
    { seq: 3, kind: 'evidence', label: 'Evidence ledger opened', detail: 'Source records normalized; every claim must resolve to one of these rows.', ts: '2026-07-19T07:12:03Z', payload: { evidence_rows: 3, provenance: 'fixture' } },
    { seq: 4, kind: 'reason', label: 'Compare independent signals', detail: '# Keep the axes independent\nrows = sql("SELECT axis, score FROM signals")\npublic = [row for row in rows if row["source"] == "public"]\nclaims = validate(public, evidence_required=True)\nreturn rank(claims)', ts: '2026-07-19T07:12:04Z' },
    { seq: 5, kind: 'claim', label: 'Draft supported claim', detail: 'A fixture claim has materialized from the evidence ledger.', ts: '2026-07-19T07:12:05Z', payload: { text: 'The founder has a visible and recently active public build record.', evidence_refs: ['fixture-profile', 'fixture-repo'], confidence: 0.86, verification_status: 'verified', contradictions: [] } },
    { seq: 6, kind: 'done', label: 'Deep dive complete', detail: 'Fixture diligence completed with evidence-bound claims.', ts: '2026-07-19T07:12:06Z', payload: { outcome: 'OK' } }
  ];

  let steps: RunStep[] = isMockMode ? mockSteps : [];
  let status = isMockMode ? 'Replay complete' : 'Connecting to live audit stream';
  let streamError = '';
  let expandedReasonSteps = new Set<number>();

  function isClaim(value: Record<string, unknown> | undefined): boolean {
    return Boolean(value && typeof value.text === 'string' && Array.isArray(value.evidence_refs) && typeof value.confidence === 'number');
  }

  function statusTone(claimStatus: Claim['verification_status']): string {
    if (claimStatus === 'verified') return 'forest';
    if (claimStatus === 'single_source') return 'blue';
    return 'amber';
  }

  function labelStatus(value: string): string {
    return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function reasonLines(value: string): string[] {
    return value.split('\n');
  }

  function isComment(value: string): boolean {
    return /^\s*(#|\/\/)/.test(value);
  }

  function hasBranch(step: RunStep): boolean {
    return step.kind === 'reason' || Boolean(step.payload);
  }

  function payloadEntries(payload: Record<string, unknown> | undefined): Array<[string, string]> {
    if (!payload) return [];
    return Object.entries(payload).map(([key, value]) => [key, typeof value === 'string' ? value : JSON.stringify(value)]);
  }

  function toggleReason(seq: number): void {
    const next = new Set(expandedReasonSteps);
    if (next.has(seq)) next.delete(seq); else next.add(seq);
    expandedReasonSteps = next;
  }

  $: claims = steps.filter((step) => step.kind === 'claim' && isClaim(step.payload)).map((step) => ({ seq: step.seq, claim: step.payload as unknown as Claim }));
  $: isLive = !isMockMode && !streamError && !steps.some((step) => step.kind === 'done' || step.kind === 'error');
  $: newestSeq = isLive ? steps.at(-1)?.seq ?? null : null;
  const time = (value: string) => new Intl.DateTimeFormat('en', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(new Date(value));

  onMount(() => {
    if (isMockMode) return;
    const source = new EventSource(`/api/v1/deepdive/runs/${encodeURIComponent(runId)}/stream`);
    const onStep = (event: Event) => {
      const step = JSON.parse((event as MessageEvent<string>).data) as RunStep;
      if (!steps.some((item) => item.seq === step.seq)) steps = [...steps, step].sort((a, b) => a.seq - b.seq);
      status = step.kind === 'done' ? 'Diligence complete' : step.kind === 'error' ? 'Run failed' : 'Agent working · audit live';
      if (step.kind === 'done' || step.kind === 'error') source.close();
    };
    source.addEventListener('step', onStep);
    source.onerror = () => {
      if (!steps.some((step) => step.kind === 'done' || step.kind === 'error')) {
        streamError = 'The audit stream disconnected. Cached steps remain visible.';
        status = 'Stream disconnected';
      }
      source.close();
    };
    return () => {
      source.removeEventListener('step', onStep);
      source.close();
    };
  });
</script>

<section class="run-page shell">
  <div class="run-breadcrumb"><button onclick={() => history.back()}>←</button><span>Founder record / Deep dive</span></div>
  <header class="run-header">
    <div><div class="live-label"><i></i>{isMockMode ? 'Fixture replay' : 'Live diligence'}</div><h1>Deep-dive run</h1><p>Run <code>{runId}</code> · Replay-safe audit stream</p></div>
    <div class="run-status"><span class="live-pulse"><i></i></span><div><strong>{status}</strong><small>Evidence first · boundary validated</small></div></div>
  </header>
  {#if streamError}<p class="stream-error" role="alert">{streamError}</p>{/if}
  <div class="run-grid">
    <section class="step-feed" aria-labelledby="step-title">
      <div class="feed-heading"><div><p class="eyebrow">Agent trace</p><h2 id="step-title">Diligence steps</h2></div><span>{steps.length} steps</span></div>
      {#if steps.length}
        <ol class="trace-list">
          {#each steps as step}
            {@const claim = isClaim(step.payload) ? step.payload as unknown as Claim : null}
            {@const expanded = expandedReasonSteps.has(step.seq)}
            <li class="trace-item step-{step.kind}" class:newest-live={step.seq === newestSeq}>
              <div class="step-node" aria-hidden="true"><i></i><span>{String(step.seq).padStart(2, '0')}</span></div>
              <div class="trace-content">
                <header class="trace-summary"><div><span class="step-kind">{step.kind}</span><h3>{step.label}</h3></div><time>{time(step.ts)}</time></header>
                <p class="step-detail">{step.kind === 'reason' ? 'Sandbox execution captured below.' : step.detail}</p>
                {#if hasBranch(step)}
                  <div class="trace-branch">
                    <span class="branch-elbow" aria-hidden="true"></span>
                    {#if step.kind === 'reason'}
                      <article class="step-payload-card reason-card">
                        <header><div><span>Sandbox trace</span><strong>Reason step</strong></div><span class:expanded class="reason-expand"><CircularIconButton icon="chevron-down" size={36} label={expanded ? 'Collapse sandbox code' : 'Expand sandbox code'} onclick={() => toggleReason(step.seq)} /></span></header>
                        <pre class:expanded><code>{#each reasonLines(step.detail) as line}<span class:comment={isComment(line)}>{line || ' '}</span>{/each}</code></pre>
                      </article>
                    {:else if claim}
                      <article class="step-payload-card claim-payload-card">
                        <ConfidenceArc value={claim.confidence} size={48} label="Claim confidence" />
                        <div><header><span>Materialized claim</span><Chip variant="status" tone={statusTone(claim.verification_status)} label={labelStatus(claim.verification_status)} icon="✓" /></header><p>{claim.text}</p><footer>{claim.evidence_refs.length} linked evidence ref{claim.evidence_refs.length === 1 ? '' : 's'}</footer></div>
                      </article>
                    {:else}
                      <article class="step-payload-card data-payload-card">
                        <span class="payload-label">Step payload</span>
                        <dl>{#each payloadEntries(step.payload) as [key, value]}<div><dt>{labelStatus(key)}</dt><dd>{value}</dd></div>{/each}</dl>
                      </article>
                    {/if}
                  </div>
                {/if}
              </div>
            </li>
          {/each}
        </ol>
      {:else}<p class="feed-empty">Waiting for the first audited action…</p>{/if}
    </section>
    <aside class="run-side">
      <section><p class="eyebrow">Guardrails</p><h2>Trust contract</h2><ul><li>Evidence rows arrive before claims</li><li>Every claim resolves to source IDs</li><li>Unknowns stay visible as gaps</li><li>Three axes remain independent</li></ul></section>
      <section class="claim-results">
        <div class="claim-results-heading"><div><span>Claims</span><strong>{claims.length}</strong></div><small>Materialized from trace</small></div>
        {#if claims.length}
          <div>{#each claims as item}<article><ConfidenceArc value={item.claim.confidence} size={44} label={`Claim ${item.seq} confidence`} /><div><Chip variant="status" tone={statusTone(item.claim.verification_status)} label={labelStatus(item.claim.verification_status)} /><p>{item.claim.text}</p><small>{item.claim.evidence_refs.length} evidence ref{item.claim.evidence_refs.length === 1 ? '' : 's'}</small></div></article>{/each}</div>
        {:else}<p>Claim cards materialize as validated claim events arrive.</p>{/if}
      </section>
      <button class="secondary-button" onclick={() => navigate('/')}>Return to radar</button>
    </aside>
  </div>
</section>
