"use client";

import { BugPlay, Loader2, Upload, X } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { CodeEditor } from "../components/CodeEditor";
import { ErrorBanner } from "../components/ErrorBanner";
import { OptimizationView } from "../components/OptimizationView";
import { ParseTreeGraph } from "../components/ParseTreeGraph";
import { PhaseTabs } from "../components/PhaseTabs";
import { PlaybackControls } from "../components/PlaybackControls";
import { SymbolTablePanel } from "../components/SymbolTablePanel";
import { TACView } from "../components/TACView";
import { TokenStream } from "../components/TokenStream";
import { compileFull, compileUpload } from "../lib/api";
import { samplePrograms, usePipelineStore } from "../store/pipelineStore";

export default function Home() {
  const {
    source,
    result,
    currentPhase,
    currentStepIndex,
    selectedAstNodeId,
    uploadedFile,
    diagnostics,
    setSource,
    setResult,
    setPhase,
    setSelectedAstNodeId,
    setUploadedFile
  } = usePipelineStore();
  const [isCompiling, setIsCompiling] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const activePhase = result?.[currentPhase] ?? null;
  const highlightRange = activePhase?.steps[currentStepIndex]?.highlightRange ?? null;
  const stepCount = activePhase?.steps.length ?? 0;

  const phasePanel = useMemo(() => {
    if (currentPhase === "lex") return <TokenStream data={result?.lex.data ?? null} currentStepIndex={currentStepIndex} />;
    if (currentPhase === "parse") {
      return (
        <ParseTreeGraph
          ast={result?.parse.data?.ast ?? null}
          steps={result?.parse.steps ?? []}
          currentStepIndex={currentStepIndex}
          selectedAstNodeId={selectedAstNodeId}
          onSelect={setSelectedAstNodeId}
        />
      );
    }
    if (currentPhase === "semantic") return <SymbolTablePanel data={result?.semantic.data ?? null} />;
    if (currentPhase === "tac") {
      return <TACView data={result?.tac.data ?? null} selectedAstNodeId={selectedAstNodeId} onSelectAst={setSelectedAstNodeId} />;
    }
    return <OptimizationView data={result?.optimize.data ?? null} original={result?.tac.data ?? null} />;
  }, [currentPhase, currentStepIndex, result, selectedAstNodeId, setSelectedAstNodeId]);

  async function handleCompile() {
    setIsCompiling(true);
    setRequestError(null);
    try {
      const compiled = await compileFull(source);
      setResult(compiled);
      console.log(compiled);
    } catch (error) {
      setRequestError(error instanceof Error ? error.message : "Compile request failed");
    } finally {
      setIsCompiling(false);
    }
  }

  async function handleFile(file: File) {
    setRequestError(null);
    if (!/\.(c|h)$/i.test(file.name)) {
      setRequestError("Upload a .c or .h file.");
      return;
    }
    if (file.size > 256 * 1024) {
      setRequestError("File is larger than the 256 KB limit.");
      return;
    }
    setIsCompiling(true);
    try {
      const compiled = await compileUpload(file);
      setUploadedFile({ name: file.name, size: file.size });
      setSource(compiled.source ?? source);
      setResult(compiled);
    } catch (error) {
      setRequestError(error instanceof Error ? error.message : "Upload request failed");
    } finally {
      setIsCompiling(false);
    }
  }

  return (
    <main className="flex h-screen min-h-[720px] flex-col bg-background text-ink">
      <header className="flex h-20 items-center gap-4 border-b-2 border-primary bg-background px-6">
        <div className="flex min-w-0 items-center gap-3">
          <BugPlay className="h-6 w-6 text-secondary" />
          <div>
            <div className="font-display text-subhead uppercase">Compiler Visualizer</div>
            <div className="text-overline uppercase text-muted">Pipeline desk</div>
          </div>
        </div>
        <select
          aria-label="Sample program"
          className="ml-auto h-11 border-2 border-border-medium bg-background px-3 text-sm uppercase tracking-[0.06em] text-ink focus:border-primary"
          onChange={(event) => setSource(samplePrograms[event.target.value as keyof typeof samplePrograms])}
          defaultValue="Simple expression"
        >
          {Object.keys(samplePrograms).map((name) => (
            <option key={name}>{name}</option>
          ))}
        </select>
        {uploadedFile ? (
          <span className="inline-flex h-11 items-center gap-2 border-2 border-primary bg-background px-3 text-overline uppercase text-ink">
            {uploadedFile.name}
            <button
              aria-label="Clear uploaded file"
              className="p-0.5 hover:text-secondary"
              onClick={() => setUploadedFile(null)}
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </span>
        ) : null}
        <input
          ref={fileInputRef}
          className="hidden"
          type="file"
          accept=".c,.h"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void handleFile(file);
            event.currentTarget.value = "";
          }}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          className="inline-flex h-11 items-center gap-2 border-2 border-primary bg-background px-5 text-sm font-bold uppercase tracking-[0.06em] text-primary hover:bg-primary hover:text-tertiary"
        >
          <Upload className="h-4 w-4" />
          Upload .c
        </button>
        <button
          onClick={handleCompile}
          disabled={isCompiling}
          className="inline-flex h-11 items-center gap-2 border-2 border-primary bg-primary px-6 text-sm font-bold uppercase tracking-[0.06em] text-tertiary hover:border-secondary hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-35"
        >
          {isCompiling ? <Loader2 className="h-4 w-4 animate-spin" /> : <BugPlay className="h-4 w-4" />}
          Run
        </button>
      </header>

      <ErrorBanner result={result} />
      {requestError ? <div className="border-b-2 border-secondary bg-[var(--vb-error-surface)] px-6 py-3 text-sm font-bold uppercase tracking-[0.04em] text-secondary">{requestError}</div> : null}
      {diagnostics?.length ? (
        <div className="flex max-h-28 flex-wrap gap-2 overflow-auto border-b-2 border-border-subtle bg-surface px-6 py-3 text-caption text-ink">
          {diagnostics.map((diagnostic, index) => (
            <button
              key={`${diagnostic.message}-${index}`}
              className="border-2 border-border-medium bg-background px-3 py-1 text-left hover:border-primary"
              title={`${diagnostic.line}:${diagnostic.column}`}
            >
              <span className="font-bold uppercase text-secondary">{diagnostic.severity}</span> {diagnostic.message}
            </button>
          ))}
        </div>
      ) : null}

      <section className="grid min-h-0 flex-1 grid-cols-[42%_58%] border-b-2 border-primary">
        <div
          className="min-w-0 border-r-2 border-primary bg-background"
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            const file = event.dataTransfer.files?.[0];
            if (file) void handleFile(file);
          }}
        >
          <CodeEditor source={source} onChange={setSource} highlightRange={highlightRange} />
        </div>
        <div className="flex min-w-0 flex-col">
          <div className="flex items-center border-b-2 border-primary bg-background">
            <PhaseTabs result={result} currentPhase={currentPhase} onChange={setPhase} />
            <div className="ml-auto px-6 text-overline uppercase text-muted">
              step {stepCount ? currentStepIndex + 1 : 0} / {stepCount}
            </div>
          </div>
          <div className="min-h-0 flex-1">{phasePanel}</div>
          <PlaybackControls />
        </div>
      </section>
    </main>
  );
}
