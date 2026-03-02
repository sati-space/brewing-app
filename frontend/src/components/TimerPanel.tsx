import type { Translator } from "../i18n";
import type { BrewPlan } from "../types";
import { EmptyBrewPlanState } from "./EmptyBrewPlanState";

export interface TimerState {
  stepIndex: number;
  running: boolean;
  remainingSeconds: number;
}

interface TimerPanelProps {
  tr: Translator;
  brewPlan: BrewPlan | null;
  timer: TimerState;
  onStartPause: () => void;
  onNextStep: () => void;
  onReset: () => void;
  onJumpToDataManager: () => void;
}

export function TimerPanel({
  tr,
  brewPlan,
  timer,
  onStartPause,
  onNextStep,
  onReset,
  onJumpToDataManager,
}: TimerPanelProps) {
  const activeStep = brewPlan?.timer_plan[timer.stepIndex] ?? null;

  return (
    <section className="panel span-two">
      <h2>{tr("timer")}</h2>
      {brewPlan && activeStep ? (
        <>
          <p className="timer-title">
            {tr("step")} {timer.stepIndex + 1} {tr("of")} {brewPlan.timer_plan.length}: {activeStep.name}
          </p>
          <p className="timer-readout">{formatTimer(timer.remainingSeconds)}</p>
          <div className="button-row">
            <button className="primary-button" onClick={onStartPause}>
              {timer.running ? tr("pause") : tr("start")}
            </button>
            <button className="ghost-button" onClick={onNextStep}>
              {tr("next_step")}
            </button>
            <button className="ghost-button" onClick={onReset}>
              {tr("reset")}
            </button>
          </div>
        </>
      ) : (
        <EmptyBrewPlanState tr={tr} onJumpToDataManager={onJumpToDataManager} />
      )}
    </section>
  );
}

function formatTimer(totalSeconds: number): string {
  const safeSeconds = Math.max(0, totalSeconds);
  const minutes = Math.floor(safeSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = Math.floor(safeSeconds % 60)
    .toString()
    .padStart(2, "0");
  return `${minutes}:${seconds}`;
}
