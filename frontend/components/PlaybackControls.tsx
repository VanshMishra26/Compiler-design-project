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
    <div className="flex items-center gap-2 border-t-2 border-primary bg-background px-4 py-3">
      <button title="Reset" onClick={() => setStep(0)} className="grid h-10 w-10 place-items-center border-2 border-primary bg-background hover:bg-primary hover:text-tertiary">
        <RotateCcw className="h-4 w-4" />
      </button>
      <button title="Step back" onClick={() => stepBy(-1)} className="grid h-10 w-10 place-items-center border-2 border-primary bg-background hover:bg-primary hover:text-tertiary">
        <SkipBack className="h-4 w-4" />
      </button>
      <button title={isPlaying ? "Pause" : "Play"} onClick={() => setPlaying(!isPlaying)} className="grid h-10 w-10 place-items-center border-2 border-primary bg-primary text-tertiary hover:border-secondary hover:bg-secondary">
        {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
      </button>
      <button title="Step forward" onClick={() => stepBy(1)} className="grid h-10 w-10 place-items-center border-2 border-primary bg-background hover:bg-primary hover:text-tertiary">
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
        className="ml-4 w-36 accent-secondary"
      />
      <span className="text-overline uppercase text-muted">{playbackSpeedMs}ms</span>
    </div>
  );
}
