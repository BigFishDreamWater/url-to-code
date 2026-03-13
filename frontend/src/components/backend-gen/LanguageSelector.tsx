import { BackendLanguage, useBackendStore } from "../../store/backend-store";

const LANGUAGES: {
  value: BackendLanguage;
  label: string;
  framework: string;
}[] = [
  { value: "python", label: "Python", framework: "Flask" },
  { value: "php", label: "PHP", framework: "Laravel" },
  { value: "java", label: "Java", framework: "Spring Boot" },
];

export default function LanguageSelector() {
  const { selectedLanguage, setSelectedLanguage, apiDoc } = useBackendStore();
  const recommended = apiDoc?.recommended_language;

  return (
    <div className="space-y-2">
      <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
        Backend Language
      </div>
      <div className="space-y-1.5">
        {LANGUAGES.map((lang) => (
          <label
            key={lang.value}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors ${
              selectedLanguage === lang.value
                ? "border-blue-500 bg-blue-50 dark:bg-blue-950/30"
                : "border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-zinc-800"
            }`}
          >
            <input
              type="radio"
              name="backend-language"
              value={lang.value}
              checked={selectedLanguage === lang.value}
              onChange={() => setSelectedLanguage(lang.value)}
              className="text-blue-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              {lang.label} ({lang.framework})
            </span>
            {recommended === lang.value && (
              <span className="ml-auto text-[10px] px-1.5 py-0.5 bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 rounded">
                Recommended
              </span>
            )}
          </label>
        ))}
      </div>
      {apiDoc?.recommend_reason && (
        <p className="text-[11px] text-gray-400 dark:text-gray-500 leading-tight">
          {apiDoc.recommend_reason}
        </p>
      )}
    </div>
  );
}
