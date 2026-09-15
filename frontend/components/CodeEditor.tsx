"use client";

import Editor, { type OnMount } from "@monaco-editor/react";
import type { editor as MonacoEditor, IDisposable, IRange, languages } from "monaco-editor";
import { useEffect, useRef } from "react";

interface CodeEditorProps {
  source: string;
  onChange: (source: string) => void;
  highlightRange: [number, number] | null;
}

export function CodeEditor({ source, onChange, highlightRange }: CodeEditorProps) {
  const editorRef = useRef<MonacoEditor.IStandaloneCodeEditor | null>(null);
  const decorationsRef = useRef<string[]>([]);

  const handleMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    monaco.languages.register({ id: "clike-small" });
    monaco.languages.setMonarchTokensProvider("clike-small", tokenProvider);
  };

  useEffect(() => {
    const editor = editorRef.current;
    const model = editor?.getModel();
    if (!editor || !model) return;

    const decorations =
      highlightRange && highlightRange[0] !== highlightRange[1]
        ? [
            {
              range: offsetRangeToMonaco(model, highlightRange),
              options: { inlineClassName: "source-highlight" }
            }
          ]
        : [];

    decorationsRef.current = editor.deltaDecorations(decorationsRef.current, decorations);
  }, [highlightRange, source]);

  return (
    <Editor
      height="100%"
      language="clike-small"
      theme="vs-light"
      value={source}
      onChange={(value) => onChange(value ?? "")}
      onMount={handleMount}
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbersMinChars: 3,
        scrollBeyondLastLine: false,
        roundedSelection: false,
        automaticLayout: true,
        tabSize: 2
      }}
    />
  );
}

function offsetRangeToMonaco(model: MonacoEditor.ITextModel, range: [number, number]): IRange {
  const start = model.getPositionAt(range[0]);
  const end = model.getPositionAt(range[1]);
  return { startLineNumber: start.lineNumber, startColumn: start.column, endLineNumber: end.lineNumber, endColumn: end.column };
}

const tokenProvider: languages.IMonarchLanguage = {
  keywords: ["int", "float", "bool", "void", "if", "else", "while", "return"],
  tokenizer: {
    root: [
      [/[a-zA-Z_]\w*/, { cases: { "@keywords": "keyword", "true|false": "number", "@default": "identifier" } }],
      [/\d+\.\d+/, "number.float"],
      [/\d+/, "number"],
      [/[{}()[\];,]/, "delimiter"],
      [/[+\-*/%=!<>|&]+/, "operator"]
    ]
  }
};
