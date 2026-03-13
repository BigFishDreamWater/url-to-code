import { WS_BACKEND_URL } from "../config";
import {
  ApiDoc,
  BackendLanguage,
  useBackendStore,
} from "../store/backend-store";

/**
 * Stage 2: Generate API documentation from frontend code.
 */
export function generateApiDoc(frontendCode: string): void {
  const store = useBackendStore.getState();
  store.setStage("generating_doc");
  store.setError(null);

  const ws = new WebSocket(`${WS_BACKEND_URL}/generate-api-doc`);

  ws.onopen = () => {
    ws.send(JSON.stringify({ frontendCode }));
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    if (msg.type === "apiDoc") {
      try {
        const doc: ApiDoc = JSON.parse(msg.value);
        const s = useBackendStore.getState();
        s.setApiDoc(doc);
        s.setSelectedLanguage(
          (doc.recommended_language as BackendLanguage) || "python"
        );
        s.setStage("doc_ready");
      } catch {
        useBackendStore.getState().setError("Failed to parse API doc");
        useBackendStore.getState().setStage("idle");
      }
    } else if (msg.type === "error") {
      useBackendStore.getState().setError(msg.value);
      useBackendStore.getState().setStage("idle");
    }
    // ignore "status", "chunk", "complete"
  };

  ws.onerror = () => {
    useBackendStore.getState().setError("WebSocket connection failed");
    useBackendStore.getState().setStage("idle");
  };

  ws.onclose = () => {
    // If still generating, it means connection dropped
    const s = useBackendStore.getState();
    if (s.stage === "generating_doc") {
      s.setError("Connection lost during API doc generation");
      s.setStage("idle");
    }
  };
}

/**
 * Stage 3: Generate backend code from API documentation.
 */
export function generateBackendCode(
  apiDoc: ApiDoc,
  language: BackendLanguage
): void {
  const store = useBackendStore.getState();
  store.setStage("generating_code");
  store.setError(null);
  store.setBackendFiles({});

  const ws = new WebSocket(`${WS_BACKEND_URL}/generate-backend`);

  ws.onopen = () => {
    ws.send(
      JSON.stringify({
        apiDoc: JSON.stringify(apiDoc, null, 2),
        language,
      })
    );
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    if (msg.type === "setFile" && msg.data) {
      // Streaming: individual file created
      useBackendStore.getState().addFile(msg.data.path, msg.data.content);
    } else if (msg.type === "backendFiles") {
      // Final: all files
      try {
        const files: Record<string, string> = JSON.parse(msg.value);
        useBackendStore.getState().setBackendFiles(files);
      } catch {
        // keep whatever we streamed
      }
      useBackendStore.getState().setStage("code_ready");
    } else if (msg.type === "complete") {
      const s = useBackendStore.getState();
      if (s.stage !== "code_ready") {
        s.setStage("code_ready");
      }
    } else if (msg.type === "error") {
      useBackendStore.getState().setError(msg.value);
      useBackendStore.getState().setStage("doc_ready"); // go back to doc_ready so user can retry
    }
  };

  ws.onerror = () => {
    useBackendStore.getState().setError("WebSocket connection failed");
    useBackendStore.getState().setStage("doc_ready");
  };

  ws.onclose = () => {
    const s = useBackendStore.getState();
    if (s.stage === "generating_code") {
      s.setError("Connection lost during backend generation");
      s.setStage("doc_ready");
    }
  };
}
