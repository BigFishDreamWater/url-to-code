import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Stack } from "../../lib/stacks";
import { Settings } from "../../types";
import UploadTab from "./tabs/UploadTab";
import UrlTab from "./tabs/UrlTab";
import TextTab from "./tabs/TextTab";
import ImportTab from "./tabs/ImportTab";

interface Props {
  doCreate: (
    images: string[],
    inputMode: "image" | "video",
    textPrompt?: string,
    dom?: string,
  ) => void;
  doCreateFromText: (text: string) => void;
  importFromCode: (code: string, stack: Stack) => void;
  settings: Settings;
  setSettings: React.Dispatch<React.SetStateAction<Settings>>;
}

type InputTab = "upload" | "text" | "import";

function UnifiedInputPane({
  doCreate,
  doCreateFromText,
  importFromCode,
  settings,
  setSettings,
}: Props) {
  const [activeTab, setActiveTab] = useState<InputTab>("upload");

  function setStack(stack: Stack) {
    setSettings((prev: Settings) => ({
      ...prev,
      generatedCodeConfig: stack,
    }));
  }

  return (
    <div className="w-full max-w-2xl mx-auto px-4">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          url-to-code
        </h1>
        <p className="text-gray-500 dark:text-zinc-400">
          输入网址或上传截图，生成前端代码
        </p>
      </div>

      {/* URL Input — always visible, primary entry */}
      <div className="mb-6">
        <UrlTab
          doCreate={doCreate}
          stack={settings.generatedCodeConfig}
          setStack={setStack}
        />
      </div>

      {/* Divider */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1 border-t border-gray-200 dark:border-zinc-700" />
        <span className="text-sm text-gray-400 dark:text-zinc-500">或者</span>
        <div className="flex-1 border-t border-gray-200 dark:border-zinc-700" />
      </div>

      {/* Secondary input tabs */}
      <Tabs
        value={activeTab}
        onValueChange={(v) => setActiveTab(v as InputTab)}
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="upload" data-testid="tab-upload">
            Upload
          </TabsTrigger>
          <TabsTrigger value="text" data-testid="tab-text">
            Text
          </TabsTrigger>
          <TabsTrigger value="import" data-testid="tab-import">
            Import
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="mt-0">
          <UploadTab
            doCreate={doCreate}
            stack={settings.generatedCodeConfig}
            setStack={setStack}
          />
        </TabsContent>

        <TabsContent value="text" className="mt-0">
          <TextTab
            doCreateFromText={doCreateFromText}
            stack={settings.generatedCodeConfig}
            setStack={setStack}
          />
        </TabsContent>

        <TabsContent value="import" className="mt-0">
          <ImportTab importFromCode={importFromCode} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default UnifiedInputPane;
