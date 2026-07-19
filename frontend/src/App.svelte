<script lang="ts">
  import { route, navigate } from './lib/router';
  import CommandPalette from './lib/components/CommandPalette.svelte';
  import Radar from './lib/pages/Radar.svelte';
  import CandidatePage from './lib/pages/CandidatePage.svelte';
  import RunPage from './lib/pages/RunPage.svelte';
  import { isMockMode } from './lib/api/client';

  const pathOnly = ($route: string) => $route.split(/[?#]/)[0];
</script>

<a class="skip-link" href="#main-content">Skip to content</a>
<header class="topbar">
  <a class="brand" href="/" onclick={(event) => { event.preventDefault(); navigate('/'); }} aria-label="VC Brain radar">
    <span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i></span>
    <span>VC Brain</span>
  </a>
  <nav class="topnav" aria-label="Primary navigation">
    <a class:active={pathOnly($route) === '/'} href="/" onclick={(event) => { event.preventDefault(); navigate('/'); }}>Radar</a>
    <span>Portfolio</span>
    <span>Thesis</span>
  </nav>
  <div class="top-actions">
    {#if isMockMode}<span class="fixture-flag"><i></i>Fixture intelligence</span>{/if}
    <button class="palette-trigger" type="button" onclick={() => window.dispatchEvent(new CustomEvent('palette:open'))} aria-label="Open command palette">
      <span>Search intelligence</span><kbd>⌘ K</kbd>
    </button>
  </div>
</header>

<main id="main-content">
  {#if pathOnly($route) === '/'}
    <Radar />
  {:else if pathOnly($route).startsWith('/candidate/')}
    <CandidatePage login={decodeURIComponent(pathOnly($route).slice('/candidate/'.length))} />
  {:else if pathOnly($route).startsWith('/runs/')}
    <RunPage runId={decodeURIComponent(pathOnly($route).slice('/runs/'.length))} />
  {:else}
    <section class="not-found shell">
      <p class="eyebrow">404 · Signal lost</p>
      <h1>That intelligence record is not here.</h1>
      <button class="primary-button" onclick={() => navigate('/')}>Return to radar</button>
    </section>
  {/if}
</main>

<CommandPalette />
