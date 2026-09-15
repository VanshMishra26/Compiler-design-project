"use client";

import { Pause, Play, RotateCcw, SkipBack, SkipForward } from "lucide-react";
import { useEffect } from "react";
import { usePipelineStore } from "../store/pipelineStore";

export function PlaybackControls() {
  const { isPlaying, playbackSpeedMs, setPlaying, stepBy, setStep, setSpeed } = usePipelineStore();

  useEffect(() => {
    if (!isPlaying) return;
    const timer = window.setInterval(() => stepBy(1), playbackSpeedMs);
    return () => window.clearInterval(timer);
  }, [isPlaying, playbackSpeedMs, stepBy]);

  return (
    <div className="flex items-center gap-2 border-t border-ink/10 bg-white px-3 py-2">
      <button title="Reset" onClick={() => setStep(0)} className="grid h-9 w-9 place-items-center rounded border border-ink/15 hover:bg-paper">
        <RotateCcw className="h-4 w-4" />
      </button>
      <button title="Step back" onClick={() => stepBy(-1)} className="grid h-9 w-9 place-items-center rounded border border-ink/15 hover:bg-paper">
        <SkipBack className="h-4 w-4" />
      </button>
      <button title={isPlaying ? "Pause" : "Play"} onClick={() => setPlaying(!isPlaying)} className="grid h-9 w-9 place-items-center rounded bg-ink text-white hover:bg-ink/90">
        {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
      </button>
      <button title="Step forward" onClick={() => stepBy(1)} className="grid h-9 w-9 place-items-center rounded border border-ink/15 hover:bg-paper">
        <SkipForward className="h-4 w-4" />
      </button>
      <input
        aria-label="Playback speed"
        type="range"
        min="200"
        max="1600"
        step="100"
        value={playbackSpeedMs}
        onChange={(event) => setSpeed(Number(event.target.value))}
        className="ml-3 w-36 accent-coral"
      />
      <span className="text-xs text-ink/60">{playbackSpeedMs}ms</span>
    </div>
  );
}
