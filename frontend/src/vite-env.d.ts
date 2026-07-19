/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_MOCK?: string;
  readonly VITE_DEEPDIVE_ENABLED?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
