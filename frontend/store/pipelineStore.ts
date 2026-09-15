import { create } from "zustand";
import type { FullPipelineResponse, PhaseName } from "../lib/types";

export const samplePrograms = {
  "Simple expression": "void main() {\n  int x = 2 + 3 * 4;\n  return;\n}\n",
  "If / else": "void main() {\n  int x = 0;\n  if (x == 0) x = 1; else x = 2;\n}\n",
  "While loop": "void main() {\n  int x = 0;\n  while (x < 3) {\n    x = x + 1;\n  }\n}\n",
  "Type error": "void main() {\n  int x = true;\n}\n"
};

interface PipelineState {
  source: string;
  result: FullPipelineResponse | null;
  currentPhase: PhaseName;
  currentStepIndex: number;
  isPlaying: boolean;
  playbackSpeedMs: number;
  selectedAstNodeId: string | null;
  showOptimized: boolean;
  setSource: (source: string) => void;
  setResult: (result: FullPipelineResponse | null) => void;
  setPhase: (phase: PhaseName) => void;
  setStep: (step: number) => void;
  stepBy: (delta: number) => void;
  setPlaying: (isPlaying: boolean) => void;
  setSpeed: (speed: number) => void;
  setSelectedAstNodeId: (id: string | null) => void;
  setShowOptimized: (value: boolean) => void;
}

export const usePipelineStore = create<PipelineState>((set, get) => ({
  source: samplePrograms["Simple expression"],
  result: null,
  currentPhase: "lex",
  currentStepIndex: 0,
  isPlaying: false,
  playbackSpeedMs: 700,
  selectedAstNodeId: null,
  showOptimized: true,
  setSource: (source) => set({ source }),
  setResult: (result) => set({ result, currentStepIndex: 0, selectedAstNodeId: null }),
  setPhase: (currentPhase) => set({ currentPhase, currentStepIndex: 0 }),
  setStep: (currentStepIndex) => set({ currentStepIndex: Math.max(0, currentStepIndex) }),
  stepBy: (delta) => {
    const { result, currentPhase, currentStepIndex } = get();
    const max = result?.[currentPhase]?.steps.length ?? 0;
    set({ currentStepIndex: Math.min(Math.max(currentStepIndex + delta, 0), Math.max(max - 1, 0)) });
  },
  setPlaying: (isPlaying) => set({ isPlaying }),
  setSpeed: (playbackSpeedMs) => set({ playbackSpeedMs }),
  setSelectedAstNodeId: (selectedAstNodeId) => set({ selectedAstNodeId }),
  setShowOptimized: (showOptimized) => set({ showOptimized })
}));
