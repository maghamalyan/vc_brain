<script lang="ts">
  export let variant: 'filter' | 'nav' | 'event' | 'status' = 'filter';
  export let label: string;
  export let icon = '';
  export let count: number | null = null;
  export let active = false;
  export let disabled = false;
  export let tone = '';
  export let href = '';
  export let target: '_blank' | '_self' = '_self';
  export let pressed: boolean | undefined = undefined;
  export let onclick: ((event: MouseEvent) => void) | undefined = undefined;
</script>

{#if href}
  <a
    class="chip chip-{variant} tone-{tone}"
    class:active
    {href}
    {target}
    rel={target === '_blank' ? 'noreferrer' : undefined}
    aria-label={label}
  >
    {#if icon}<span class="chip-icon" aria-hidden="true">{icon}</span>{/if}
    <span>{label}</span>
    {#if count !== null}<strong>{count}</strong>{/if}
  </a>
{:else}
  <button
    type="button"
    class="chip chip-{variant} tone-{tone}"
    class:active
    {disabled}
    aria-pressed={pressed}
    {onclick}
  >
    {#if icon}<span class="chip-icon" aria-hidden="true">{icon}</span>{/if}
    <span>{label}</span>
    {#if count !== null}<strong>{count}</strong>{/if}
  </button>
{/if}

<style>
  .chip {
    min-height: 30px;
    padding: 5px 9px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: var(--nested-surface, #fbfcfa);
    color: var(--ink-soft);
    font-size: 10px;
    font-weight: 680;
    line-height: 1;
    text-decoration: none;
    white-space: nowrap;
    flex-shrink: 0;
    cursor: pointer;
    transition: transform 150ms ease, border-color 150ms ease, background 150ms ease, color 150ms ease;
  }
  .chip:hover { transform: translateY(-1px); border-color: #c6ccc7; }
  .chip:disabled { cursor: default; opacity: .52; transform: none; }
  .chip-icon { width: 14px; height: 14px; display: grid; place-items: center; font-size: 11px; }
  strong {
    min-width: 19px;
    height: 19px;
    padding: 0 5px;
    display: grid;
    place-items: center;
    border-radius: 999px;
    background: #e9ece8;
    color: var(--muted);
    font: 700 9px/1 var(--mono-font, ui-monospace, monospace);
    font-variant-numeric: tabular-nums;
  }
  .chip-nav { min-height: 34px; padding-inline: 12px; background: var(--white); }
  .chip-nav.active { border-color: var(--ink); background: var(--ink); color: var(--paper); }
  .chip-nav.active strong { background: rgba(255,255,255,.14); color: var(--paper); }
  .chip-filter.active { border-color: #b8cdc0; background: var(--forest-pale); color: var(--forest); }
  .chip-filter.active strong { background: var(--forest); color: var(--white); }
  .chip-event { min-height: 24px; padding: 3px 7px; background: var(--white); font-size: 8px; }
  .chip-event .chip-icon { width: 11px; height: 11px; font-size: 9px; }
  .chip-status { min-height: 25px; padding: 3px 8px; font-size: 8px; font-weight: 760; letter-spacing: .06em; text-transform: uppercase; cursor: default; }
  .chip-status:hover { transform: none; }
  .chip-status.tone-forest { border-color: #b9d2c3; background: var(--forest-pale); color: var(--forest); }
  .chip-status.tone-blue { border-color: #c4d4e4; background: var(--blue-pale); color: var(--blue); }
  .chip-status.tone-amber { border-color: #eed3ad; background: var(--amber-pale); color: var(--amber); }
  .chip-status.tone-live { border-color: #789c38; background: var(--live); color: #26380e; }
  @media (prefers-reduced-motion: reduce) { .chip { transition: none; } }
</style>
