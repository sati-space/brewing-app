import { FormEvent, useState } from "react";

import type { Translator } from "../i18n";
import type {
  EquipmentProfile,
  EquipmentProfileCreate,
  IngredientProfile,
  IngredientProfileCreate,
  Recipe,
  RecipeCreate,
} from "../types";

type DataTab = "recipes" | "ingredients" | "equipment";

interface DataManagerPanelProps {
  loading: boolean;
  tr: Translator;
  recipes: Recipe[];
  ingredientProfiles: IngredientProfile[];
  equipmentProfiles: EquipmentProfile[];
  onRefresh: () => Promise<void>;
  onCreateIngredient: (payload: IngredientProfileCreate) => Promise<boolean>;
  onCreateEquipment: (payload: EquipmentProfileCreate) => Promise<boolean>;
  onCreateRecipe: (payload: RecipeCreate) => Promise<boolean>;
  onClientError: (message: string) => void;
  panelId?: string;
}

export function DataManagerPanel({
  loading,
  tr,
  recipes,
  ingredientProfiles,
  equipmentProfiles,
  onRefresh,
  onCreateIngredient,
  onCreateEquipment,
  onCreateRecipe,
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
