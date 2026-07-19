<script lang="ts">
  import type { Claim, EvidenceEvent } from '../api/types';

  export let sections: Array<{ id: string; label: string; anchorId: string; claimIds: string[] }> = [];
  export let claims: Record<string, Claim> = {};
  export let evidence: EvidenceEvent[] = [];
  export let numberById: Record<string, number> = {};
  let activeNode = '';

  const WIDTH = 1120;
  const COLUMN_X = { section: 30, claim: 410, evidence: 790 };
  const NODE_WIDTH = 300;
  $: claimIds = [...new Set(sections.flatMap((section) => section.claimIds))].filter((id) => claims[id]);
  $: evidenceIds = [...new Set(claimIds.flatMap((id) => claims[id].evidence_refs))];
  $: referencedEvidence = evidenceIds.map((id) => evidence.find((item) => item.evidence_id === id)).filter((item): item is EvidenceEvent => Boolean(item));
  $: rowCount = Math.max(sections.length, claimIds.length, referencedEvidence.length, 1);
  $: height = Math.max(370, 96 + rowCount * 44);
  $: activeConnections = connectionsFor(activeNode);

  const y = (index: number, count: number) => 78 + (index + 0.5) * ((height - 98) / Math.max(count, 1));
  const nodeId = (kind: string, id: string) => `${kind}:${id}`;
  const short = (value: string, length = 38) => value.length > length ? `${value.slice(0, length - 1)}…` : value;

  function connectionsFor(id: string): Set<string> {
    const connected = new Set<string>();
    if (!id) return connected;
    connected.add(id);
    const [kind, value] = id.split(':', 2);
    if (kind === 'section') {
      const section = sections.find((item) => item.id === value);
      for (const claimId of section?.claimIds ?? []) {
        connected.add(nodeId('claim', claimId));
        for (const evidenceId of claims[claimId]?.evidence_refs ?? []) connected.add(nodeId('evidence', evidenceId));
      }
    } else if (kind === 'claim') {
      for (const section of sections.filter((item) => item.claimIds.includes(value))) connected.add(nodeId('section', section.id));
      for (const evidenceId of claims[value]?.evidence_refs ?? []) connected.add(nodeId('evidence', evidenceId));
    } else if (kind === 'evidence') {
      for (const claimId of claimIds.filter((claimId) => claims[claimId].evidence_refs.includes(value))) {
        connected.add(nodeId('claim', claimId));
        for (const section of sections.filter((item) => item.claimIds.includes(claimId))) connected.add(nodeId('section', section.id));
      }
    }
    return connected;
  }

  function navigateNode(kind: string, id: string): void {
    if (kind === 'section') {
      const section = sections.find((item) => item.id === id);
      document.getElementById(section?.anchorId ?? '')?.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'center' });
      return;
    }
    if (kind === 'claim') {
      const button = document.getElementById(`claim-${id}`)?.querySelector('button');
      if (button instanceof HTMLButtonElement) { button.focus(); button.click(); }
      return;
    }
    const item = evidence.find((event) => event.evidence_id === id);
    if (!item) return;
    const month = /^\d{4}-\d{2}/.test(item.ts) ? item.ts.slice(0, 7) : '';
    const timelineNode = month ? document.querySelector(`[data-month="${month}"] button`) : null;
    if (timelineNode instanceof HTMLButtonElement) {
      timelineNode.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'nearest', inline: 'center' });
      timelineNode.focus();
    } else if (item.url) window.open(item.url, '_blank', 'noopener,noreferrer');
  }

  function reducedMotion(): boolean {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function handleKey(event: KeyboardEvent, kind: string, id: string): void {
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); navigateNode(kind, id); }
    else if (event.key === 'Escape') activeNode = '';
  }
</script>

