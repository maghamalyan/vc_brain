<script lang="ts">
  import type { Claim, EvidenceEvent } from '../api/types';

  export let claimIds: string[] = [];
  export let claims: Record<string, Claim> = {};
  export let evidence: EvidenceEvent[] = [];
  export let numberById: Record<string, number> = {};
  export let highlightedClaimIds: string[] = [];
  let visibleId = '';

  const statusLabel: Record<string, string> = {
    verified: 'Verified', single_source: 'Single source', unverified: 'Unverified', not_disclosed: 'Not disclosed'
  };
  $: availableIds = claimIds.filter((id) => Boolean(claims[id]));
  $: minimumConfidence = availableIds.length ? Math.min(...availableIds.map((id) => claims[id].confidence)) : 0;

  function closeOnEscape(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      visibleId = '';
      (event.currentTarget as HTMLButtonElement).blur();
    }
  }
</script>

<span class="memo-inline-citations" data-claim-count={claimIds.length}>
  {#each availableIds as id}
    {@const claim = claims[id]}
    <span
      class="citation-anchor"
      role="group"
      id={`claim-${id}`}
      onmouseenter={() => visibleId = id}
      onmouseleave={() => visibleId = ''}
      onfocusin={() => visibleId = id}
      onfocusout={(event) => { if (!event.currentTarget.contains(event.relatedTarget as Node)) visibleId = ''; }}
    >
      <button
        class="memo-citation"
        class:linked-highlight={highlightedClaimIds.includes(id)}
        type="button"
        aria-haspopup="dialog"
        aria-expanded={visibleId === id}
        aria-label={`Citation ${numberById[id]}, claim ${id}`}
        onclick={() => visibleId = visibleId === id ? '' : id}
        onkeydown={closeOnEscape}
      >[{numberById[id]}]</button>
      {#if visibleId === id}
        <span class="claim-popover" role="dialog" aria-label={`Evidence for claim ${id}`}>
          <span class="popover-head"><span class="verification-badge status-{claim.verification_status}">{statusLabel[claim.verification_status]}</span><strong>{Math.round(claim.confidence * 100)}% confidence</strong></span>
          <span class="confidence-track" aria-label={`${Math.round(claim.confidence * 100)} percent confidence`}><i style={`width:${claim.confidence * 100}%`}></i></span>
          <span class="citation-claim-text">{claim.text}</span>
          <span class="evidence-links">
            <span>Evidence references</span>
            {#each claim.evidence_refs as ref}
              {@const resolved = evidence.find((event) => event.evidence_id === ref)}
              <a href={resolved?.url ?? '#'} target="_blank" rel="noreferrer" title={resolved?.detail ?? ref}>{resolved?.detail ?? ref} <b>↗</b></a>
            {/each}
          </span>
          {#if claim.contradictions.length}
            <span class="contradictions"><strong>Contradiction</strong>{#each claim.contradictions as item}<span>{item}</span>{/each}</span>
          {/if}
        </span>
      {/if}
    </span>
  {/each}
  <span
    class="section-confidence-dot"
    style:opacity={0.35 + minimumConfidence * 0.65}
    title={`Minimum linked-claim confidence: ${Math.round(minimumConfidence * 100)}%`}
    aria-label={`Minimum linked-claim confidence ${Math.round(minimumConfidence * 100)} percent`}
  ></span>
</span>
