import { create } from "zustand";

export interface ApiEndpoint {
  method: "GET" | "POST" | "PUT" | "DELETE";
  path: string;
  description: string;
  request_body?: Record<string, unknown> | null;
  response_body?: Record<string, unknown>;
}

export interface DataModel {
  name: string;
  fields: {
    name: string;
    type: string;
    primary_key?: boolean;
    nullable?: boolean;
  }[];
}

export interface ApiDoc {
  recommended_language: string;
  recommend_reason: string;
  endpoints: ApiEndpoint[];
  data_models: DataModel[];
}

export type BackendLanguage = "python" | "php" | "java";

export type BackendStage =
  | "idle"
  | "generating_doc"
  | "doc_ready"
  | "generating_code"
  | "code_ready";

interface BackendStore {
  stage: BackendStage;
  setStage: (stage: BackendStage) => void;

  // Stage 2 output
  apiDoc: ApiDoc | null;
  setApiDoc: (doc: ApiDoc) => void;

  // Language selection
  selectedLanguage: BackendLanguage;
  setSelectedLanguage: (lang: BackendLanguage) => void;

  // Stage 3 output
  backendFiles: Record<string, string>;
  setBackendFiles: (files: Record<string, string>) => void;
  addFile: (path: string, content: string) => void;

  // File viewer state
  selectedFile: string | null;
  setSelectedFile: (path: string | null) => void;

  // Error
  error: string | null;
  setError: (error: string | null) => void;

  // Reset
  reset: () => void;
}

export const useBackendStore = create<BackendStore>((set) => ({
  stage: "idle",
  setStage: (stage) => set({ stage }),

  apiDoc: null,
  setApiDoc: (doc) => set({ apiDoc: doc }),

  selectedLanguage: "python",
  setSelectedLanguage: (lang) => set({ selectedLanguage: lang }),

  backendFiles: {},
  setBackendFiles: (files) => set({ backendFiles: files }),
  addFile: (path, content) =>
    set((state) => ({
      backendFiles: { ...state.backendFiles, [path]: content },
    })),

  selectedFile: null,
  setSelectedFile: (path) => set({ selectedFile: path }),

  error: null,
  setError: (error) => set({ error }),

  reset: () =>
    set({
      stage: "idle",
      apiDoc: null,
      selectedLanguage: "python",
      backendFiles: {},
      selectedFile: null,
      error: null,
    }),
}));
