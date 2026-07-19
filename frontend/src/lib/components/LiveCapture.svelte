<script lang="ts">
  import type { DeepDiveRun, EvidenceEvent } from '../api/types';
  import Chip from './Chip.svelte';
  import ConfidenceArc from './ConfidenceArc.svelte';

  export let runs: DeepDiveRun[] = [];
  export let backtestEvidence: EvidenceEvent[] = [];
  const statusLabel: Record<string, string> = {
    verified: 'Verified', single_source: 'Single source', unverified: 'Unverified', not_disclosed: 'Not disclosed'
  };
  const toneForStatus = (status: string) => status === 'verified' ? 'forest' : status === 'single_source' ? 'blue' : 'amber';
  const dateLabel = (value: string) => new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(new Date(value));
</script>

{#if runs.length}
  <section class="live-capture-panel shell" aria-labelledby="live-capture-title">
    <header>
      <div><p class="eyebrow">Merge-back layer</p><h2 id="live-capture-title">Recent capture (hand-validated)</h2></div>
      <Chip variant="status" tone="live" label="live capture" icon="●" />
    </header>
    <div class="live-capture-runs">
      {#each runs as run}
        <article class="live-run-block">
          <div class="live-run-meta"><span>Captured {dateLabel(run.finished_at ?? run.started_at)}</span><a href={`/runs/${encodeURIComponent(run.run_id)}`}>{run.run_id} ↗</a></div>
          <div class="live-claim-grid">
            {#each Object.entries(run.claims) as [id, claim]}
              <article class="live-claim-card">
                <ConfidenceArc value={claim.confidence} label={`Live claim ${id} confidence`} />
                <div>
                  <div class="live-claim-chips"><Chip variant="status" tone="live" label="live capture" /><Chip variant="status" tone={toneForStatus(claim.verification_status)} label={statusLabel[claim.verification_status]} /></div>
                  <p>{claim.text}</p>
                  <div class="live-evidence-refs">
                    {#each claim.evidence_refs as ref}
                      {@const resolved = [...run.evidence, ...backtestEvidence].find((item) => item.evidence_id === ref)}
                      {#if ref.startsWith('live-') && resolved?.url}
                        <a href={resolved.url} target="_blank" rel="noreferrer" title={resolved.detail}>{ref} ↗</a>
                      {:else}<span title={resolved?.detail ?? ref}>{ref}</span>{/if}
                    {/each}
                  </div>
                </div>
              </article>
            {/each}
          </div>
        </article>
      {/each}
    </div>
  </section>
{/if}
