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
    const colors = voiceboxColors();
    monaco.languages.register({ id: "clike-small" });
    monaco.languages.setMonarchTokensProvider("clike-small", tokenProvider);
    monaco.editor.defineTheme("voicebox", {
      base: "vs",
      inherit: true,
      rules: [
        { token: "keyword", foreground: colors.primary, fontStyle: "bold" },
        { token: "identifier", foreground: colors.primary },
        { token: "number", foreground: colors.secondary },
        { token: "string", foreground: colors.muted },
        { token: "comment", foreground: colors.faint, fontStyle: "italic" },
        { token: "operator", foreground: colors.primary, fontStyle: "bold" }
      ],
      colors: {
        "editor.background": colors.background,
        "editor.foreground": colors.primary,
        "editorLineNumber.foreground": colors.faint,
        "editorLineNumber.activeForeground": colors.primary,
        "editor.selectionBackground": colors.raised,
        "editor.lineHighlightBackground": colors.surface,
        "editorCursor.foreground": colors.secondary,
        "editorWhitespace.foreground": colors.borderMedium
      }
    });
    monaco.editor.setTheme("voicebox");
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
      theme="voicebox"
      value={source}
      onChange={(value) => onChange(value ?? "")}
      onMount={handleMount}
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        fontFamily: "Space Mono, Courier New, Consolas, monospace",
        lineHeight: 22,
        lineNumbersMinChars: 3,
        scrollBeyondLastLine: false,
        roundedSelection: false,
        automaticLayout: true,
        tabSize: 2,
        renderLineHighlight: "line",
        overviewRulerBorder: false
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
  keywords: ["auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else", "enum", "extern", "float", "for", "goto", "if", "inline", "int", "long", "register", "restrict", "return", "short", "signed", "sizeof", "static", "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while", "bool"],
  tokenizer: {
    root: [
      [/[a-zA-Z_]\w*/, { cases: { "@keywords": "keyword", "true|false": "number", "@default": "identifier" } }],
      [/\/\/.*$/, "comment"],
      [/\/\*/, "comment", "@comment"],
      [/"([^"\\]|\\.)*$/, "string.invalid"],
      [/"/, "string", "@string"],
      [/\d+\.\d+/, "number.float"],
      [/\d+/, "number"],
      [/[{}()[\];,]/, "delimiter"],
      [/[+\-*/%=!<>|&]+/, "operator"]
    ],
    comment: [
      [/[^/*]+/, "comment"],
      [/\*\//, "comment", "@pop"],
      [/[/*]/, "comment"]
    ],
    string: [
      [/[^\\"]+/, "string"],
      [/\\./, "string.escape"],
      [/"/, "string", "@pop"]
    ]
  }
};

function voiceboxColors() {
  const styles = getComputedStyle(document.documentElement);
  const read = (name: string) => styles.getPropertyValue(name).trim().replace("#", "");
  return {
    primary: read("--vb-primary"),
    secondary: read("--vb-secondary"),
    background: read("--vb-background"),
    surface: read("--vb-surface"),
    raised: read("--vb-surface-raised"),
    muted: read("--vb-text-secondary"),
    faint: read("--vb-text-tertiary"),
    borderMedium: read("--vb-border-medium")
  };
}
