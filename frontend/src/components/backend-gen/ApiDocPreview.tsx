import { useBackendStore } from "../../store/backend-store";

const METHOD_COLORS: Record<string, string> = {
  GET: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400",
  POST: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400",
  PUT: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400",
  DELETE: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400",
};

export default function ApiDocPreview() {
  const { apiDoc } = useBackendStore();

  if (!apiDoc) return null;

  return (
    <div className="space-y-3">
      <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
        API Endpoints ({apiDoc.endpoints.length})
      </div>
      <div className="space-y-1.5 max-h-48 overflow-y-auto">
        {apiDoc.endpoints.map((ep, i) => (
          <div
            key={i}
            className="flex items-center gap-2 px-2 py-1.5 rounded border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-zinc-800/50"
          >
            <span
              className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                METHOD_COLORS[ep.method] || "bg-gray-100 text-gray-600"
              }`}
            >
              {ep.method}
            </span>
            <span className="text-xs font-mono text-gray-700 dark:text-gray-300">
              {ep.path}
            </span>
            <span className="ml-auto text-[10px] text-gray-400 dark:text-gray-500 truncate max-w-[120px]">
              {ep.description}
            </span>
          </div>
        ))}
      </div>

      {apiDoc.data_models.length > 0 && (
        <>
          <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
            Data Models ({apiDoc.data_models.length})
          </div>
          <div className="flex flex-wrap gap-1.5">
            {apiDoc.data_models.map((model, i) => (
              <span
                key={i}
                className="text-[11px] px-2 py-1 rounded bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 border border-purple-200 dark:border-purple-800"
              >
                {model.name} ({model.fields.length} fields)
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
