<script lang="ts">
  import type { Claim, EvidenceEvent } from '../api/types';
  export let id: string;
  export let claim: Claim;
  export let evidence: EvidenceEvent[] = [];
  let visible = false;

  const statusLabel: Record<string, string> = {
    verified: 'Verified', single_source: 'Single source', unverified: 'Unverified', not_disclosed: 'Not disclosed'
  };
</script>

<span class="claim-anchor" role="group" id={`claim-${id}`} onmouseenter={() => visible = true} onmouseleave={() => visible = false} onfocusin={() => visible = true} onfocusout={(event) => { if (!event.currentTarget.contains(event.relatedTarget as Node)) visible = false; }}>
  <button class="claim-chip status-{claim.verification_status}" type="button" aria-haspopup="dialog" aria-expanded={visible} onclick={() => visible = true}>
    <span aria-hidden="true">{claim.verification_status === 'verified' ? '✓' : claim.verification_status === 'single_source' ? '1' : claim.verification_status === 'not_disclosed' ? '—' : '?'}</span>
    Claim {id.replace(/^.*-/, '').toUpperCase()}
  </button>
  {#if visible}
    <div class="claim-popover" role="dialog" aria-label={`Evidence for claim ${id}`}>
      <div class="popover-head"><span class="verification-badge status-{claim.verification_status}">{statusLabel[claim.verification_status]}</span><strong>{Math.round(claim.confidence * 100)}% confidence</strong></div>
      <div class="confidence-track" aria-label={`${Math.round(claim.confidence * 100)} percent confidence`}><i style={`width:${claim.confidence * 100}%`}></i></div>
      <p>{claim.text}</p>
      <div class="evidence-links">
        <span>Evidence references</span>
        {#each claim.evidence_refs as ref}
          {@const resolved = evidence.find((event) => event.evidence_id === ref)}
          <a href={resolved?.url ?? '#'} target="_blank" rel="noreferrer" title={resolved?.detail ?? ref}>{resolved?.detail ?? ref} <b>↗</b></a>
        {/each}
      </div>
      {#if claim.contradictions.length}
        <div class="contradictions"><strong>Contradiction</strong>{#each claim.contradictions as item}<p>{item}</p>{/each}</div>
      {/if}
    </div>
  {/if}
</span>
