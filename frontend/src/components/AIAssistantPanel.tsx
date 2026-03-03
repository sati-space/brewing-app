import { FormEvent, useEffect, useState } from "react";

import type { Translator } from "../i18n";
import type { AIAnalysisResponse, Batch, Recipe } from "../types";

interface OptimizeRecipeInput {
  recipeId: number;
  measuredOg: number | null;
  measuredFg: number | null;
}

interface AIAssistantPanelProps {
  loading: boolean;
  tr: Translator;
  recipes: Recipe[];
  batches: Batch[];
  selectedBatchId: number | null;
  onOptimizeRecipe: (payload: OptimizeRecipeInput) => Promise<AIAnalysisResponse | null>;
  onDiagnoseFermentation: (batchId: number) => Promise<AIAnalysisResponse | null>;
  onClientError: (message: string) => void;
}

export function AIAssistantPanel({
  loading,
  tr,
  recipes,
  batches,
  selectedBatchId,
  onOptimizeRecipe,
  onDiagnoseFermentation,
  onClientError,
}: AIAssistantPanelProps) {
  const [recipeId, setRecipeId] = useState<number | null>(null);
  const [batchId, setBatchId] = useState<number | null>(selectedBatchId);
  const [measuredOg, setMeasuredOg] = useState("");
  const [measuredFg, setMeasuredFg] = useState("");
  const [analysis, setAnalysis] = useState<AIAnalysisResponse | null>(null);

  useEffect(() => {
    if (recipeId === null && recipes.length > 0) {
      setRecipeId(recipes[0].id);
    }
  }, [recipeId, recipes]);

  useEffect(() => {
    if (selectedBatchId !== null) {
      setBatchId(selectedBatchId);
      return;
    }
    if (batchId === null && batches.length > 0) {
      setBatchId(batches[0].id);
    }
  }, [batchId, batches, selectedBatchId]);

  async function handleOptimizeRecipe(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!recipeId) {
      return;
    }

    const og = parseOptionalNumber(measuredOg);
    const fg = parseOptionalNumber(measuredFg);

    if ((og !== null && (og <= 1.0 || og >= 1.2)) || (fg !== null && (fg <= 0.99 || fg >= 1.2))) {
      onClientError("Measured OG/FG must be within expected brewing ranges.");
      return;
    }

    const result = await onOptimizeRecipe({
      recipeId,
      measuredOg: og,
      measuredFg: fg,
    });
    if (result) {
      setAnalysis(result);
    }
  }

  async function handleDiagnoseFermentation(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!batchId) {
      return;
    }

    const result = await onDiagnoseFermentation(batchId);
    if (result) {
      setAnalysis(result);
    }
  }

  return (
    <section className="panel span-two ai-panel">
      <h2>{tr("ai_assistant")}</h2>

      <div className="manager-grid ai-grid">
        <form onSubmit={(event) => void handleOptimizeRecipe(event)} className="stack-form">
          <h3>{tr("optimize_recipe")}</h3>
          <label>
            {tr("recipe")}
            <select
              value={recipeId ?? ""}
              onChange={(event) => setRecipeId(event.target.value ? Number(event.target.value) : null)}
            >
              <option value="">{tr("default_value")}</option>
              {recipes.map((recipe) => (
                <option key={recipe.id} value={recipe.id}>
                  #{recipe.id} - {recipe.name} ({recipe.style})
                </option>
              ))}
            </select>
          </label>

          <div className="inline-grid">
            <label>
              {tr("measured_og")}
              <input
                type="number"
                min="1"
                max="1.2"
                step="0.001"
                value={measuredOg}
                onChange={(event) => setMeasuredOg(event.target.value)}
                placeholder="optional"
              />
            </label>
            <label>
              {tr("measured_fg")}
              <input
                type="number"
                min="0.99"
                max="1.2"
                step="0.001"
                value={measuredFg}
                onChange={(event) => setMeasuredFg(event.target.value)}
                placeholder="optional"
              />
            </label>
          </div>

          <button className="primary-button" type="submit" disabled={loading || !recipeId}>
            {tr("optimize_recipe")}
          </button>
        </form>

        <form onSubmit={(event) => void handleDiagnoseFermentation(event)} className="stack-form">
          <h3>{tr("diagnose_fermentation")}</h3>
          <label>
            {tr("select_batch")}
            <select value={batchId ?? ""} onChange={(event) => setBatchId(event.target.value ? Number(event.target.value) : null)}>
              <option value="">{tr("default_value")}</option>
              {batches.map((batch) => (
                <option key={batch.id} value={batch.id}>
                  #{batch.id} - {batch.name} ({batch.status})
                </option>
              ))}
            </select>
          </label>

          <button className="primary-button" type="submit" disabled={loading || !batchId}>
            {tr("diagnose_fermentation")}
          </button>
        </form>
      </div>

      <h3>{tr("ai_latest_result")}</h3>
      {analysis ? (
        <>
          <p className="inline-note">
            <strong>{tr("ai_source")}:</strong> <code>{analysis.source}</code>
          </p>
          <p className="inline-note">{analysis.summary}</p>
          {analysis.suggestions.length ? (
            <ul className="list compact-list">
              {analysis.suggestions.map((item, index) => (
                <li key={`${item.title}-${index}`}>
                  <strong>{item.title}</strong> ({item.priority})<br />
                  {item.rationale}<br />
                  Action: {item.action}
                </li>
              ))}
            </ul>
          ) : null}
        </>
      ) : (
        <p className="inline-note">{tr("ai_no_result")}</p>
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
