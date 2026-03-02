import type { Translator } from "../i18n";

interface EmptyBrewPlanStateProps {
  tr: Translator;
  onJumpToDataManager: () => void;
}

export function EmptyBrewPlanState({ tr, onJumpToDataManager }: EmptyBrewPlanStateProps) {
  return (
    <div className="empty-state">
      <p>{tr("not_loaded")}</p>
      <p className="inline-note">{tr("empty_plan_hint")}</p>
      <button className="ghost-button" type="button" onClick={onJumpToDataManager}>
        {tr("jump_data_manager")}
      </button>
    </div>
  );
}
