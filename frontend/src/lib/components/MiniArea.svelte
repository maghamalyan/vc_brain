<script lang="ts">
  export let values: number[] = [];
  export let width = 148;
  export let height = 36;
  export let label = 'Data trend';

  $: safeValues = values.length ? values.map((value) => Number.isFinite(value) ? value : 0) : [0];
  $: maximum = Math.max(...safeValues, 1);
  $: minimum = Math.min(...safeValues, 0);
  $: range = Math.max(maximum - minimum, 1);
  $: coordinates = safeValues.map((value, index) => ({
    x: safeValues.length === 1 ? width / 2 : (index / (safeValues.length - 1)) * width,
    y: height - 3 - ((value - minimum) / range) * (height - 8)
  }));
  $: line = coordinates.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(' ');
  $: fill = `${line} L ${coordinates.at(-1)?.x ?? width} ${height} L ${coordinates[0]?.x ?? 0} ${height} Z`;
</script>

<svg class="mini-area" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label} preserveAspectRatio="none">
  <path class="area-fill" d={fill} />
  <path class="area-line" d={line} pathLength="1" />
  {#if coordinates.length === 1}<circle cx={coordinates[0].x} cy={coordinates[0].y} r="2" />{/if}
</svg>

<style>
  .mini-area { width: 100%; height: auto; min-height: 28px; overflow: visible; }
  .area-fill { fill: var(--forest); opacity: .12; }
  .area-line { fill: none; stroke: var(--forest); stroke-width: 1.5; vector-effect: non-scaling-stroke; stroke-linecap: round; stroke-linejoin: round; animation: draw 650ms ease-out both; }
  circle { fill: var(--forest); }
  @keyframes draw { from { stroke-dasharray: 1; stroke-dashoffset: 1; } to { stroke-dasharray: 1; stroke-dashoffset: 0; } }
  @media (prefers-reduced-motion: reduce) { .area-line { animation: none; } }
</style>
