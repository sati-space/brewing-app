import type { Translator } from "../i18n";
import type {
  Batch,
  BrewPlanApplyResult,
  EquipmentProfile,
  Language,
  TemperatureUnit,
  UnitSystem,
  WaterProfile,
} from "../types";

interface BrewPlannerPanelProps {
  loading: boolean;
  tr: Translator;
  batches: Batch[];
  equipmentProfiles: EquipmentProfile[];
  waterProfiles: WaterProfile[];
  selectedBatchId: number | null;
  selectedEquipmentId: number | null;
  selectedWaterProfileId: number | null;
  overrideUnitSystem: "" | UnitSystem;
  overrideTemperatureUnit: "" | TemperatureUnit;
  overrideLanguage: "" | Language;
  applyResult: BrewPlanApplyResult | null;
  hasMinimumSetup: boolean;
  onSelectedBatchChange: (value: number | null) => void;
  onSelectedEquipmentChange: (value: number | null) => void;
  onSelectedWaterProfileChange: (value: number | null) => void;
  onOverrideUnitSystemChange: (value: "" | UnitSystem) => void;
  onOverrideTemperatureUnitChange: (value: "" | TemperatureUnit) => void;
  onOverrideLanguageChange: (value: "" | Language) => void;
  onGeneratePlan: () => Promise<void>;
  onApplyTimeline: () => Promise<void>;
  onJumpToDataManager: () => void;
}

export function BrewPlannerPanel({
  loading,
  tr,
  batches,
  equipmentProfiles,
  waterProfiles,
  selectedBatchId,
  selectedEquipmentId,
  selectedWaterProfileId,
  overrideUnitSystem,
  overrideTemperatureUnit,
  overrideLanguage,
  applyResult,
  hasMinimumSetup,
  onSelectedBatchChange,
  onSelectedEquipmentChange,
  onSelectedWaterProfileChange,
  onOverrideUnitSystemChange,
  onOverrideTemperatureUnitChange,
  onOverrideLanguageChange,
  onGeneratePlan,
  onApplyTimeline,
  onJumpToDataManager,
}: BrewPlannerPanelProps) {
  return (
    <section className="panel planner-panel">
      <h2>{tr("dashboard")}</h2>
      <div className="stack-form">
        <label>
          {tr("select_batch")}
          <select
            value={selectedBatchId ?? ""}
            onChange={(event) => onSelectedBatchChange(event.target.value ? Number(event.target.value) : null)}
          >
            <option value="">{tr("default_value")}</option>
            {batches.map((batch) => (
              <option key={batch.id} value={batch.id}>
                #{batch.id} - {batch.name} ({batch.status})
              </option>
            ))}
          </select>
        </label>

        <label>
          {tr("equipment_profile")}
          <select
            value={selectedEquipmentId ?? ""}
            onChange={(event) => onSelectedEquipmentChange(event.target.value ? Number(event.target.value) : null)}
          >
            <option value="">{tr("default_value")}</option>
            {equipmentProfiles.map((equipment) => (
              <option key={equipment.id} value={equipment.id}>
                #{equipment.id} - {equipment.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          {tr("water_profile")}
          <select
            value={selectedWaterProfileId ?? ""}
            onChange={(event) => onSelectedWaterProfileChange(event.target.value ? Number(event.target.value) : null)}
          >
            <option value="">{tr("default_value")}</option>
            {waterProfiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                #{profile.id} - {profile.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <h3>{tr("overrides")}</h3>
      <div className="override-grid planner-override-grid">
        <label>
          {tr("unit_system")}
          <select
            value={overrideUnitSystem}
            onChange={(event) => onOverrideUnitSystemChange((event.target.value as UnitSystem | "") || "")}
          >
            <option value="">{tr("default_value")}</option>
            <option value="metric">metric</option>
            <option value="imperial">imperial</option>
          </select>
        </label>

        <label>
          {tr("temperature_unit")}
          <select
            value={overrideTemperatureUnit}
            onChange={(event) => onOverrideTemperatureUnitChange((event.target.value as TemperatureUnit | "") || "")}
          >
            <option value="">{tr("default_value")}</option>
            <option value="C">C</option>
            <option value="F">F</option>
          </select>
        </label>

        <label className="override-label-full">
          {tr("language")}
          <select
            value={overrideLanguage}
            onChange={(event) => onOverrideLanguageChange((event.target.value as Language | "") || "")}
          >
            <option value="">{tr("default_value")}</option>
            <option value="en">en</option>
            <option value="es">es</option>
          </select>
        </label>
      </div>

      <div className="button-row">
        <button className="primary-button" onClick={() => void onGeneratePlan()} disabled={loading || !selectedBatchId}>
          {tr("generate_plan")}
        </button>
        <button className="ghost-button" onClick={() => void onApplyTimeline()} disabled={loading || !selectedBatchId}>
          {tr("apply_timeline")}
        </button>
      </div>

      {!hasMinimumSetup ? (
        <div className="inline-note with-action">
          <span>{tr("empty_plan_hint")}</span>
          <button className="ghost-button" type="button" onClick={onJumpToDataManager}>
            {tr("jump_data_manager")}
          </button>
        </div>
      ) : null}

      {applyResult ? (
        <p className="inline-note">
          created: {applyResult.created_step_count}, deleted: {applyResult.deleted_step_count}, preserved: {" "}
          {applyResult.preserved_step_count}
        </p>
      ) : null}
    </section>
  );
}
