<script lang="ts">
  export let icon: 'arrow-left' | 'arrow-right' | 'external' | 'expand' | 'back' | 'chevron-down' = 'external';
  export let label: string;
  export let size: 36 | 44 = 36;
  export let href = '';
  export let target: '_blank' | '_self' = '_self';
  export let disabled = false;
  export let onclick: ((event: MouseEvent) => void) | undefined = undefined;
</script>

{#snippet glyph()}
  <svg viewBox="0 0 24 24" aria-hidden="true">
    {#if icon === 'external'}
      <path d="M9 6H6.8A2.8 2.8 0 0 0 4 8.8v8.4A2.8 2.8 0 0 0 6.8 20h8.4a2.8 2.8 0 0 0 2.8-2.8V15M13 4h7v7M20 4l-9 9" />
    {:else if icon === 'expand'}
      <path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5" />
    {:else if icon === 'arrow-right'}
      <path d="M5 12h14M14 7l5 5-5 5" />
    {:else if icon === 'chevron-down'}
      <path d="M6 9l6 6 6-6" />
    {:else}
      <path d="M19 12H5M10 7l-5 5 5 5" />
    {/if}
  </svg>
{/snippet}

{#if href}
  <a class="circle-button" style:width={`${size}px`} style:height={`${size}px`} {href} {target} rel={target === '_blank' ? 'noreferrer' : undefined} aria-label={label}>
    {@render glyph()}
  </a>
{:else}
  <button class="circle-button" type="button" style:width={`${size}px`} style:height={`${size}px`} aria-label={label} {disabled} {onclick}>
    {@render glyph()}
  </button>
{/if}

<style>
  .circle-button {
    flex: 0 0 auto;
    display: grid;
    place-items: center;
    border: 1px solid var(--line);
    border-radius: 50%;
    background: var(--white);
    color: var(--ink);
    box-shadow: 0 2px 5px rgba(29,40,33,.04);
    cursor: pointer;
    transition: transform 150ms ease, box-shadow 150ms ease, border-color 150ms ease;
  }
  .circle-button:hover { transform: translateY(-2px); border-color: #c7cdc8; box-shadow: 0 8px 18px rgba(29,40,33,.09); }
  .circle-button:disabled { opacity: .36; cursor: default; transform: none; box-shadow: none; }
  svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 1.65; stroke-linecap: round; stroke-linejoin: round; }
  @media (prefers-reduced-motion: reduce) { .circle-button { transition: none; } }
</style>
