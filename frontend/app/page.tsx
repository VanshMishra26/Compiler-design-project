"use client";

import { BugPlay, Loader2 } from "lucide-react";
import { useMemo, useState } from "react";
import { CodeEditor } from "../components/CodeEditor";
import { ErrorBanner } from "../components/ErrorBanner";
import { OptimizationView } from "../components/OptimizationView";
import { ParseTreeGraph } from "../components/ParseTreeGraph";
import { PhaseTabs } from "../components/PhaseTabs";
import { PlaybackControls } from "../components/PlaybackControls";
import { SymbolTablePanel } from "../components/SymbolTablePanel";
import { TACView } from "../components/TACView";
import { TokenStream } from "../components/TokenStream";
import { compileFull } from "../lib/api";
import { samplePrograms, usePipelineStore } from "../store/pipelineStore";

export default function Home() {
  const {
    source,
    result,
    currentPhase,
    currentStepIndex,
    selectedAstNodeId,
    setSource,
    setResult,
    setPhase,
    setSelectedAstNodeId
  } = usePipelineStore();
  const [isCompiling, setIsCompiling] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);

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

  return (
    <main className="flex h-screen min-h-[720px] flex-col bg-paper text-ink">
      <header className="flex h-14 items-center gap-3 border-b border-ink/10 bg-white px-4">
        <div className="flex items-center gap-2 font-semibold">
          <BugPlay className="h-5 w-5 text-coral" />
          Compiler Visualizer
        </div>
        <select
          className="ml-auto h-9 rounded border border-ink/15 bg-white px-3 text-sm"
          onChange={(event) => setSource(samplePrograms[event.target.value as keyof typeof samplePrograms])}
          defaultValue="Simple expression"
        >
          {Object.keys(samplePrograms).map((name) => (
            <option key={name}>{name}</option>
          ))}
        </select>
        <button
          onClick={handleCompile}
          disabled={isCompiling}
          className="inline-flex h-9 items-center gap-2 rounded bg-coral px-4 text-sm font-semibold text-white hover:bg-coral/90 disabled:opacity-60"
        >
          {isCompiling ? <Loader2 className="h-4 w-4 animate-spin" /> : <BugPlay className="h-4 w-4" />}
          Compile
        </button>
      </header>

      <ErrorBanner result={result} />
      {requestError ? <div className="border-b border-coral/30 bg-coral/10 px-4 py-2 text-sm text-coral">{requestError}</div> : null}

      <section className="grid min-h-0 flex-1 grid-cols-[40%_60%]">
        <div className="min-w-0 border-r border-ink/10 bg-white">
          <CodeEditor source={source} onChange={setSource} highlightRange={highlightRange} />
        </div>
        <div className="flex min-w-0 flex-col">
          <div className="flex items-center border-b border-ink/10 bg-white">
            <PhaseTabs result={result} currentPhase={currentPhase} onChange={setPhase} />
            <div className="ml-auto px-4 text-xs text-ink/55">
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
