<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../api/client';
  import type { SearchHit } from '../api/types';
  import { navigate } from '../router';

  interface PaletteRow extends SearchHit { group: string; verb?: boolean }
  let open = false;
  let query = '';
  let input: HTMLInputElement;
  let rows: PaletteRow[] = [];
  let selected = 0;
  let searching = false;
  let timer: ReturnType<typeof setTimeout>;

  function openPalette(): void {
    open = true;
    selected = 0;
    requestAnimationFrame(() => input?.focus());
  }

  function close(): void {
    open = false;
    query = '';
    rows = [];
  }

  function go(row: PaletteRow): void {
    close();
    navigate(row.route);
  }

  async function runSearch(value: string): Promise<void> {
    clearTimeout(timer);
    if (!value.trim()) { rows = []; searching = false; return; }
    searching = true;
    timer = setTimeout(async () => {
      const response = await api.search(value);
      const groupLabels: Record<string, string> = { founder: 'Founders', company: 'Companies', claim: 'Memo claims', evidence: 'Evidence', memo_section: 'Memo sections', thesis_term: 'Thesis' };
      const resultRows = response.groups.flatMap((group) => group.hits.map((hit) => ({ ...hit, group: groupLabels[group.type] ?? group.type })));
      const founder = resultRows.find((row) => row.doc_type === 'founder');
      const sector = resultRows.find((row) => row.doc_type === 'thesis_term');
      const verbs: PaletteRow[] = [];
      if (founder) {
        verbs.push({ ...founder, doc_id: `deep-${founder.doc_id}`, title: `Deep dive on ${founder.title}…`, subtitle: 'Start founder analysis', snippet: 'Open the founder health record', group: 'Actions', verb: true });
        verbs.push({ ...founder, doc_id: `memo-${founder.doc_id}`, title: 'Open memo…', subtitle: founder.title, snippet: `Review claims for ${founder.title}`, route: `${founder.route}#memo`, group: 'Actions', verb: true });
      }
      if (sector) verbs.push({ ...sector, doc_id: `filter-${sector.doc_id}`, title: `Filter radar to ${sector.title}`, subtitle: 'Apply thesis lens', group: 'Actions', verb: true });
      rows = [...verbs, ...resultRows];
      selected = 0;
      searching = false;
    }, 80);
  }

  function onInput(): void { void runSearch(query); }

  function onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') { close(); return; }
    if (event.key === 'ArrowDown') { event.preventDefault(); selected = Math.min(selected + 1, rows.length - 1); }
    if (event.key === 'ArrowUp') { event.preventDefault(); selected = Math.max(selected - 1, 0); }
    if (event.key === 'Enter' && rows[selected]) { event.preventDefault(); go(rows[selected]); }
  }

  onMount(() => {
    const globalKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.isContentEditable;
      if ((event.key.toLowerCase() === 'k' && (event.metaKey || event.ctrlKey)) || (event.key === '/' && !typing)) {
        event.preventDefault(); openPalette();
      }
    };
    const customOpen = () => openPalette();
    window.addEventListener('keydown', globalKey);
    window.addEventListener('palette:open', customOpen);
    return () => {
      window.removeEventListener('keydown', globalKey);
      window.removeEventListener('palette:open', customOpen);
    };
  });

  $: groupedRows = rows.reduce<Record<string, PaletteRow[]>>((groups, row) => {
    (groups[row.group] ??= []).push(row);
    return groups;
  }, {});
</script>

{#if open}
  <div class="palette-backdrop" role="presentation" onclick={(event) => { if (event.target === event.currentTarget) close(); }}>
    <div class="command-palette" role="dialog" aria-modal="true" aria-label="Search and command palette" tabindex="-1" onkeydown={onKeydown}>
      <div class="palette-input-wrap">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="m16 16 5 5"></path></svg>
        <input bind:this={input} bind:value={query} oninput={onInput} role="combobox" aria-expanded="true" aria-controls="palette-results" aria-activedescendant={rows[selected] ? `palette-${rows[selected].doc_id}` : undefined} placeholder="Find a founder, company, claim, or thesis term…" />
        <kbd>esc</kbd>
      </div>
      <div id="palette-results" class="palette-results" role="listbox" aria-label="Search results">
        {#if searching}<p class="palette-state">Searching intelligence…</p>
        {:else if !query}<p class="palette-state">Type a name, company, memo claim, or sector.</p>
        {:else if !rows.length}<p class="palette-state">No matching intelligence found.</p>
        {:else}
          {#each Object.entries(groupedRows) as [group, hits]}
            <div class="palette-group">
              <div class="palette-group-label">{group}</div>
              {#each hits as row}
                {@const index = rows.indexOf(row)}
                <button id={`palette-${row.doc_id}`} class:active={index === selected} class:verb-row={row.verb} type="button" role="option" aria-selected={index === selected} onmouseenter={() => selected = index} onclick={() => go(row)}>
                  <span class="result-icon" aria-hidden="true">{row.verb ? '↳' : row.doc_type === 'founder' ? '◎' : row.doc_type === 'claim' ? '≡' : '⌁'}</span>
                  <span class="result-copy"><strong>{row.title}</strong><small>{row.subtitle}</small><span class="result-snippet">{@html row.snippet}</span></span>
                  <span class="result-enter" aria-hidden="true">↵</span>
                </button>
              {/each}
            </div>
          {/each}
        {/if}
      </div>
      <footer class="palette-footer"><span><kbd>↑</kbd><kbd>↓</kbd> Navigate</span><span><kbd>↵</kbd> Open</span><span>Search updates in 80ms</span></footer>
    </div>
  </div>
{/if}
