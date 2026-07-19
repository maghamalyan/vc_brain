<script lang="ts">
  import type { TrajectoryPoint } from '../api/types';
  export let points: TrajectoryPoint[] = [];
  export let firstDetection = '';
  export let labelledBy = '';

  const width = 640;
  const height = 180;
  const pad = 12;
  $: values = points.map((point) => point.score);
  $: min = Math.min(...values, 0);
  $: max = Math.max(...values, 1);
  $: x = (index: number) => pad + (index / Math.max(points.length - 1, 1)) * (width - pad * 2);
  $: y = (value: number) => height - pad - ((value - min) / Math.max(max - min, 0.01)) * (height - pad * 2);
  $: path = points.map((point, index) => `${index ? 'L' : 'M'} ${x(index).toFixed(1)} ${y(point.score).toFixed(1)}`).join(' ');
  $: markerIndex = Math.max(0, points.findIndex((point) => point.month.slice(0, 7) === firstDetection.slice(0, 7)));
</script>

<svg class="sparkline" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img" aria-labelledby={labelledBy || undefined}>
  <g class="chart-grid" aria-hidden="true"><line x1={pad} y1="45" x2={width-pad} y2="45"></line><line x1={pad} y1="90" x2={width-pad} y2="90"></line><line x1={pad} y1="135" x2={width-pad} y2="135"></line></g>
  {#if points.length}
    <path class="trajectory-path" d={path}></path>
    <line class="detection-line" x1={x(markerIndex)} y1={pad} x2={x(markerIndex)} y2={height-pad}></line>
    <circle class="detection-dot" cx={x(markerIndex)} cy={y(points[markerIndex]?.score ?? 0)} r="5"></circle>
    <circle class="latest-dot" cx={x(points.length - 1)} cy={y(points.at(-1)?.score ?? 0)} r="4"></circle>
  {/if}
</svg>
