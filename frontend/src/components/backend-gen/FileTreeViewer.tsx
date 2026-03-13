import { useMemo } from "react";
import { useBackendStore } from "../../store/backend-store";
import { LuFile, LuFolder, LuDownload } from "react-icons/lu";

interface TreeNode {
  name: string;
  path: string;
  isDir: boolean;
  children: TreeNode[];
}

function buildTree(files: Record<string, string>): TreeNode[] {
  const root: TreeNode[] = [];
  const paths = Object.keys(files).sort();

  for (const filePath of paths) {
    const parts = filePath.split("/");
    let current = root;

    for (let i = 0; i < parts.length; i++) {
      const name = parts[i];
      const isLast = i === parts.length - 1;
      const partialPath = parts.slice(0, i + 1).join("/");

      let existing = current.find((n) => n.name === name);
      if (!existing) {
        existing = {
          name,
          path: partialPath,
          isDir: !isLast,
          children: [],
        };
        current.push(existing);
      }
      current = existing.children;
    }
  }

  return root;
}

function TreeItem({
  node,
  depth,
  selectedFile,
  onSelect,
}: {
  node: TreeNode;
  depth: number;
  selectedFile: string | null;
  onSelect: (path: string) => void;
}) {
  const isSelected = node.path === selectedFile;

  return (
    <>
      <button
        onClick={() => !node.isDir && onSelect(node.path)}
        className={`flex items-center gap-1.5 w-full text-left px-2 py-1 text-xs rounded transition-colors ${
          isSelected
            ? "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300"
            : node.isDir
            ? "text-gray-500 dark:text-gray-400 cursor-default"
            : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-zinc-800 cursor-pointer"
        }`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {node.isDir ? (
          <LuFolder className="w-3.5 h-3.5 text-yellow-500 flex-shrink-0" />
        ) : (
          <LuFile className="w-3.5 h-3.5 flex-shrink-0" />
        )}
        <span className="truncate">{node.name}</span>
      </button>
      {node.children.map((child) => (
        <TreeItem
          key={child.path}
          node={child}
          depth={depth + 1}
          selectedFile={selectedFile}
          onSelect={onSelect}
        />
      ))}
    </>
  );
}

function downloadZip(files: Record<string, string>) {
  // Simple approach: create a combined text file with all files
  // For a real zip, we'd need JSZip, but let's keep deps minimal
  let content = "";
  for (const [path, code] of Object.entries(files)) {
    content += `${"=".repeat(60)}\n`;
    content += `FILE: ${path}\n`;
    content += `${"=".repeat(60)}\n`;
    content += code;
    content += "\n\n";
  }
  const blob = new Blob([content], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "backend-project.txt";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function FileTreeViewer() {
  const { backendFiles, selectedFile, setSelectedFile } = useBackendStore();

  const tree = useMemo(() => buildTree(backendFiles), [backendFiles]);
  const fileCount = Object.keys(backendFiles).length;
  const currentCode = selectedFile ? backendFiles[selectedFile] || "" : "";

  if (fileCount === 0) return null;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
          Files ({fileCount})
        </div>
        <button
          onClick={() => downloadZip(backendFiles)}
          className="flex items-center gap-1 px-2 py-1 text-[10px] font-medium text-white bg-blue-500 rounded hover:bg-blue-600 transition-colors"
        >
          <LuDownload className="w-3 h-3" />
          Download All
        </button>
      </div>

      {/* File tree */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div className="max-h-40 overflow-y-auto bg-gray-50 dark:bg-zinc-900 py-1">
          {tree.map((node) => (
            <TreeItem
              key={node.path}
              node={node}
              depth={0}
              selectedFile={selectedFile}
              onSelect={setSelectedFile}
            />
          ))}
        </div>

        {/* Code viewer */}
        {selectedFile && (
          <div className="border-t border-gray-200 dark:border-gray-700">
            <div className="px-2 py-1 bg-gray-100 dark:bg-zinc-800 text-[10px] text-gray-500 dark:text-gray-400 font-mono">
              {selectedFile}
            </div>
            <pre className="p-2 text-[11px] leading-relaxed font-mono text-gray-700 dark:text-gray-300 bg-white dark:bg-zinc-950 max-h-64 overflow-auto whitespace-pre-wrap break-all">
              {currentCode}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
