import { FormEvent, useMemo, useState } from "react";

import type { Translator } from "../i18n";
import type { Batch, FermentationReading, FermentationReadingCreate, FermentationTrend } from "../types";

interface FermentationPanelProps {
  loading: boolean;
  tr: Translator;
  batches: Batch[];
  selectedBatchId: number | null;
  readings: FermentationReading[];
  trend: FermentationTrend | null;
  onSelectedBatchChange: (value: number | null) => void;
  onCreateReading: (payload: FermentationReadingCreate) => Promise<boolean>;
  onRefresh: () => Promise<void>;
  onJumpToDataManager: () => void;
  onClientError: (message: string) => void;
}

export function FermentationPanel({
  loading,
  tr,
  batches,
  selectedBatchId,
  readings,
  trend,
  onSelectedBatchChange,
  onCreateReading,
  onRefresh,
  onJumpToDataManager,
  onClientError,
}: FermentationPanelProps) {
  const [recordedAt, setRecordedAt] = useState("");
  const [gravity, setGravity] = useState("");
  const [tempC, setTempC] = useState("");
  const [ph, setPh] = useState("");
  const [notes, setNotes] = useState("");

  const recentReadings = useMemo(() => [...readings].slice(-8).reverse(), [readings]);

  async function handleCreateReading(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!selectedBatchId) {
      onClientError("Select a batch before logging fermentation readings.");
      return;
    }

    const gravityValue = parseOptionalNumber(gravity);
    const tempValue = parseOptionalNumber(tempC);
    const phValue = parseOptionalNumber(ph);
    const noteValue = notes.trim();

    if (gravityValue !== null && (gravityValue <= 0.99 || gravityValue >= 1.2)) {
      onClientError("Gravity must be between 0.99 and 1.2.");
      return;
    }
    if (tempValue !== null && (tempValue <= -10 || tempValue >= 60)) {
      onClientError("Temperature must be between -10 C and 60 C.");
      return;
    }
    if (phValue !== null && (phValue <= 0 || phValue >= 14)) {
      onClientError("pH must be between 0 and 14.");
      return;
    }
    if (gravityValue === null && tempValue === null && phValue === null && !noteValue) {
      onClientError("Add at least one reading value or note before saving.");
      return;
    }

    let recordedAtIso: string | undefined;
    if (recordedAt.trim()) {
      const parsed = Date.parse(recordedAt);
      if (Number.isNaN(parsed)) {
        onClientError("Recorded at date/time is invalid.");
        return;
      }
      recordedAtIso = new Date(parsed).toISOString();
    }

    const created = await onCreateReading({
      recorded_at: recordedAtIso,
      gravity: gravityValue,
      temp_c: tempValue,
      ph: phValue,
      notes: noteValue,
    });
    if (created) {
      setRecordedAt("");
      setGravity("");
      setTempC("");
      setPh("");
      setNotes("");
    }
  }

  return (
    <section className="panel span-two">
      <h2>{tr("fermentation_tracker")}</h2>

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

      {batches.length === 0 ? (
        <div className="inline-note with-action">
          <span>{tr("empty_plan_hint")}</span>
          <button className="ghost-button" type="button" onClick={onJumpToDataManager}>
            {tr("jump_data_manager")}
          </button>
        </div>
      ) : (
        <>
          <div className="button-row">
            <button className="ghost-button" onClick={() => void onRefresh()} disabled={loading || !selectedBatchId}>
              {tr("refresh")}
            </button>
          </div>

          <h3>{tr("log_reading")}</h3>
          <form onSubmit={(event) => void handleCreateReading(event)} className="stack-form">
            <label>
              {tr("recorded_at")}
              <input
                type="datetime-local"
                value={recordedAt}
                onChange={(event) => setRecordedAt(event.target.value)}
              />
            </label>

            <div className="inline-grid">
              <label>
                {tr("gravity")}
                <input
                  type="number"
                  min="0.99"
                  max="1.2"
                  step="0.001"
                  value={gravity}
                  onChange={(event) => setGravity(event.target.value)}
                  placeholder="optional"
                />
              </label>

              <label>
                {tr("temperature_c")}
                <input
                  type="number"
                  min="-10"
                  max="60"
                  step="0.1"
                  value={tempC}
                  onChange={(event) => setTempC(event.target.value)}
                  placeholder="optional"
                />
              </label>
            </div>

            <div className="inline-grid">
              <label>
                {tr("ph")}
                <input
                  type="number"
                  min="0"
                  max="14"
                  step="0.01"
                  value={ph}
                  onChange={(event) => setPh(event.target.value)}
                  placeholder="optional"
                />
              </label>

              <label>
                {tr("notes")}
                <input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="optional" />
              </label>
            </div>

            <button className="primary-button" type="submit" disabled={loading || !selectedBatchId}>
              {tr("log_reading")}
            </button>
          </form>

          <h3>{tr("fermentation_trend")}</h3>
          {trend ? (
            <div className="summary-grid">
              <div className="data-row">
                <span>{tr("reading_count")}</span>
                <strong>{trend.reading_count}</strong>
              </div>
              <div className="data-row">
                <span>{tr("latest_gravity")}</span>
                <strong>{formatReadingValue(trend.latest_gravity, 3)}</strong>
              </div>
              <div className="data-row">
                <span>{tr("latest_temp_c")}</span>
                <strong>{formatReadingValue(trend.latest_temp_c, 1)}</strong>
              </div>
              <div className="data-row">
                <span>{tr("latest_ph")}</span>
                <strong>{formatReadingValue(trend.latest_ph, 2)}</strong>
              </div>
              <div className="data-row">
                <span>{tr("gravity_drop")}</span>
                <strong>{formatReadingValue(trend.gravity_drop, 4)}</strong>
              </div>
              <div className="data-row">
                <span>{tr("avg_hourly_drop")}</span>
                <strong>{formatReadingValue(trend.average_hourly_gravity_drop, 5)}</strong>
              </div>
              <div className="data-row">
                <span>{tr("plateau_risk")}</span>
                <strong>{trend.plateau_risk ? "yes" : "no"}</strong>
              </div>
              <div className="data-row">
                <span>{tr("temperature_warning")}</span>
                <strong>{trend.temperature_warning ? "yes" : "no"}</strong>
              </div>
            </div>
          ) : (
            <p className="inline-note">{tr("no_readings_logged")}</p>
          )}

          <h3>{tr("fermentation_alerts")}</h3>
          {trend?.alerts.length ? (
            <ul className="list compact-list">
              {trend.alerts.map((alert, index) => (
                <li key={`${alert}-${index}`}>{alert}</li>
              ))}
            </ul>
          ) : (
            <p className="inline-note">{tr("no_readings_logged")}</p>
          )}

          <h3>{tr("recent_readings")}</h3>
          {recentReadings.length ? (
            <ul className="list compact-list">
              {recentReadings.map((reading) => (
                <li key={reading.id}>
                  <strong>{formatDateTime(reading.recorded_at)}</strong>
                  <br />
                  SG {formatReadingValue(reading.gravity, 3)} | {tr("temperature_c")}{" "}
                  {formatReadingValue(reading.temp_c, 1)} | pH {formatReadingValue(reading.ph, 2)}
                  {reading.notes ? (
                    <>
                      <br />
                      {reading.notes}
                    </>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : (
            <p className="inline-note">{tr("no_readings_logged")}</p>
          )}
        </>
      )}
    </section>
  );
}

function parseOptionalNumber(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed)) {
    return null;
  }
  return parsed;
}

function formatReadingValue(value: number | null, digits: number): string {
  if (value === null) {
    return "--";
  }
  return value.toFixed(digits);
}

function formatDateTime(value: string): string {
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) {
    return value;
  }
  return new Date(parsed).toLocaleString();
}
