import type { Translator } from "../i18n";
import type { BrewPlan } from "../types";
import { EmptyBrewPlanState } from "./EmptyBrewPlanState";

interface ShoppingListPanelProps {
  tr: Translator;
  brewPlan: BrewPlan | null;
  onJumpToDataManager: () => void;
}

export function ShoppingListPanel({ tr, brewPlan, onJumpToDataManager }: ShoppingListPanelProps) {
  return (
    <section className="panel">
      <h2>{tr("shopping_list")}</h2>
      {!brewPlan ? <EmptyBrewPlanState tr={tr} onJumpToDataManager={onJumpToDataManager} /> : null}
      {brewPlan?.shopping_list.length ? (
        <ul className="list">
          {brewPlan.shopping_list.map((item) => (
            <li key={`${item.name}-${item.required_unit}`}>
              {item.name} - {tr("missing")} {item.shortage_amount} {item.required_unit}
            </li>
          ))}
        </ul>
      ) : brewPlan ? (
        <p>-</p>
      ) : null}
    </section>
  );
}
