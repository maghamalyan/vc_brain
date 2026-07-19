<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../api/client';
  import type { Thesis } from '../api/types';
  import Chip from '../components/Chip.svelte';
  import {
    resetThesisSettings,
    setThesisWeight,
    thesisSettings,
    toggleThesisFilter,
    type ThesisFilter,
    type ThesisWeight
  } from '../thesisStore';

  let thesis: Thesis | null = null;
  let error = '';

  const currency = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: 'compact',
    maximumFractionDigits: 1
  });

  const filterSections: Array<{ key: ThesisFilter; label: string }> = [
    { key: 'sector', label: 'Sectors' },
    { key: 'stage', label: 'Stages' },
    { key: 'geography', label: 'Geographies' }
  ];
  const weightRows: Array<{ key: ThesisWeight; label: string }> = [
    { key: 'signalWeight', label: 'Signal strength' },
    { key: 'momentumWeight', label: 'Momentum' },
    { key: 'thesisWeight', label: 'Thesis fit' }
  ];

  function optionsFor(filter: ThesisFilter): string[] {
    if (!thesis) return [];
    return filter === 'sector' ? thesis.sectors : filter === 'stage' ? thesis.stages : thesis.geographies;
  }

  onMount(() => {
    void api.getThesis()
      .then((response) => { thesis = response; })
      .catch((reason) => { error = reason instanceof Error ? reason.message : 'Unable to load the fund thesis'; });
  });
</script>

<section class="thesis-page shell" aria-labelledby="thesis-page-title">
  <header class="thesis-page-header">
    <div>
      <p class="eyebrow"><span>Fund configuration</span> · Ranking mandate</p>
      <h1 id="thesis-page-title">The lens behind<br />the radar.</h1>
    </div>
    <p>Set the mandate used to rank emerging founder signals. Changes take effect on Radar immediately.</p>
  </header>

  <div class="local-config-banner" role="note">
    <span aria-hidden="true">⌁</span>
    <p><strong>Local configuration</strong> Saved only in this browser. No changes are written to the server.</p>
  </div>

  {#if error}
    <div class="page-state" role="alert">{error}</div>
  {:else if !thesis}
    <div class="page-state" aria-live="polite">Loading fund mandate…</div>
  {:else}
    <div class="thesis-page-grid">
      <section class="mandate-panel" aria-labelledby="mandate-title">
        <header class="thesis-panel-heading">
          <div><p class="eyebrow">01 · Scope</p><h2 id="mandate-title">Fund mandate</h2></div>
          <span>Served baseline</span>
        </header>

        {#each filterSections as section}
          <fieldset class="mandate-fieldset">
            <legend>{section.label}</legend>
            <p>Choose one preference to strengthen its thesis-fit contribution.</p>
            <div class="mandate-chips" data-testid={`thesis-${section.key}-chips`}>
              {#each optionsFor(section.key) as item}
                <Chip
                  variant="filter"
                  label={item}
                  active={$thesisSettings[section.key] === item}
                  pressed={$thesisSettings[section.key] === item}
                  onclick={() => toggleThesisFilter(section.key, item)}
                />
              {/each}
            </div>
          </fieldset>
        {/each}

        <div class="mandate-facts">
          <article>
            <span>Check size</span>
            <strong>{currency.format(thesis.check_size_usd[0])}–{currency.format(thesis.check_size_usd[1])}</strong>
            <small>Initial investment · USD</small>
          </article>
          <article>
            <span>Risk appetite</span>
            <p>{thesis.risk_appetite}</p>
          </article>
        </div>
      </section>

      <aside class="ranking-panel" aria-labelledby="ranking-title">
        <header class="thesis-panel-heading">
          <div><p class="eyebrow">02 · Calibration</p><h2 id="ranking-title">Ranking weights</h2></div>
          <span>{$thesisSettings.signalWeight + $thesisSettings.momentumWeight + $thesisSettings.thesisWeight} pts</span>
        </header>
        <p class="ranking-intro">Tune how the radar combines observed signal, recent velocity, and mandate alignment.</p>
        <div class="thesis-weight-list">
          {#each weightRows as row}
            <label>
              <span>{row.label}<b>{$thesisSettings[row.key]}</b></span>
              <input
                aria-label={`${row.label} weight`}
                type="range"
                min="0"
                max="100"
                value={$thesisSettings[row.key]}
                oninput={(event) => setThesisWeight(row.key, Number(event.currentTarget.value))}
              />
            </label>
          {/each}
        </div>
        <div class="ranking-note">
          <span>Mandate note</span>
          <p>{thesis.notes}</p>
        </div>
        <button class="secondary-button reset-thesis" type="button" onclick={resetThesisSettings}>Reset to fund defaults</button>
      </aside>
    </div>
  {/if}
</section>
