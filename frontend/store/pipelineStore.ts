import { create } from "zustand";
import type { FullPipelineResponse, PhaseName } from "../lib/types";

export const samplePrograms = {
  "Simple expression": "void main() {\n  int x = 2 + 3 * 4;\n  return;\n}\n",
  "If / else": "void main() {\n  int x = 0;\n  if (x == 0) x = 1; else x = 2;\n}\n",
  "While loop": "void main() {\n  int x = 0;\n  while (x < 3) {\n    x = x + 1;\n  }\n}\n",
  "Linked list": "#include <stdlib.h>\nstruct Node { int value; struct Node *next; };\nvoid push(struct Node *head, int value) {\n  struct Node *node = malloc(sizeof(struct Node));\n  node->value = value;\n  node->next = head->next;\n  head->next = node;\n}\n",
  "BST": "struct Node { int value; struct Node *left; struct Node *right; };\nint search(struct Node *node, int value) {\n  while (node != NULL) {\n    if (value == node->value) return 1;\n    if (value < node->value) node = node->left; else node = node->right;\n  }\n  return 0;\n}\n",
  "Hash table": "#define SIZE 16\nstruct Entry { int key; int value; struct Entry *next; };\nstruct Entry *table[SIZE];\nint hash(int key) { return key % SIZE; }\n",
  "Matrix multiply": "void multiply(int a[2][2], int b[2][2], int c[2][2]) {\n  for (int i = 0; i < 2; i = i + 1) {\n    for (int j = 0; j < 2; j = j + 1) {\n      c[i][j] = a[i][j] * b[i][j];\n    }\n  }\n}\n",
  "Quick sort": "int cmp(int a, int b) { return a - b; }\nvoid sort(int *items, int count, int (*compare)(int, int)) {\n  int pivot = items[count / 2];\n}\n",
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
  uploadedFile: { name: string; size: number } | null;
  selectedFunction: string | null;
  diagnostics: FullPipelineResponse["diagnostics"];
  activeSourceRange: [number, number] | null;
  astCollapsed: Record<string, boolean>;
  filters: Record<string, string>;
  showOptimized: boolean;
  setSource: (source: string) => void;
  setResult: (result: FullPipelineResponse | null) => void;
  setPhase: (phase: PhaseName) => void;
  setStep: (step: number) => void;
  stepBy: (delta: number) => void;
  setPlaying: (isPlaying: boolean) => void;
  setSpeed: (speed: number) => void;
  setSelectedAstNodeId: (id: string | null) => void;
  setUploadedFile: (file: { name: string; size: number } | null) => void;
  setSelectedFunction: (name: string | null) => void;
  setActiveSourceRange: (range: [number, number] | null) => void;
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
  uploadedFile: null,
  selectedFunction: null,
  diagnostics: [],
  activeSourceRange: null,
  astCollapsed: {},
  filters: {},
  showOptimized: true,
  setSource: (source) => set({ source }),
  setResult: (result) => set({ result, currentStepIndex: 0, selectedAstNodeId: null, diagnostics: result?.diagnostics ?? [], selectedFunction: result?.functions?.[0]?.name ?? null }),
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
  setUploadedFile: (uploadedFile) => set({ uploadedFile }),
  setSelectedFunction: (selectedFunction) => set({ selectedFunction }),
  setActiveSourceRange: (activeSourceRange) => set({ activeSourceRange }),
  setShowOptimized: (showOptimized) => set({ showOptimized })
}));
