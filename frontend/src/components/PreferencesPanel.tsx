import { FormEvent } from "react";

import type { Translator } from "../i18n";
import type { Language, TemperatureUnit, UnitSystem } from "../types";

interface PreferencesPanelProps {
  loading: boolean;
  tr: Translator;
  unitSystem: UnitSystem;
  temperatureUnit: TemperatureUnit;
  language: Language;
  onUnitSystemChange: (value: UnitSystem) => void;
  onTemperatureUnitChange: (value: TemperatureUnit) => void;
  onLanguageChange: (value: Language) => void;
  onSave: () => Promise<void>;
}

export function PreferencesPanel({
  loading,
  tr,
  unitSystem,
  temperatureUnit,
  language,
  onUnitSystemChange,
  onTemperatureUnitChange,
  onLanguageChange,
  onSave,
}: PreferencesPanelProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    void onSave();
  }

  return (
    <section className="panel">
      <h2>{tr("preferences")}</h2>
      <form onSubmit={handleSubmit} className="stack-form">
        <label>
          {tr("unit_system")}
          <select value={unitSystem} onChange={(event) => onUnitSystemChange(event.target.value as UnitSystem)}>
            <option value="metric">metric</option>
            <option value="imperial">imperial</option>
          </select>
        </label>

        <label>
          {tr("temperature_unit")}
          <select
            value={temperatureUnit}
            onChange={(event) => onTemperatureUnitChange(event.target.value as TemperatureUnit)}
          >
            <option value="C">C</option>
            <option value="F">F</option>
          </select>
        </label>

        <label>
          {tr("language")}
          <select value={language} onChange={(event) => onLanguageChange(event.target.value as Language)}>
            <option value="en">en</option>
            <option value="es">es</option>
          </select>
        </label>

        <button className="primary-button" type="submit" disabled={loading}>
          {tr("save_preferences")}
        </button>
      </form>
    </section>
  );
}
