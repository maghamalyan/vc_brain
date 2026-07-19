<script lang="ts">
  import type { ScoreComponent } from '../api/types';

  export let components: ScoreComponent[] = [];
  export let score = 0;
  export let activeKey = '';
  export let onactivate: (key: string) => void = () => {};
  export let ondeactivate: () => void = () => {};

  const WIDTH = 920;
  const LABEL_WIDTH = 250;
  const CHART_WIDTH = 520;
  const ROW_HEIGHT = 58;
  const TOP = 38;
  $: total = Math.max(score, components.reduce((sum, component) => sum + component.contribution, 0), 0.01);
  $: rows = components.map((component, index) => {
    const start = components.slice(0, index).reduce((sum, item) => sum + item.contribution, 0);
    const running = start + component.contribution;
    return { ...component, start, running };
  });
  $: height = TOP + rows.length * ROW_HEIGHT + 34;
  const x = (value: number) => LABEL_WIDTH + (value / total) * CHART_WIDTH;

  function handleKey(event: KeyboardEvent, key: string): void {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onactivate(key);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      ondeactivate();
    }
  }
</script>

<div
  class="score-waterfall"
  data-testid="score-waterfall"
  data-displayed-score={(score * 100).toFixed(2)}
  aria-label="Signal score decomposition"
>
  <svg viewBox={`0 0 ${WIDTH} ${height}`} role="img" aria-labelledby="waterfall-title waterfall-description">
    <title id="waterfall-title">Signal score waterfall</title>
    <desc id="waterfall-description">Each bar adds a score component to the running signal total.</desc>
    <text class="waterfall-axis-label" x={LABEL_WIDTH} y="18">0</text>
    <text class="waterfall-axis-label" x={LABEL_WIDTH + CHART_WIDTH} y="18" text-anchor="end">{(total * 100).toFixed(0)} signal points</text>
    <line class="waterfall-baseline" x1={LABEL_WIDTH} x2={LABEL_WIDTH + CHART_WIDTH} y1="27" y2="27" />
    {#each rows as row, index (row.key)}
      {@const y = TOP + index * ROW_HEIGHT}
      {#if index > 0}
        <line class="waterfall-connector" x1={x(row.start)} x2={x(row.start)} y1={y - 24} y2={y + 8} />
      {/if}
      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <g
        class="waterfall-row"
        class:active={activeKey === row.key}
        role="button"
        tabindex="0"
        aria-label={`${row.label}, adds ${(row.contribution * 100).toFixed(1)} points, running total ${(row.running * 100).toFixed(1)}`}
        data-score-component={row.key}
        data-contribution={(row.contribution * 100).toFixed(3)}
        onmouseenter={() => onactivate(row.key)}
        onmouseleave={ondeactivate}
        onfocus={() => onactivate(row.key)}
        onblur={ondeactivate}
        onkeydown={(event) => handleKey(event, row.key)}
      >
        <text class="waterfall-label" x="0" y={y + 16}>{row.label}</text>
        <rect class="waterfall-bar" x={x(row.start)} y={y} width={Math.max(3, x(row.running) - x(row.start))} height="24" rx="4" />
        <text class="waterfall-contribution" x={x(row.start) + 9} y={y + 16}>+{(row.contribution * 100).toFixed(1)}</text>
        <text class="waterfall-running" x={LABEL_WIDTH + CHART_WIDTH + 25} y={y + 16}>{(row.running * 100).toFixed(1)} running</text>
      </g>
    {/each}
  </svg>
</div>
