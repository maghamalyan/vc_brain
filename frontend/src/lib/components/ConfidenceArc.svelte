<script lang="ts">
  export let value: number;
  export let size = 38;
  export let label = 'Confidence';
  $: normalized = Math.max(0, Math.min(1, value > 1 ? value / 100 : value));
  $: percent = Math.round(normalized * 100);
</script>

<span class="confidence-arc" style:width={`${size}px`} style:height={`${size}px`} role="img" aria-label={`${label} ${percent}%`}>
  <svg viewBox="0 0 42 42" aria-hidden="true">
    <circle class="arc-track" cx="21" cy="21" r="16" pathLength="1" />
    <circle class="arc-value" cx="21" cy="21" r="16" pathLength="1" style:stroke-dasharray={`${normalized} 1`} />
  </svg>
  <strong>{percent}</strong>
</span>

<style>
  .confidence-arc { position: relative; flex: 0 0 auto; display: inline-grid; place-items: center; font-variant-numeric: tabular-nums; }
  svg { position: absolute; inset: 0; width: 100%; height: 100%; transform: rotate(-90deg); }
  circle { fill: none; stroke-width: 3; }
  .arc-track { stroke: var(--line-soft); }
  .arc-value { stroke: var(--forest); stroke-linecap: round; transition: stroke-dasharray 420ms ease; }
  strong { color: var(--ink); font: 720 8px/1 var(--mono-font, ui-monospace, monospace); }
  @media (prefers-reduced-motion: reduce) { .arc-value { transition: none; } }
</style>
