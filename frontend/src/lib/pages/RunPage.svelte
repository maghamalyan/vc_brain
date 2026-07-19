<script lang="ts">
  import type { RunStep } from '../api/types';
  import { navigate } from '../router';
  export let runId: string;

  const steps: RunStep[] = [
    { seq: 1, kind: 'plan', label: 'Plan diligence dimensions', detail: 'Founder, market, and idea-vs-market will be evaluated independently.', ts: '2026-07-19T07:12:01Z' },
    { seq: 2, kind: 'fetch', label: 'Fetch public build record', detail: 'Collecting repository, release, issue, and contributor evidence.', ts: '2026-07-19T07:12:02Z' },
    { seq: 3, kind: 'evidence', label: 'Evidence ledger opened', detail: '8 source records normalized; each claim must resolve to one of these rows.', ts: '2026-07-19T07:12:03Z' },
    { seq: 4, kind: 'reason', label: 'Compare independent signals', detail: 'Checking cadence, outside participation, licensing clarity, and disclosed commercial proof.', ts: '2026-07-19T07:12:04Z' },
    { seq: 5, kind: 'claim', label: 'Draft supported claims', detail: 'Claims will materialize here as the future SSE stream arrives.', ts: '2026-07-19T07:12:05Z' }
  ];

  const time = (value: string) => new Intl.DateTimeFormat('en', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(new Date(value));
</script>

<section class="run-page shell">
  <div class="run-breadcrumb"><button onclick={() => history.back()}>←</button><span>Founder record / Deep dive</span></div>
  <header class="run-header">
    <div><div class="live-label"><i></i>Live diligence shell</div><h1>Deep-dive run</h1><p>Run <code>{runId}</code> · Static step feed ready for SSE wiring</p></div>
    <div class="run-status"><span class="live-pulse"><i></i></span><div><strong>Preparing stream</strong><small>Replay-safe · evidence first</small></div></div>
  </header>
  <div class="run-grid">
    <section class="step-feed" aria-labelledby="step-title"><div class="feed-heading"><div><p class="eyebrow">Agent trace</p><h2 id="step-title">Diligence steps</h2></div><span>{steps.length} steps</span></div><ol>{#each steps as step}<li class="step-{step.kind}"><div class="step-node"><span>{step.seq}</span></div><article><div><span class="step-kind">{step.kind}</span><time>{time(step.ts)}</time></div><h3>{step.label}</h3><p>{step.detail}</p></article></li>{/each}</ol></section>
    <aside class="run-side"><section><p class="eyebrow">Guardrails</p><h2>Trust contract</h2><ul><li>Evidence rows arrive before claims</li><li>Every claim resolves to source IDs</li><li>Unknowns stay visible as gaps</li><li>Three axes remain independent</li></ul></section><section class="claim-placeholder"><span>Claims</span><strong>0</strong><p>Claim cards will materialize here as SSE <code>claim</code> events arrive.</p></section><button class="secondary-button" onclick={() => navigate('/')}>Return to radar</button></aside>
  </div>
</section>
