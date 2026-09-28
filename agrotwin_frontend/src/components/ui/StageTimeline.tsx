"use client";
import LocalizedText from "@/components/ui/LocalizedText";

/**
 * Shared crop-stage timeline. Dashboard uses this read-only, driven by the
 * twin's real growthStageRaw/stageSequence. The simulator keeps its own
 * richer 3D-model-paired timeline (GrowthStageTimeline in simulator/page.tsx)
 * since it drives simulate/what-if visuals, not just a read display.
 */
export default function StageTimeline({
  stages,
  currentStage,
  readOnly = true,
  currentLabel = "Current",
}: {
  stages: string[];
  currentStage: string;
  stageProgress?: number;
  readOnly?: boolean;
  currentLabel?: string;
}) {
  const currentIdx = stages.findIndex(
    (s) => s.toLowerCase() === currentStage.toLowerCase()
  );
  const resolvedIdx = currentIdx >= 0 ? currentIdx : Math.max(0, stages.length - 2);

  const items = stages.map((name, i) => ({
    name,
    done: i < resolvedIdx,
    current: i === resolvedIdx,
  }));

  return (
    <LocalizedText><div className="relative" aria-readonly={readOnly}>
      <div className="absolute top-4 left-0 right-0 h-0.5 bg-gray-200" />
      {items.length > 1 && (
        <div
          className="absolute top-4 left-0 h-0.5 bg-green-500"
          style={{ width: `${(resolvedIdx / (items.length - 1)) * 100}%` }}
        />
      )}

      <div
        className="relative grid gap-2"
        style={{ gridTemplateColumns: `repeat(${items.length || 6}, minmax(0, 1fr))` }}
      >
        {items.map((stage, i) => (
          <div key={i} className="flex flex-col items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center z-10 text-sm mb-2
                ${stage.current
                  ? "bg-green-600 border-2 border-green-600 text-white shadow-lg shadow-green-200 ring-4 ring-green-200 animate-pulse"
                  : stage.done
                  ? "bg-white border-2 border-green-500"
                  : "bg-white border-2 border-gray-200"
                }`}
            >
              {stage.done && !stage.current ? (
                <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <span className={`text-base ${stage.current ? "" : "opacity-30"}`}>🌿</span>
              )}
            </div>
            <div
              className={`text-center text-[10px] font-semibold ${
                stage.current ? "text-green-700" : stage.done ? "text-gray-600" : "text-gray-300"
              }`}
            >
              {stage.name}
            </div>
            {stage.current && (
              <span className="mt-1 bg-green-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full whitespace-nowrap">
                {currentLabel}
              </span>
            )}
          </div>
        ))}
      </div>
    </div></LocalizedText>
  );
}
