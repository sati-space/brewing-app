import type { Translator } from "../i18n";

interface OnboardingPanelProps {
  tr: Translator;
  onJumpToDataManager: () => void;
}

export function OnboardingPanel({ tr, onJumpToDataManager }: OnboardingPanelProps) {
  return (
    <section className="panel onboarding-panel span-full">
      <h2>{tr("getting_started_title")}</h2>
      <p className="inline-note">{tr("getting_started_intro")}</p>
      <ol className="onboarding-list">
        <li>{tr("getting_started_step_1")}</li>
        <li>{tr("getting_started_step_2")}</li>
        <li>{tr("getting_started_step_3")}</li>
      </ol>
      <div className="button-row">
        <button className="primary-button" type="button" onClick={onJumpToDataManager}>
          {tr("jump_data_manager")}
        </button>
        <a className="ghost-link" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
          {tr("open_api_docs")}
        </a>
      </div>
    </section>
  );
}
