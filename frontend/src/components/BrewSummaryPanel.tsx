import type { Translator } from "../i18n";
import type { BrewPlan } from "../types";
import { DataRow } from "./DataRow";
import { EmptyBrewPlanState } from "./EmptyBrewPlanState";

interface BrewSummaryPanelProps {
  tr: Translator;
  brewPlan: BrewPlan | null;
  onJumpToDataManager: () => void;
}

export function BrewSummaryPanel({ tr, brewPlan, onJumpToDataManager }: BrewSummaryPanelProps) {
  return (
    <section className="panel span-two">
      <h2>{tr("summary")}</h2>
      {brewPlan ? (
        <div className="summary-grid">
          <DataRow label={tr("grain_bill")} value={brewPlan.display.grain_bill} unit={brewPlan.display_units.grain_unit} />
          <DataRow label={tr("mash_water")} value={brewPlan.display.mash_water} unit={brewPlan.display_units.volume_unit} />
          <DataRow
            label={tr("sparge_water")}
            value={brewPlan.display.sparge_water}
            unit={brewPlan.display_units.volume_unit}
          />
          <DataRow label={tr("total_water")} value={brewPlan.display.total_water} unit={brewPlan.display_units.volume_unit} />
          <DataRow
            label={tr("pre_boil")}
            value={brewPlan.display.pre_boil_volume}
            unit={brewPlan.display_units.volume_unit}
          />
          <DataRow
            label={tr("post_boil")}
            value={brewPlan.display.post_boil_volume}
            unit={brewPlan.display_units.volume_unit}
          />
          <DataRow label={tr("boil_off")} value={brewPlan.display.boil_off} unit={brewPlan.display_units.volume_unit} />
          <DataRow
            label={tr("mash_target_temp")}
            value={brewPlan.display.mash_target_temp}
            unit={brewPlan.display_units.temperature_unit}
          />
          <DataRow
            label={tr("strike_temp")}
            value={brewPlan.display.strike_water_temp}
            unit={brewPlan.display_units.temperature_unit}
          />
        </div>
      ) : (
        <EmptyBrewPlanState tr={tr} onJumpToDataManager={onJumpToDataManager} />
      )}
    </section>
  );
}
