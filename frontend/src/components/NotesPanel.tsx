import type { Translator } from "../i18n";
import type { BrewPlan } from "../types";

interface NotesPanelProps {
  tr: Translator;
  brewPlan: BrewPlan | null;
}

export function NotesPanel({ tr, brewPlan }: NotesPanelProps) {
  return (
    <section className="panel">
      <h2>{tr("notes")}</h2>
      {brewPlan?.notes.length ? (
        <ul className="list">
          {brewPlan.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      ) : (
        <p>-</p>
      )}
    </section>
  );
}
