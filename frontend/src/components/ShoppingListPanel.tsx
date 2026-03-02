import type { Translator } from "../i18n";
import type { BrewPlan } from "../types";

interface ShoppingListPanelProps {
  tr: Translator;
  brewPlan: BrewPlan | null;
}

export function ShoppingListPanel({ tr, brewPlan }: ShoppingListPanelProps) {
  return (
    <section className="panel">
      <h2>{tr("shopping_list")}</h2>
      {brewPlan?.shopping_list.length ? (
        <ul className="list">
          {brewPlan.shopping_list.map((item) => (
            <li key={`${item.name}-${item.required_unit}`}>
              {item.name} - {tr("missing")} {item.shortage_amount} {item.required_unit}
            </li>
          ))}
        </ul>
      ) : (
        <p>-</p>
      )}
    </section>
  );
}