<section class="provenance-panel" aria-labelledby="provenance-title">
  <header>
    <div><p class="eyebrow">Trust architecture</p><h2 id="provenance-title">How this memo knows what it knows</h2></div>
    <p><strong>{sections.length}</strong> sections · <strong>{claimIds.length}</strong> claims · <strong>{referencedEvidence.length}</strong> evidence events</p>
  </header>
  <div class="provenance-canvas">
    <svg viewBox={`0 0 ${WIDTH} ${height}`} role="img" aria-label="Memo sections linked to claims and their evidence events">
      <text class="graph-column-label" x={COLUMN_X.section} y="28">Memo sections</text>
      <text class="graph-column-label" x={COLUMN_X.claim} y="28">Claims</text>
      <text class="graph-column-label" x={COLUMN_X.evidence} y="28">Evidence events</text>

      <g class="graph-paths">
        {#each sections as section, sectionIndex}
          {#each section.claimIds.filter((id) => claimIds.includes(id)) as claimId}
            {@const claimIndex = claimIds.indexOf(claimId)}
            {@const from = nodeId('section', section.id)}
            {@const to = nodeId('claim', claimId)}
            <path class:dimmed={activeNode && !(activeConnections.has(from) && activeConnections.has(to))} d={`M ${COLUMN_X.section + NODE_WIDTH} ${y(sectionIndex, sections.length)} C 365 ${y(sectionIndex, sections.length)}, 365 ${y(claimIndex, claimIds.length)}, ${COLUMN_X.claim} ${y(claimIndex, claimIds.length)}`} />
          {/each}
        {/each}
        {#each claimIds as claimId, claimIndex}
          {#each claims[claimId].evidence_refs.filter((id) => evidenceIds.includes(id)) as evidenceId}
            {@const evidenceIndex = referencedEvidence.findIndex((item) => item.evidence_id === evidenceId)}
            {#if evidenceIndex >= 0}
              {@const from = nodeId('claim', claimId)}
              {@const to = nodeId('evidence', evidenceId)}
              <path class:dimmed={activeNode && !(activeConnections.has(from) && activeConnections.has(to))} d={`M ${COLUMN_X.claim + NODE_WIDTH} ${y(claimIndex, claimIds.length)} C 745 ${y(claimIndex, claimIds.length)}, 745 ${y(evidenceIndex, referencedEvidence.length)}, ${COLUMN_X.evidence} ${y(evidenceIndex, referencedEvidence.length)}`} />
            {/if}
          {/each}
        {/each}
      </g>

      {#each sections as section, index}
        {@const id = nodeId('section', section.id)}
        <g class="graph-node section-node" class:dimmed={activeNode && !activeConnections.has(id)} role="button" tabindex="0" onmouseenter={() => activeNode = id} onmouseleave={() => activeNode = ''} onfocus={() => activeNode = id} onblur={() => activeNode = ''} onclick={() => navigateNode('section', section.id)} onkeydown={(event) => handleKey(event, 'section', section.id)}>
          <rect x={COLUMN_X.section} y={y(index, sections.length) - 17} width={NODE_WIDTH} height="34" rx="8" />
          <text x={COLUMN_X.section + 12} y={y(index, sections.length) + 4}>{short(section.label)}</text>
        </g>
      {/each}
      {#each claimIds as claimId, index}
        {@const id = nodeId('claim', claimId)}
        <g class="graph-node claim-node" class:dimmed={activeNode && !activeConnections.has(id)} role="button" tabindex="0" onmouseenter={() => activeNode = id} onmouseleave={() => activeNode = ''} onfocus={() => activeNode = id} onblur={() => activeNode = ''} onclick={() => navigateNode('claim', claimId)} onkeydown={(event) => handleKey(event, 'claim', claimId)}>
          <rect x={COLUMN_X.claim} y={y(index, claimIds.length) - 17} width={NODE_WIDTH} height="34" rx="8" />
          <text x={COLUMN_X.claim + 12} y={y(index, claimIds.length) + 4}>[{numberById[claimId]}] {short(claims[claimId].text, 35)}</text>
        </g>
      {/each}
      {#each referencedEvidence as event, index}
        {@const id = nodeId('evidence', event.evidence_id)}
        <g class="graph-node evidence-node" class:dimmed={activeNode && !activeConnections.has(id)} role="button" tabindex="0" onmouseenter={() => activeNode = id} onmouseleave={() => activeNode = ''} onfocus={() => activeNode = id} onblur={() => activeNode = ''} onclick={() => navigateNode('evidence', event.evidence_id)} onkeydown={(keyboardEvent) => handleKey(keyboardEvent, 'evidence', event.evidence_id)}>
          <rect x={COLUMN_X.evidence} y={y(index, referencedEvidence.length) - 17} width={NODE_WIDTH} height="34" rx="8" />
          <text x={COLUMN_X.evidence + 12} y={y(index, referencedEvidence.length) + 4}>{short(event.detail)}</text>
        </g>
      {/each}
    </svg>
  </div>
</section>
