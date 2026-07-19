import { writable } from 'svelte/store';

export interface ThesisSettings {
  sector: string;
  stage: string;
  geography: string;
  signalWeight: number;
  momentumWeight: number;
  thesisWeight: number;
}

export type ThesisFilter = 'sector' | 'stage' | 'geography';
export type ThesisWeight = 'signalWeight' | 'momentumWeight' | 'thesisWeight';

export const THESIS_STORAGE_KEY = 'vc-brain:thesis-overlay';

export const fundDefaultSettings: ThesisSettings = {
  sector: '',
  stage: '',
  geography: '',
  signalWeight: 64,
  momentumWeight: 22,
  thesisWeight: 14
};

function loadSettings(): ThesisSettings {
  try {
    const saved = localStorage.getItem(THESIS_STORAGE_KEY);
    if (!saved) return { ...fundDefaultSettings };
    const overlay = JSON.parse(saved) as Partial<ThesisSettings>;
    return { ...fundDefaultSettings, ...overlay };
  } catch {
    return { ...fundDefaultSettings };
  }
}

function persist(settings: ThesisSettings): void {
  try {
    localStorage.setItem(THESIS_STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // Keep the in-memory lens usable when browser storage is unavailable.
  }
}

export const thesisSettings = writable<ThesisSettings>(loadSettings());

export function toggleThesisFilter(filter: ThesisFilter, value: string): void {
  thesisSettings.update((settings) => {
    const next = { ...settings, [filter]: settings[filter] === value ? '' : value };
    persist(next);
    return next;
  });
}

export function setThesisFilter(filter: ThesisFilter, value: string): void {
  thesisSettings.update((settings) => {
    const next = { ...settings, [filter]: value };
    persist(next);
    return next;
  });
}

export function setThesisWeight(weight: ThesisWeight, value: number): void {
  thesisSettings.update((settings) => {
    const next = { ...settings, [weight]: Math.max(0, Math.min(100, value)) };
    persist(next);
    return next;
  });
}

export function resetThesisSettings(): void {
  try {
    localStorage.removeItem(THESIS_STORAGE_KEY);
  } catch {
    // The in-memory reset still applies when browser storage is unavailable.
  }
  thesisSettings.set({ ...fundDefaultSettings });
}
