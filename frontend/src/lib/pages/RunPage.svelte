<script lang="ts">
  import { onMount } from 'svelte';
  import type { Claim, RunStep } from '../api/types';
  import { isMockMode } from '../api/client';
  import { navigate } from '../router';

  export let runId: string;

  const mockSteps: RunStep[] = [
    { seq: 1, kind: 'plan', label: 'Plan diligence dimensions', detail: 'Founder, market, and idea-vs-market will be evaluated independently.', ts: '2026-07-19T07:12:01Z' },
    { seq: 2, kind: 'fetch', label: 'Fetch public build record', detail: 'Collecting repository, release, issue, and contributor evidence.', ts: '2026-07-19T07:12:02Z' },
    { seq: 3, kind: 'evidence', label: 'Evidence ledger opened', detail: 'Source records normalized; every claim must resolve to one of these rows.', ts: '2026-07-19T07:12:03Z' },
    { seq: 4, kind: 'reason', label: 'Compare independent signals', detail: 'Checking cadence, outside participation, licensing clarity, and disclosed commercial proof.', ts: '2026-07-19T07:12:04Z' },
    { seq: 5, kind: 'claim', label: 'Draft supported claim', detail: 'A fixture claim has materialized from the evidence ledger.', ts: '2026-07-19T07:12:05Z', payload: { text: 'The founder has a visible and recently active public build record.', evidence_refs: ['fixture-profile', 'fixture-repo'], confidence: 0.86, verification_status: 'verified', contradictions: [] } },
    { seq: 6, kind: 'done', label: 'Deep dive complete', detail: 'Fixture diligence completed with evidence-bound claims.', ts: '2026-07-19T07:12:06Z', payload: { outcome: 'OK' } }
  ];

  let steps: RunStep[] = isMockMode ? mockSteps : [];
  let status = isMockMode ? 'Replay complete' : 'Connecting to live audit stream';
  let streamError = '';

  function isClaim(value: Record<string, unknown> | undefined): boolean {
    return Boolean(value && typeof value.text === 'string' && Array.isArray(value.evidence_refs) && typeof value.confidence === 'number');
  }

  $: claims = steps.filter((step) => step.kind === 'claim' && isClaim(step.payload)).map((step) => ({ seq: step.seq, claim: step.payload as unknown as Claim }));
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
    <section class="step-feed" aria-labelledby="step-title"><div class="feed-heading"><div><p class="eyebrow">Agent trace</p><h2 id="step-title">Diligence steps</h2></div><span>{steps.length} steps</span></div>{#if steps.length}<ol>{#each steps as step}<li class="step-{step.kind}"><div class="step-node"><span>{step.seq}</span></div><article><div><span class="step-kind">{step.kind}</span><time>{time(step.ts)}</time></div><h3>{step.label}</h3><p>{step.detail}</p></article></li>{/each}</ol>{:else}<p class="feed-empty">Waiting for the first audited action…</p>{/if}</section>
    <aside class="run-side"><section><p class="eyebrow">Guardrails</p><h2>Trust contract</h2><ul><li>Evidence rows arrive before claims</li><li>Every claim resolves to source IDs</li><li>Unknowns stay visible as gaps</li><li>Three axes remain independent</li></ul></section><section class="claim-results"><span>Claims</span><strong>{claims.length}</strong>{#if claims.length}<div>{#each claims as item}<article><p>{item.claim.text}</p><footer><span>{item.claim.verification_status.replaceAll('_', ' ')}</span><span>{Math.round(item.claim.confidence * 100)}%</span></footer><small>{item.claim.evidence_refs.length} evidence ref{item.claim.evidence_refs.length === 1 ? '' : 's'}</small></article>{/each}</div>{:else}<p>Claim cards materialize as validated claim events arrive.</p>{/if}</section><button class="secondary-button" onclick={() => navigate('/')}>Return to radar</button></aside>
  </div>
</section>
