<script lang="ts">
  export let values: number[] = [];
  export let width = 120;
  export let height = 30;
  export let label = 'Data bars';
  export let segments = false;

  $: safeValues = values.length ? values.map((value) => Number.isFinite(value) ? Math.max(0, value) : 0) : [0];
  $: maximum = Math.max(...safeValues, 1);
  $: gap = segments ? 3 : 4;
  $: barWidth = Math.max(2, (width - gap * (safeValues.length - 1)) / safeValues.length);
</script>

<svg class="mini-bars" class:segments viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label} preserveAspectRatio="none">
  {#each safeValues as value, index}
    {@const barHeight = Math.max(2, (value / maximum) * (height - 2))}
    <rect x={index * (barWidth + gap)} y={height - barHeight} width={barWidth} height={barHeight} rx={segments ? 1.5 : 2.5} />
  {/each}
</svg>

<style>
  .mini-bars { width: 100%; height: auto; min-height: 24px; overflow: visible; }
  rect { fill: var(--forest); transform-box: fill-box; transform-origin: center bottom; animation: rise 460ms ease-out both; }
  rect:nth-child(2n) { opacity: .78; }
  rect:nth-child(3n) { opacity: .58; }
  .segments rect { opacity: 1; }
  @keyframes rise { from { transform: scaleY(.08); } to { transform: scaleY(1); } }
  @media (prefers-reduced-motion: reduce) { rect { animation: none; } }
</style>
