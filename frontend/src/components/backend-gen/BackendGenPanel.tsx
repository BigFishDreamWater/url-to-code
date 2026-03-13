import { LuServer, LuLoader2 } from "react-icons/lu";
import { useBackendStore } from "../../store/backend-store";
import { useProjectStore } from "../../store/project-store";
import { generateApiDoc, generateBackendCode } from "../../lib/generateBackend";
import ApiDocPreview from "./ApiDocPreview";
import LanguageSelector from "./LanguageSelector";
import FileTreeViewer from "./FileTreeViewer";

export default function BackendGenPanel() {
  const { stage, apiDoc, selectedLanguage, error, reset } = useBackendStore();
  const { head, commits } = useProjectStore();

  const getFrontendCode = (): string => {
    if (!head || !commits[head]) return "";
    const commit = commits[head];
    return commit.variants[commit.selectedVariantIndex]?.code || "";
  };

  const handleGenerateDoc = () => {
    const code = getFrontendCode();
    if (!code) return;
    generateApiDoc(code);
  };

  const handleGenerateBackend = () => {
    if (!apiDoc) return;
    generateBackendCode(apiDoc, selectedLanguage);
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 pt-3 mt-3 space-y-3">
      {/* Error display */}
      {error && (
        <div className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-md p-2">
          {error}
        </div>
      )}

      {/* Stage: idle - Show Generate Backend button */}
      {stage === "idle" && (
        <button
          onClick={handleGenerateDoc}
          disabled={!getFrontendCode()}
          className="flex items-center justify-center gap-2 w-full px-3 py-2 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <LuServer className="w-4 h-4" />
          Generate Backend
        </button>
      )}

      {/* Stage: generating_doc - Loading */}
      {stage === "generating_doc" && (
        <div className="flex items-center justify-center gap-2 py-3 text-sm text-gray-500 dark:text-gray-400">
          <LuLoader2 className="w-4 h-4 animate-spin" />
          Analyzing frontend code...
        </div>
      )}

      {/* Stage: doc_ready - Show API doc + language selector + confirm button */}
      {stage === "doc_ready" && (
        <>
          <ApiDocPreview />
          <LanguageSelector />
          <div className="flex gap-2">
            <button
              onClick={reset}
              className="flex-1 px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleGenerateBackend}
              className="flex-1 px-3 py-1.5 text-xs font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors"
            >
              Confirm & Generate
            </button>
          </div>
        </>
      )}

      {/* Stage: generating_code - Loading + streaming files */}
      {stage === "generating_code" && (
        <>
          <div className="flex items-center justify-center gap-2 py-2 text-sm text-gray-500 dark:text-gray-400">
            <LuLoader2 className="w-4 h-4 animate-spin" />
            Generating backend code...
          </div>
          <FileTreeViewer />
        </>
      )}

      {/* Stage: code_ready - Show file tree */}
      {stage === "code_ready" && (
        <>
          <FileTreeViewer />
          <button
            onClick={reset}
            className="w-full px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
          >
            Reset
          </button>
        </>
      )}
    </div>
  );
}
