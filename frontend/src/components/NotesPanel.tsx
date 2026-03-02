import type { Translator } from "../i18n";
import type { BrewPlan } from "../types";
import { EmptyBrewPlanState } from "./EmptyBrewPlanState";

interface NotesPanelProps {
  tr: Translator;
  brewPlan: BrewPlan | null;
  onJumpToDataManager: () => void;
}

export function NotesPanel({ tr, brewPlan, onJumpToDataManager }: NotesPanelProps) {
  return (
    <section className="panel">
      <h2>{tr("notes")}</h2>
      {!brewPlan ? <EmptyBrewPlanState tr={tr} onJumpToDataManager={onJumpToDataManager} /> : null}
      {brewPlan?.notes.length ? (
        <ul className="list">
          {brewPlan.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      ) : brewPlan ? (
        <p>-</p>
      ) : null}
    </section>
  );
}
