"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";

export interface TimelineStage {
  id: string;
  label: string;
  dayStart: number;
  dayEnd: number;
}

interface SimulationTimelineProps {
  stages: TimelineStage[];
  currentStageIndex: number;
  currentDay: number;
  totalDuration: number;
  onSeek?: (day: number) => void;
  readOnly?: boolean;
  label?: string;
}

export default function SimulationTimeline({
  stages,
  currentStageIndex,
  currentDay,
  totalDuration,
  onSeek,
  readOnly = false,
  label = "Growth Stage Timeline",
}: SimulationTimelineProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [localDay, setLocalDay] = useState(currentDay);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    setLocalDay(currentDay);
  }, [currentDay]);

  useEffect(() => {
    if (isPlaying) {
      intervalRef.current = setInterval(() => {
        setLocalDay((prev) => {
          const next = prev + 1;
          if (next >= totalDuration) {
            setIsPlaying(false);
            return totalDuration;
          }
          return next;
        });
      }, 100);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying, totalDuration]);

  useEffect(() => {
    if (!readOnly && onSeek && isPlaying) {
      onSeek(localDay);
    }
  }, [localDay, isPlaying, onSeek, readOnly]);

  const getStageIndexForDay = useCallback(
    (day: number): number => {
      for (let i = stages.length - 1; i >= 0; i--) {
        if (day >= stages[i].dayStart) return i;
      }
      return 0;
    },
    [stages]
  );

  const activeStageIndex = getStageIndexForDay(localDay);
  const progress = totalDuration > 0 ? (localDay / totalDuration) * 100 : 0;

  const handleReset = () => {
    setIsPlaying(false);
    setLocalDay(0);
    onSeek?.(0);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-ink-secondary">
          {label}
        </span>
        {!readOnly && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="btn-secondary text-xs py-1 px-3"
              aria-label={isPlaying ? "Pause" : "Play"}
            >
              {isPlaying ? "Pause" : "Play"}
            </button>
            <button
              onClick={handleReset}
              className="btn-secondary text-xs py-1 px-3"
              aria-label="Reset"
            >
              Reset
            </button>
          </div>
        )}
      </div>

      {/* Progress bar */}
      <div className="relative w-full h-2 bg-zinc-200 rounded-full overflow-hidden">
        <div
          className="absolute left-0 top-0 h-full bg-agri-primary rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Stage nodes */}
      <div className="flex items-center justify-between">
        {stages.map((stage, idx) => {
          const isDone = idx < activeStageIndex;
          const isCurrent = idx === activeStageIndex;
          return (
            <button
              key={stage.id}
              onClick={() => !readOnly && onSeek?.(stage.dayStart)}
              disabled={readOnly}
              className={`flex flex-col items-center gap-1 min-w-0 group ${
                readOnly ? "cursor-default" : "cursor-pointer"
              }`}
              title={`${stage.label} (Day ${stage.dayStart}-${stage.dayEnd})`}
            >
              <div
                className={`w-3 h-3 rounded-full border-2 transition ${
                  isDone
                    ? "bg-agri-primary border-agri-primary"
                    : isCurrent
                    ? "bg-white border-agri-primary"
                    : "bg-white border-zinc-300"
                }`}
              />
              <span
                className={`text-[10px] leading-tight text-center truncate max-w-[80px] ${
                  isCurrent
                    ? "font-semibold text-agri-primary"
                    : "text-ink-muted group-hover:text-ink-secondary"
                }`}
              >
                {stage.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* Day scrubber */}
      {!readOnly && onSeek && (
        <div className="space-y-1">
          <input
            type="range"
            min={0}
            max={totalDuration}
            value={localDay}
            onChange={(e) => {
              const day = parseInt(e.target.value);
              setLocalDay(day);
              onSeek(day);
            }}
            className="w-full h-2 bg-zinc-200 rounded-lg appearance-none cursor-pointer"
            aria-label="Simulation day scrubber"
          />
          <div className="flex justify-between text-[10px] text-ink-muted">
            <span>Day 0</span>
            <span className="font-medium text-ink-secondary">
              Day {localDay} / {totalDuration}
            </span>
            <span>Day {totalDuration}</span>
          </div>
        </div>
      )}

      {/* Reduced motion */}
      <style jsx>{`
        @media (prefers-reduced-motion: reduce) {
          .transition-all {
            transition: none !important;
          }
        }
      `}</style>
    </div>
  );
}
