import { FormEvent, useEffect, useState } from "react";

import type { Translator } from "../i18n";
import type {
  Batch,
  BatchCreate,
  EquipmentProfile,
  EquipmentProfileCreate,
  IngredientProfile,
  IngredientProfileCreate,
  Recipe,
  RecipeCreate,
} from "../types";

type DataTab = "recipes" | "ingredients" | "equipment" | "batches";

interface DataManagerPanelProps {
  loading: boolean;
  tr: Translator;
  recipes: Recipe[];
  batches: Batch[];
  ingredientProfiles: IngredientProfile[];
  equipmentProfiles: EquipmentProfile[];
  onRefresh: () => Promise<void>;
  onCreateIngredient: (payload: IngredientProfileCreate) => Promise<boolean>;
  onCreateEquipment: (payload: EquipmentProfileCreate) => Promise<boolean>;
  onCreateRecipe: (payload: RecipeCreate) => Promise<boolean>;
  onCreateBatch: (payload: BatchCreate) => Promise<boolean>;
  onClientError: (message: string) => void;
  panelId?: string;
}

export function DataManagerPanel({
  loading,
  tr,
  recipes,
  batches,
  ingredientProfiles,
  equipmentProfiles,
  onRefresh,
  onCreateIngredient,
  onCreateEquipment,
  onCreateRecipe,
  onCreateBatch,
  onClientError,
  panelId,
}: DataManagerPanelProps) {
  const [activeTab, setActiveTab] = useState<DataTab>("recipes");

  const [ingredientName, setIngredientName] = useState("");
  const [ingredientType, setIngredientType] = useState("grain");
  const [ingredientUnit, setIngredientUnit] = useState("g");
  const [ingredientNotes, setIngredientNotes] = useState("");

  const [equipmentName, setEquipmentName] = useState("");
  const [equipmentBatchVolume, setEquipmentBatchVolume] = useState("20");
  const [equipmentMashTunVolume, setEquipmentMashTunVolume] = useState("");
  const [equipmentBoilKettleVolume, setEquipmentBoilKettleVolume] = useState("");
  const [equipmentEfficiency, setEquipmentEfficiency] = useState("72");
  const [equipmentBoilOffRate, setEquipmentBoilOffRate] = useState("");
  const [equipmentTrubLoss, setEquipmentTrubLoss] = useState("");
  const [equipmentNotes, setEquipmentNotes] = useState("");

  const [recipeName, setRecipeName] = useState("");
  const [recipeStyle, setRecipeStyle] = useState("21A");
  const [recipeOg, setRecipeOg] = useState("1.060");
  const [recipeFg, setRecipeFg] = useState("1.012");
  const [recipeIbu, setRecipeIbu] = useState("60");
  const [recipeSrm, setRecipeSrm] = useState("10");
  const [recipeEfficiency, setRecipeEfficiency] = useState("72");
  const [recipeNotes, setRecipeNotes] = useState("");
  const [recipeIngredientName, setRecipeIngredientName] = useState("");
  const [recipeIngredientType, setRecipeIngredientType] = useState("grain");
  const [recipeIngredientAmount, setRecipeIngredientAmount] = useState("1");
  const [recipeIngredientUnit, setRecipeIngredientUnit] = useState("kg");
  const [recipeIngredientStage, setRecipeIngredientStage] = useState("mash");
  const [recipeIngredientMinute, setRecipeIngredientMinute] = useState("0");
  const [recipeIngredientsDraft, setRecipeIngredientsDraft] = useState<RecipeCreate["ingredients"]>([]);

  const [batchRecipeId, setBatchRecipeId] = useState<string>("");
  const [batchName, setBatchName] = useState("");
  const [batchBrewedOn, setBatchBrewedOn] = useState(todayDateString());
  const [batchStatus, setBatchStatus] = useState("planned");
  const [batchVolume, setBatchVolume] = useState("20");
  const [batchMeasuredOg, setBatchMeasuredOg] = useState("");
  const [batchMeasuredFg, setBatchMeasuredFg] = useState("");
  const [batchNotes, setBatchNotes] = useState("");

  useEffect(() => {
    if (!batchRecipeId && recipes.length > 0) {
      setBatchRecipeId(String(recipes[0].id));
    }
  }, [batchRecipeId, recipes]);

  async function handleCreateIngredient(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const created = await onCreateIngredient({
      name: ingredientName.trim(),
      ingredient_type: ingredientType.trim(),
      default_unit: ingredientUnit.trim(),
      notes: ingredientNotes.trim(),
    });
    if (created) {
      setIngredientName("");
      setIngredientNotes("");
    }
  }

  async function handleCreateEquipment(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const batchVolume = Number(equipmentBatchVolume);
    const efficiency = Number(equipmentEfficiency);
    if (!Number.isFinite(batchVolume) || batchVolume <= 0 || !Number.isFinite(efficiency) || efficiency <= 0) {
      onClientError("Equipment volume and efficiency must be valid positive numbers.");
      return;
    }

    const created = await onCreateEquipment({
      name: equipmentName.trim(),
      batch_volume_liters: batchVolume,
      mash_tun_volume_liters: parseOptionalNumber(equipmentMashTunVolume),
      boil_kettle_volume_liters: parseOptionalNumber(equipmentBoilKettleVolume),
      brewhouse_efficiency_pct: efficiency,
      boil_off_rate_l_per_hour: parseOptionalNumber(equipmentBoilOffRate),
      trub_loss_liters: parseOptionalNumber(equipmentTrubLoss),
      notes: equipmentNotes.trim(),
    });

    if (created) {
      setEquipmentName("");
      setEquipmentBatchVolume("20");
      setEquipmentMashTunVolume("");
      setEquipmentBoilKettleVolume("");
      setEquipmentEfficiency("72");
      setEquipmentBoilOffRate("");
      setEquipmentTrubLoss("");
      setEquipmentNotes("");
    }
  }

  function handleAddRecipeIngredient(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const amount = Number(recipeIngredientAmount);
    const minuteAdded = Number(recipeIngredientMinute);
    if (!Number.isFinite(amount) || amount <= 0 || !Number.isFinite(minuteAdded) || minuteAdded < 0) {
      onClientError("Ingredient amount/minute must be valid numbers.");
      return;
    }

    setRecipeIngredientsDraft((previous) => [
      ...previous,
      {
        name: recipeIngredientName.trim(),
        ingredient_type: recipeIngredientType.trim(),
        amount,
        unit: recipeIngredientUnit.trim(),
        stage: recipeIngredientStage.trim(),
        minute_added: minuteAdded,
      },
    ]);
    setRecipeIngredientName("");
    setRecipeIngredientAmount("1");
    setRecipeIngredientMinute("0");
  }

  async function handleCreateRecipe(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    if (!recipeIngredientsDraft.length) {
      onClientError("Add at least one ingredient before creating a recipe.");
      return;
    }

    const payload: RecipeCreate = {
      name: recipeName.trim(),
      style: recipeStyle.trim(),
      target_og: Number(recipeOg),
      target_fg: Number(recipeFg),
      target_ibu: Number(recipeIbu),
      target_srm: Number(recipeSrm),
      efficiency_pct: Number(recipeEfficiency),
      notes: recipeNotes.trim(),
      ingredients: recipeIngredientsDraft,
    };

    if (
      !Number.isFinite(payload.target_og) ||
      !Number.isFinite(payload.target_fg) ||
      !Number.isFinite(payload.target_ibu) ||
      !Number.isFinite(payload.target_srm) ||
      !Number.isFinite(payload.efficiency_pct)
    ) {
      onClientError("Recipe numeric fields must be valid numbers.");
      return;
    }

    const created = await onCreateRecipe(payload);
    if (created) {
      setRecipeName("");
      setRecipeNotes("");
      setRecipeIngredientsDraft([]);
    }
  }

  async function handleCreateBatch(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    if (!batchRecipeId) {
      onClientError("Select a recipe before creating a batch.");
      return;
    }

    const volumeLiters = Number(batchVolume);
    if (!Number.isFinite(volumeLiters) || volumeLiters <= 0) {
      onClientError("Batch volume must be a valid positive number.");
      return;
    }

    const measuredOg = parseOptionalNumber(batchMeasuredOg);
    const measuredFg = parseOptionalNumber(batchMeasuredFg);
    if ((measuredOg !== null && (measuredOg <= 1.0 || measuredOg >= 1.2)) || (measuredFg !== null && (measuredFg <= 0.99 || measuredFg >= 1.2))) {
      onClientError("Measured OG/FG must be within expected brewing ranges.");
      return;
    }

    const created = await onCreateBatch({
      recipe_id: Number(batchRecipeId),
      name: batchName.trim(),
      brewed_on: batchBrewedOn,
      status: batchStatus.trim(),
      volume_liters: volumeLiters,
      measured_og: measuredOg,
      measured_fg: measuredFg,
      notes: batchNotes.trim(),
    });

    if (created) {
      setBatchName("");
      setBatchBrewedOn(todayDateString());
      setBatchStatus("planned");
      setBatchVolume("20");
      setBatchMeasuredOg("");
      setBatchMeasuredFg("");
      setBatchNotes("");
    }
  }

  return (
    <section className="panel span-two" id={panelId}>
      <h2>{tr("data_manager")}</h2>

      <div className="tab-row manager-tabs">
        <button className={activeTab === "recipes" ? "tab active" : "tab"} onClick={() => setActiveTab("recipes")}>
          {tr("recipes")}
        </button>
        <button className={activeTab === "ingredients" ? "tab active" : "tab"} onClick={() => setActiveTab("ingredients")}>
          {tr("ingredients")}
        </button>
        <button className={activeTab === "equipment" ? "tab active" : "tab"} onClick={() => setActiveTab("equipment")}>
          {tr("equipment")}
        </button>
        <button className={activeTab === "batches" ? "tab active" : "tab"} onClick={() => setActiveTab("batches")}>
          {tr("batches")}
        </button>
      </div>

      <div className="button-row">
        <button className="ghost-button" onClick={() => void onRefresh()} disabled={loading}>
          {tr("refresh")}
        </button>
      </div>

      {activeTab === "recipes" ? (
        <div className="manager-grid">
          <div>
            <h3>{tr("add_ingredient")}</h3>
            <form onSubmit={(event) => void handleAddRecipeIngredient(event)} className="stack-form">
              <label>
                {tr("ingredient_name")}
                <input value={recipeIngredientName} onChange={(event) => setRecipeIngredientName(event.target.value)} required />
              </label>

              <div className="inline-grid">
                <label>
                  {tr("ingredient_type")}
                  <input
                    value={recipeIngredientType}
                    onChange={(event) => setRecipeIngredientType(event.target.value)}
                    required
                  />
                </label>
                <label>
                  {tr("amount")}
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={recipeIngredientAmount}
                    onChange={(event) => setRecipeIngredientAmount(event.target.value)}
                    required
                  />
                </label>
                <label>
                  {tr("unit")}
                  <input value={recipeIngredientUnit} onChange={(event) => setRecipeIngredientUnit(event.target.value)} required />
                </label>
              </div>

              <div className="inline-grid">
                <label>
                  {tr("stage")}
                  <input value={recipeIngredientStage} onChange={(event) => setRecipeIngredientStage(event.target.value)} required />
                </label>
                <label>
                  {tr("minute_added")}
                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={recipeIngredientMinute}
                    onChange={(event) => setRecipeIngredientMinute(event.target.value)}
                    required
                  />
                </label>
              </div>

              <button className="ghost-button" type="submit" disabled={loading}>
                {tr("add_ingredient")}
              </button>
            </form>

            {recipeIngredientsDraft.length ? (
              <ul className="list compact-list">
                {recipeIngredientsDraft.map((ingredient, index) => (
                  <li key={`${ingredient.name}-${index}`} className="list-with-action">
                    <span>
                      {ingredient.name} ({ingredient.ingredient_type}) - {ingredient.amount} {ingredient.unit}
                    </span>
                    <button
                      className="ghost-button"
                      type="button"
                      onClick={() => {
                        setRecipeIngredientsDraft((previous) => previous.filter((_, itemIndex) => itemIndex !== index));
                      }}
                    >
                      {tr("remove")}
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="inline-note">{tr("list_empty")}</p>
            )}

            <h3>{tr("new_recipe")}</h3>
            <form onSubmit={(event) => void handleCreateRecipe(event)} className="stack-form">
              <label>
                {tr("recipe_name")}
                <input value={recipeName} onChange={(event) => setRecipeName(event.target.value)} required />
              </label>

              <div className="inline-grid">
                <label>
                  {tr("style")}
                  <input value={recipeStyle} onChange={(event) => setRecipeStyle(event.target.value)} required />
                </label>
                <label>
                  {tr("efficiency")}
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="0.1"
                    value={recipeEfficiency}
                    onChange={(event) => setRecipeEfficiency(event.target.value)}
                    required
                  />
                </label>
              </div>

              <div className="inline-grid">
                <label>
                  {tr("target_og")}
                  <input
                    type="number"
                    min="1"
                    max="1.2"
                    step="0.001"
                    value={recipeOg}
                    onChange={(event) => setRecipeOg(event.target.value)}
                    required
                  />
                </label>
                <label>
                  {tr("target_fg")}
                  <input
                    type="number"
                    min="0.99"
                    max="1.2"
                    step="0.001"
                    value={recipeFg}
                    onChange={(event) => setRecipeFg(event.target.value)}
                    required
                  />
                </label>
              </div>

              <div className="inline-grid">
                <label>
                  {tr("target_ibu")}
                  <input
                    type="number"
                    min="0"
                    max="150"
                    step="0.1"
                    value={recipeIbu}
                    onChange={(event) => setRecipeIbu(event.target.value)}
                    required
                  />
                </label>
                <label>
                  {tr("target_srm")}
                  <input
                    type="number"
                    min="0"
                    max="80"
                    step="0.1"
                    value={recipeSrm}
                    onChange={(event) => setRecipeSrm(event.target.value)}
                    required
                  />
                </label>
              </div>

              <label>
                {tr("notes")}
                <input value={recipeNotes} onChange={(event) => setRecipeNotes(event.target.value)} />
              </label>

              <button className="primary-button" type="submit" disabled={loading}>
                {tr("create")}
              </button>
            </form>
          </div>

          <div>
            <h3>{tr("recipes")}</h3>
            {recipes.length ? (
              <ul className="list compact-list">
                {recipes.map((recipe) => (
                  <li key={recipe.id}>
                    <strong>#{recipe.id}</strong> {recipe.name} ({recipe.style}) - {recipe.ingredients.length} ingredients
                  </li>
                ))}
              </ul>
            ) : (
              <p className="inline-note">{tr("list_empty")}</p>
            )}
          </div>
        </div>
      ) : null}

      {activeTab === "ingredients" ? (
        <div className="manager-grid">
          <div>
            <h3>{tr("new_ingredient")}</h3>
            <form onSubmit={(event) => void handleCreateIngredient(event)} className="stack-form">
              <label>
                {tr("ingredient_name")}
                <input value={ingredientName} onChange={(event) => setIngredientName(event.target.value)} required />
              </label>

              <div className="inline-grid">
                <label>
                  {tr("ingredient_type")}
                  <input value={ingredientType} onChange={(event) => setIngredientType(event.target.value)} required />
                </label>
                <label>
                  {tr("default_unit")}
                  <input value={ingredientUnit} onChange={(event) => setIngredientUnit(event.target.value)} required />
                </label>
              </div>

              <label>
                {tr("notes")}
                <input value={ingredientNotes} onChange={(event) => setIngredientNotes(event.target.value)} />
              </label>

              <button className="primary-button" type="submit" disabled={loading}>
                {tr("create")}
              </button>
            </form>
          </div>

          <div>
            <h3>{tr("ingredients")}</h3>
            {ingredientProfiles.length ? (
              <ul className="list compact-list">
                {ingredientProfiles.map((ingredient) => (
                  <li key={ingredient.id}>
                    <strong>#{ingredient.id}</strong> {ingredient.name} ({ingredient.ingredient_type}) - {ingredient.default_unit}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="inline-note">{tr("list_empty")}</p>
            )}
          </div>
        </div>
      ) : null}

      {activeTab === "equipment" ? (
        <div className="manager-grid">
          <div>
            <h3>{tr("new_equipment")}</h3>
            <form onSubmit={(event) => void handleCreateEquipment(event)} className="stack-form">
              <label>
                {tr("equipment_profile")}
                <input value={equipmentName} onChange={(event) => setEquipmentName(event.target.value)} required />
              </label>

              <div className="inline-grid">
                <label>
                  {tr("batch_volume")}
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={equipmentBatchVolume}
                    onChange={(event) => setEquipmentBatchVolume(event.target.value)}
                    required
                  />
                </label>
                <label>
                  {tr("brewhouse_efficiency")}
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="0.1"
                    value={equipmentEfficiency}
                    onChange={(event) => setEquipmentEfficiency(event.target.value)}
                    required
                  />
                </label>
              </div>

              <div className="inline-grid">
                <label>
                  {tr("mash_tun_volume")}
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={equipmentMashTunVolume}
                    onChange={(event) => setEquipmentMashTunVolume(event.target.value)}
                  />
                </label>
                <label>
                  {tr("boil_kettle_volume")}
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={equipmentBoilKettleVolume}
                    onChange={(event) => setEquipmentBoilKettleVolume(event.target.value)}
                  />
                </label>
              </div>

              <div className="inline-grid">
                <label>
                  {tr("boil_off_rate")}
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={equipmentBoilOffRate}
                    onChange={(event) => setEquipmentBoilOffRate(event.target.value)}
                  />
                </label>
                <label>
                  {tr("trub_loss")}
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={equipmentTrubLoss}
                    onChange={(event) => setEquipmentTrubLoss(event.target.value)}
                  />
                </label>
              </div>

              <label>
                {tr("notes")}
                <input value={equipmentNotes} onChange={(event) => setEquipmentNotes(event.target.value)} />
              </label>

              <button className="primary-button" type="submit" disabled={loading}>
                {tr("create")}
              </button>
            </form>
          </div>

          <div>
            <h3>{tr("equipment")}</h3>
            {equipmentProfiles.length ? (
              <ul className="list compact-list">
                {equipmentProfiles.map((equipment) => (
                  <li key={equipment.id}>
                    <strong>#{equipment.id}</strong> {equipment.name}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="inline-note">{tr("list_empty")}</p>
            )}
          </div>
        </div>
      ) : null}

      {activeTab === "batches" ? (
        <div className="manager-grid">
          <div>
            <h3>{tr("new_batch")}</h3>
            {recipes.length ? (
              <form onSubmit={(event) => void handleCreateBatch(event)} className="stack-form">
                <label>
                  {tr("recipe")}
                  <select value={batchRecipeId} onChange={(event) => setBatchRecipeId(event.target.value)} required>
                    <option value="">{tr("choose_recipe")}</option>
                    {recipes.map((recipe) => (
                      <option key={recipe.id} value={recipe.id}>
                        #{recipe.id} - {recipe.name} ({recipe.style})
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  {tr("batch_name")}
                  <input value={batchName} onChange={(event) => setBatchName(event.target.value)} required />
                </label>

                <div className="inline-grid">
                  <label>
                    {tr("brewed_on")}
                    <input
                      type="date"
                      value={batchBrewedOn}
                      onChange={(event) => setBatchBrewedOn(event.target.value)}
                      required
                    />
                  </label>
                  <label>
                    {tr("status")}
                    <select value={batchStatus} onChange={(event) => setBatchStatus(event.target.value)}>
                      <option value="planned">planned</option>
                      <option value="brewing">brewing</option>
                      <option value="fermenting">fermenting</option>
                      <option value="conditioning">conditioning</option>
                      <option value="packaged">packaged</option>
                    </select>
                  </label>
                </div>

                <div className="inline-grid">
                  <label>
                    {tr("volume_liters")}
                    <input
                      type="number"
                      min="0"
                      step="0.1"
                      value={batchVolume}
                      onChange={(event) => setBatchVolume(event.target.value)}
                      required
                    />
                  </label>
                  <label>
                    {tr("measured_og")}
                    <input
                      type="number"
                      min="1"
                      max="1.2"
                      step="0.001"
                      value={batchMeasuredOg}
                      onChange={(event) => setBatchMeasuredOg(event.target.value)}
                      placeholder="optional"
                    />
                  </label>
                </div>

                <div className="inline-grid">
                  <label>
                    {tr("measured_fg")}
                    <input
                      type="number"
                      min="0.99"
                      max="1.2"
                      step="0.001"
                      value={batchMeasuredFg}
                      onChange={(event) => setBatchMeasuredFg(event.target.value)}
                      placeholder="optional"
                    />
                  </label>
                  <label>
                    {tr("notes")}
                    <input value={batchNotes} onChange={(event) => setBatchNotes(event.target.value)} />
                  </label>
                </div>

                <button className="primary-button" type="submit" disabled={loading}>
                  {tr("create")}
                </button>
              </form>
            ) : (
              <p className="inline-note">{tr("no_recipes_yet")}</p>
            )}
          </div>

          <div>
            <h3>{tr("batches")}</h3>
            {batches.length ? (
              <ul className="list compact-list">
                {batches.map((batch) => (
                  <li key={batch.id}>
                    <strong>#{batch.id}</strong> {batch.name} ({batch.status}) - {batch.volume_liters} L
                    {` • ${resolveRecipeName(recipes, batch.recipe_id)}`}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="inline-note">{tr("list_empty")}</p>
            )}
          </div>
        </div>
      ) : null}
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

function todayDateString(): string {
  return new Date().toISOString().slice(0, 10);
}

function resolveRecipeName(recipes: Recipe[], recipeId: number): string {
  const recipe = recipes.find((item) => item.id === recipeId);
  return recipe ? recipe.name : `recipe ${recipeId}`;
}
