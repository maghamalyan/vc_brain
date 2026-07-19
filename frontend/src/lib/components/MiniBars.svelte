<script lang="ts">
  export let values: number[] = [];
  export let width = 120;
  export let height = 30;
  export let label = 'Data bars';
  export let segments = false;

  $: safeValues = values.length ? values.map((value) => Number.isFinite(value) ? Math.max(0, value) : 0) : [0];
  $: maximum = Math.max(...safeValues, 1);
  $: gap = segments ? 3 : 4;
  // Segments variant stretches to fill its container; the default variant is
  // content-sized with fixed-width bars so 2 data points never become one
  // container-filling block.
  $: barWidth = segments ? Math.max(2, (width - gap * (safeValues.length - 1)) / safeValues.length) : 12;
  $: contentWidth = segments ? width : safeValues.length * barWidth + (safeValues.length - 1) * gap;
</script>

<svg
  class="mini-bars"
  class:segments
  viewBox={`0 0 ${contentWidth} ${height}`}
  role="img"
  aria-label={label}
  preserveAspectRatio={segments ? 'none' : 'xMinYMax meet'}
>
  <line class="baseline" x1="0" y1={height - 0.5} x2={contentWidth} y2={height - 0.5} />
  {#each safeValues as value, index}
    {@const barHeight = Math.max(2, (value / maximum) * (height - 3))}
    <rect x={index * (barWidth + gap)} y={height - 1 - barHeight} width={barWidth} height={barHeight} rx={2} />
  {/each}
</svg>

<style>
  .mini-bars { width: 100%; height: auto; min-height: 24px; overflow: visible; }
  .mini-bars:not(.segments) { width: auto; max-width: 100%; height: 30px; }
  .baseline { stroke: var(--line, #dfe3de); stroke-width: 1; }
  .segments .baseline { display: none; }
  rect { fill: var(--forest); transform-box: fill-box; transform-origin: center bottom; animation: rise 460ms ease-out both; }
  rect:nth-child(2n) { opacity: .78; }
  rect:nth-child(3n) { opacity: .58; }
  .segments rect { opacity: 1; }
  @keyframes rise { from { transform: scaleY(.08); } to { transform: scaleY(1); } }
  @media (prefers-reduced-motion: reduce) { rect { animation: none; } }
</style>
