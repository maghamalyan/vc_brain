import { writable } from 'svelte/store';

export const route = writable(`${window.location.pathname}${window.location.search}${window.location.hash}`);

export function navigate(to: string): void {
  if (to === `${window.location.pathname}${window.location.search}${window.location.hash}`) return;
  history.pushState({}, '', to);
  route.set(to);
  window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
}

window.addEventListener('popstate', () => route.set(`${window.location.pathname}${window.location.search}${window.location.hash}`));
