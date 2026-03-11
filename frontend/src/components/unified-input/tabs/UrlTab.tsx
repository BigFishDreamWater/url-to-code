import { useState } from "react";
import { HTTP_BACKEND_URL } from "../../../config";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { toast } from "react-hot-toast";
import OutputSettingsSection from "../../settings/OutputSettingsSection";
import { Stack } from "../../../lib/stacks";

interface Props {
  doCreate: (
    urls: string[],
    inputMode: "image" | "video",
    textPrompt?: string,
    dom?: string,
  ) => void;
  stack: Stack;
  setStack: (stack: Stack) => void;
}

function isFigmaUrl(url: string): boolean {
  return /^https?:\/\/([\w.-]*\.)?figma\.com\//i.test(url.trim());
}

function UrlTab({ doCreate, stack, setStack }: Props) {
  const [isLoading, setIsLoading] = useState(false);
  const [referenceUrl, setReferenceUrl] = useState("");

  async function takeScreenshot() {
    const trimmedUrl = referenceUrl.trim();

    if (!trimmedUrl) {
      toast.error("Please enter a URL");
      return;
    }

    if (trimmedUrl.toLowerCase().startsWith("file://")) {
      toast.error(
        "file:// URLs are not supported. Use the Upload tab for local files.",
      );
      return;
    }

    if (isFigmaUrl(trimmedUrl)) {
      toast.error(
        "Figma URLs are not supported. Export as images and use Upload tab.",
        { duration: 6000 },
      );
      return;
    }

    try {
      setIsLoading(true);
      const response = await fetch(`${HTTP_BACKEND_URL}/api/screenshot`, {
        method: "POST",
        body: JSON.stringify({ url: trimmedUrl }),
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to capture screenshot");
      }

      const res = await response.json();
      doCreate([res.url], "image", "", res.dom || "");
    } catch (error) {
      console.error(error);
      toast.error(
        error instanceof Error ? error.message : "Failed to capture screenshot",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="w-full space-y-3">
      <div className="flex gap-2">
        <Input
          placeholder="输入网址，如 https://example.com"
          onChange={(e) => setReferenceUrl(e.target.value)}
          value={referenceUrl}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !isLoading) takeScreenshot();
          }}
          className="flex-1"
          data-testid="url-input"
        />
        <Button
          onClick={takeScreenshot}
          disabled={isLoading}
          size="lg"
          data-testid="url-capture"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg
                className="animate-spin h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              访问中...
            </span>
          ) : (
            "生成代码"
          )}
        </Button>
      </div>
      {isFigmaUrl(referenceUrl) && (
        <p className="text-xs text-amber-600 dark:text-amber-400">
          Figma URLs are not supported. Export as images and use Upload tab.
        </p>
      )}
      <OutputSettingsSection stack={stack} setStack={setStack} />
    </div>
  );
}

export default UrlTab;
