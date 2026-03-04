import { useEffect, useState } from "react";

import { apiRequest, APIError, apiBaseUrl } from "./api";
import { AIAssistantPanel } from "./components/AIAssistantPanel";
import { AuthPanel, type AuthSubmitPayload } from "./components/AuthPanel";
import { BrewPlannerPanel } from "./components/BrewPlannerPanel";
import { BrewSummaryPanel } from "./components/BrewSummaryPanel";
import { DataManagerPanel } from "./components/DataManagerPanel";
import { FermentationPanel } from "./components/FermentationPanel";
import { InventoryPanel } from "./components/InventoryPanel";
import { NotesPanel } from "./components/NotesPanel";
import { OnboardingPanel } from "./components/OnboardingPanel";
import { PreferencesPanel } from "./components/PreferencesPanel";
import { ShoppingListPanel } from "./components/ShoppingListPanel";
import { TimerPanel, type TimerState } from "./components/TimerPanel";
import { translate, type TranslationKey } from "./i18n";
import type {
  AIAnalysisResponse,
  Batch,
  BatchCreate,
  BrewPlan,
  BrewPlanApplyResult,
  EquipmentProfile,
  EquipmentProfileCreate,
  FermentationReading,
  FermentationReadingCreate,
  FermentationTrend,
  IngredientProfile,
  IngredientProfileCreate,
  InventoryItem,
  InventoryItemCreate,
  Language,
  LowStockAlertResponse,
  Recipe,
  RecipeCreate,
  TemperatureUnit,
  TokenResponse,
  UnitSystem,
  User,
  WaterProfile,
} from "./types";

const TOKEN_STORAGE_KEY = "brewpilot.token";
const USER_STORAGE_KEY = "brewpilot.user";
const DATA_MANAGER_SECTION_ID = "data-manager-panel";

function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState<User | null>(() => readStoredUser());

  const [prefUnitSystem, setPrefUnitSystem] = useState<UnitSystem>("metric");
  const [prefTemperatureUnit, setPrefTemperatureUnit] = useState<TemperatureUnit>("C");
  const [prefLanguage, setPrefLanguage] = useState<Language>("en");

  const [batches, setBatches] = useState<Batch[]>([]);
  const [equipmentProfiles, setEquipmentProfiles] = useState<EquipmentProfile[]>([]);
  const [waterProfiles, setWaterProfiles] = useState<WaterProfile[]>([]);
  const [ingredientProfiles, setIngredientProfiles] = useState<IngredientProfile[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [inventoryItems, setInventoryItems] = useState<InventoryItem[]>([]);
  const [lowStockAlerts, setLowStockAlerts] = useState<LowStockAlertResponse>({ count: 0, items: [] });
  const [fermentationReadings, setFermentationReadings] = useState<FermentationReading[]>([]);
  const [fermentationTrend, setFermentationTrend] = useState<FermentationTrend | null>(null);

  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);
  const [selectedEquipmentId, setSelectedEquipmentId] = useState<number | null>(null);
  const [selectedWaterProfileId, setSelectedWaterProfileId] = useState<number | null>(null);

  const [overrideUnitSystem, setOverrideUnitSystem] = useState<"" | UnitSystem>("");
  const [overrideTemperatureUnit, setOverrideTemperatureUnit] = useState<"" | TemperatureUnit>("");
  const [overrideLanguage, setOverrideLanguage] = useState<"" | Language>("");

  const [brewPlan, setBrewPlan] = useState<BrewPlan | null>(null);
  const [applyResult, setApplyResult] = useState<BrewPlanApplyResult | null>(null);
  const [timer, setTimer] = useState<TimerState>({ stepIndex: 0, running: false, remainingSeconds: 0 });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showPreferences, setShowPreferences] = useState(false);

  const uiLanguage: Language = overrideLanguage || user?.preferred_language || "en";
  const tr = (key: TranslationKey): string => translate(uiLanguage, key);
  const hasMinimumSetup = recipes.length > 0 && equipmentProfiles.length > 0 && batches.length > 0;

  useEffect(() => {
    if (!token) {
      return;
    }
    void loadDashboard();
  }, [token]);

  useEffect(() => {
    if (!token || selectedBatchId === null) {
      setFermentationReadings([]);
      setFermentationTrend(null);
      return;
    }
    setFermentationReadings([]);
    setFermentationTrend(null);
    void loadFermentationData(selectedBatchId, { silent: true });
  }, [selectedBatchId, token]);

  useEffect(() => {
    if (!brewPlan?.timer_plan.length || !timer.running) {
      return;
    }
    const id = window.setInterval(() => {
      setTimer((previous) => {
        if (!brewPlan.timer_plan.length) {
          return { stepIndex: 0, running: false, remainingSeconds: 0 };
        }
        if (previous.remainingSeconds > 1) {
          return { ...previous, remainingSeconds: previous.remainingSeconds - 1 };
        }
        const nextIndex = previous.stepIndex + 1;
        if (nextIndex >= brewPlan.timer_plan.length) {
          return { ...previous, running: false, remainingSeconds: 0 };
        }
        return {
          stepIndex: nextIndex,
          running: true,
          remainingSeconds: secondsForStep(brewPlan.timer_plan[nextIndex]),
        };
      });
    }, 1000);
    return () => window.clearInterval(id);
  }, [brewPlan, timer.running]);

  useEffect(() => {
    if (!user) {
      return;
    }
    setPrefUnitSystem(user.preferred_unit_system);
    setPrefTemperatureUnit(user.preferred_temperature_unit);
    setPrefLanguage(user.preferred_language);
  }, [user]);

  async function loadDashboard(): Promise<boolean> {
    if (!token) {
      return false;
    }
    setLoading(true);
    setError(null);
    try {
      const [freshUser, batchList, equipmentList, waterList, ingredientList, recipeList, inventoryList, lowStock] =
        await Promise.all([
          apiRequest<User>("/auth/me", {}, token),
          apiRequest<Batch[]>("/batches", {}, token),
          apiRequest<EquipmentProfile[]>("/equipment", {}, token),
          apiRequest<WaterProfile[]>("/water-profiles", {}, token),
          apiRequest<IngredientProfile[]>("/ingredients", {}, token),
          apiRequest<Recipe[]>("/recipes", {}, token),
          apiRequest<InventoryItem[]>("/inventory", {}, token),
          apiRequest<LowStockAlertResponse>("/inventory/alerts/low-stock", {}, token),
        ]);

      setUser(freshUser);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(freshUser));

      setBatches(batchList);
      setEquipmentProfiles(equipmentList);
      setWaterProfiles(waterList);
      setIngredientProfiles(sortIngredientProfiles(ingredientList));
      setRecipes(recipeList);
      setInventoryItems(sortInventoryItems(inventoryList));
      setLowStockAlerts({
        count: lowStock.count,
        items: sortInventoryItems(lowStock.items),
      });

      setSelectedBatchId((previous) => {
        if (previous !== null && batchList.some((batch) => batch.id === previous)) {
          return previous;
        }
        return batchList[0]?.id ?? null;
      });
      return true;
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function onAuthenticate(payload: AuthSubmitPayload): Promise<boolean> {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const path = payload.mode === "login" ? "/auth/login" : "/auth/register";
      const body =
        payload.mode === "login"
          ? {
              email: payload.email,
              password: payload.password,
            }
          : {
              username: payload.username,
              email: payload.email,
              password: payload.password,
            };

      const result = await apiRequest<TokenResponse>(path, {
        method: "POST",
        body: JSON.stringify(body),
      });

      setToken(result.access_token);
      setUser(result.user);
      localStorage.setItem(TOKEN_STORAGE_KEY, result.access_token);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(result.user));

      setSuccess(payload.mode === "login" ? "Authenticated." : "Account created.");
      return true;
    } catch (err) {
      setError(toMessage(err));
      return false;
    } finally {
      setLoading(false);
    }
  }

  function clearSession(): void {
    setToken(null);
    setUser(null);
    setBatches([]);
    setEquipmentProfiles([]);
    setWaterProfiles([]);
    setIngredientProfiles([]);
    setRecipes([]);
    setInventoryItems([]);
    setLowStockAlerts({ count: 0, items: [] });
    setFermentationReadings([]);
    setFermentationTrend(null);
    setSelectedBatchId(null);
    setBrewPlan(null);
    setApplyResult(null);
    setTimer({ stepIndex: 0, running: false, remainingSeconds: 0 });
    setShowPreferences(false);
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
  }

  function onLogout(): void {
    clearSession();
    setError(null);
    setSuccess(null);
  }

  function handleUnauthorized(error: unknown): boolean {
    if (error instanceof APIError && error.status === 401) {
      clearSession();
      setSuccess(null);
      setError(tr("session_expired"));
      return true;
    }
    return false;
  }

  async function onSavePreferences(): Promise<void> {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const updated = await apiRequest<User>(
        "/auth/me/preferences",
        {
          method: "PATCH",
          body: JSON.stringify({
            preferred_unit_system: prefUnitSystem,
            preferred_temperature_unit: prefTemperatureUnit,
            preferred_language: prefLanguage,
          }),
        },
        token,
      );
      setUser(updated);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(updated));
      setSuccess("Preferences saved.");
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }

  async function onRefreshDataManager(): Promise<void> {
    setSuccess(null);
    const loaded = await loadDashboard();
    if (loaded) {
      setSuccess("Data refreshed.");
    }
  }

  async function onCreateIngredient(payload: IngredientProfileCreate): Promise<boolean> {
    if (!token) {
      return false;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const created = await apiRequest<IngredientProfile>(
        "/ingredients",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
        token,
      );
      setIngredientProfiles((previous) => sortIngredientProfiles([...previous, created]));
      setSuccess("Ingredient created.");
      return true;
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function onCreateEquipment(payload: EquipmentProfileCreate): Promise<boolean> {
    if (!token) {
      return false;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const created = await apiRequest<EquipmentProfile>(
        "/equipment",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
        token,
      );
      setEquipmentProfiles((previous) => [created, ...previous]);
      setSelectedEquipmentId(created.id);
      setSuccess("Equipment profile created.");
      return true;
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function onCreateRecipe(payload: RecipeCreate): Promise<boolean> {
    if (!token) {
      return false;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const created = await apiRequest<Recipe>(
        "/recipes",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
        token,
      );
      setRecipes((previous) => [created, ...previous]);
      setSuccess("Recipe created.");
      return true;
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function onCreateBatch(payload: BatchCreate): Promise<boolean> {
    if (!token) {
      return false;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const created = await apiRequest<Batch>(
        "/batches",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
        token,
      );
      setBatches((previous) => [created, ...previous]);
      setSelectedBatchId(created.id);
      setSuccess("Batch created.");
      return true;
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function onCreateInventoryItem(payload: InventoryItemCreate): Promise<boolean> {
    if (!token) {
      return false;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const created = await apiRequest<InventoryItem>(
        "/inventory",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
        token,
      );
      setInventoryItems((previous) => sortInventoryItems([...previous, created]));
      setLowStockAlerts((previous) => {
        const nextItems = created.is_low_stock
          ? sortInventoryItems([...previous.items.filter((item) => item.id !== created.id), created])
          : previous.items.filter((item) => item.id !== created.id);
        return {
          count: nextItems.length,
          items: nextItems,
        };
      });
      setSuccess("Inventory item created.");
      return true;
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function onRefreshInventory(): Promise<void> {
    if (!token) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const [items, alerts] = await Promise.all([
        apiRequest<InventoryItem[]>("/inventory", {}, token),
        apiRequest<LowStockAlertResponse>("/inventory/alerts/low-stock", {}, token),
      ]);
      setInventoryItems(sortInventoryItems(items));
      setLowStockAlerts({
        count: alerts.count,
        items: sortInventoryItems(alerts.items),
      });
      setSuccess("Inventory refreshed.");
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }

  async function loadFermentationData(batchId: number, options: { silent?: boolean } = {}): Promise<boolean> {
    if (!token) {
      return false;
    }

    const { silent = false } = options;
    if (!silent) {
      setLoading(true);
      setError(null);
      setSuccess(null);
    }

    try {
      const [readingList, trend] = await Promise.all([
        apiRequest<FermentationReading[]>(`/batches/${batchId}/readings`, {}, token),
        apiRequest<FermentationTrend>(`/batches/${batchId}/fermentation/trend`, {}, token),
      ]);
      setFermentationReadings(sortFermentationReadings(readingList));
      setFermentationTrend(trend);
      return true;
    } catch (err) {
      if (!handleUnauthorized(err) && !silent) {
        setError(toMessage(err));
      }
      return false;
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }

  async function onCreateFermentationReading(payload: FermentationReadingCreate): Promise<boolean> {
    if (!token || selectedBatchId === null) {
      return false;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const created = await apiRequest<FermentationReading>(
        `/batches/${selectedBatchId}/readings`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
        token,
      );
      setFermentationReadings((previous) => sortFermentationReadings([...previous, created]));

      const trend = await apiRequest<FermentationTrend>(`/batches/${selectedBatchId}/fermentation/trend`, {}, token);
      setFermentationTrend(trend);
      setSuccess("Fermentation reading logged.");
      return true;
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function onRefreshFermentation(): Promise<void> {
    if (selectedBatchId === null) {
      return;
    }
    const loaded = await loadFermentationData(selectedBatchId);
    if (loaded) {
      setSuccess("Fermentation data refreshed.");
    }
  }

  async function onGenerateBrewPlan(): Promise<void> {
    if (!token || !selectedBatchId) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    setApplyResult(null);

    try {
      const plan = await apiRequest<BrewPlan>(
        `/batches/${selectedBatchId}/brew-plan`,
        {
          method: "POST",
          body: JSON.stringify({
            equipment_profile_id: selectedEquipmentId ?? undefined,
            water_profile_id: selectedWaterProfileId ?? undefined,
            unit_system: overrideUnitSystem || undefined,
            temperature_unit: overrideTemperatureUnit || undefined,
            language: overrideLanguage || undefined,
          }),
        },
        token,
      );

      setBrewPlan(plan);
      const firstStep = plan.timer_plan[0];
      setTimer({
        stepIndex: 0,
        running: false,
        remainingSeconds: firstStep ? secondsForStep(firstStep) : 0,
      });
      setSuccess("Brew plan loaded.");
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }

  async function onApplyTimeline(): Promise<void> {
    if (!token || !selectedBatchId) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await apiRequest<BrewPlanApplyResult>(
        `/batches/${selectedBatchId}/brew-plan/apply-timeline`,
        {
          method: "POST",
          body: JSON.stringify({
            equipment_profile_id: selectedEquipmentId ?? undefined,
            water_profile_id: selectedWaterProfileId ?? undefined,
            unit_system: overrideUnitSystem || undefined,
            temperature_unit: overrideTemperatureUnit || undefined,
            language: overrideLanguage || undefined,
          }),
        },
        token,
      );
      setApplyResult(result);
      setSuccess("Timeline updated from brew plan.");
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }

  async function onOptimizeRecipe(payload: {
    recipeId: number;
    measuredOg: number | null;
    measuredFg: number | null;
  }): Promise<AIAnalysisResponse | null> {
    if (!token) {
      return null;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      return await apiRequest<AIAnalysisResponse>(
        "/ai/recipe-optimize",
        {
          method: "POST",
          body: JSON.stringify({
            recipe_id: payload.recipeId,
            measured_og: payload.measuredOg ?? undefined,
            measured_fg: payload.measuredFg ?? undefined,
          }),
        },
        token,
      );
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function onDiagnoseFermentation(batchId: number): Promise<AIAnalysisResponse | null> {
    if (!token) {
      return null;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      return await apiRequest<AIAnalysisResponse>(
        "/ai/fermentation-diagnose",
        {
          method: "POST",
          body: JSON.stringify({
            batch_id: batchId,
          }),
        },
        token,
      );
    } catch (err) {
      if (!handleUnauthorized(err)) {
        setError(toMessage(err));
      }
      return null;
    } finally {
      setLoading(false);
    }
  }

  function onStartPause(): void {
    if (!brewPlan?.timer_plan.length) {
      return;
    }

    setTimer((previous) => {
      if (!previous.running && previous.remainingSeconds === 0) {
        const current = brewPlan.timer_plan[previous.stepIndex];
        return {
          ...previous,
          running: true,
          remainingSeconds: current ? secondsForStep(current) : 0,
        };
      }
      return { ...previous, running: !previous.running };
    });
  }

  function onNextStep(): void {
    if (!brewPlan?.timer_plan.length) {
      return;
    }

    setTimer((previous) => {
      const nextIndex = Math.min(previous.stepIndex + 1, brewPlan.timer_plan.length - 1);
      const nextStep = brewPlan.timer_plan[nextIndex];
      return {
        stepIndex: nextIndex,
        running: false,
        remainingSeconds: secondsForStep(nextStep),
      };
    });
  }

  function onResetTimer(): void {
    if (!brewPlan?.timer_plan.length) {
      return;
    }

    setTimer({
      stepIndex: 0,
      running: false,
      remainingSeconds: secondsForStep(brewPlan.timer_plan[0]),
    });
  }

  function onJumpToDataManager(): void {
    const panel = document.getElementById(DATA_MANAGER_SECTION_ID);
    if (panel) {
      panel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <h1>{tr("app_title")}</h1>
          <p>
            {tr("api_base")}: <code>{apiBaseUrl}</code>
          </p>
        </div>
        {token ? (
          <div className="hero-actions">
            <button className="ghost-button" onClick={() => setShowPreferences(true)}>
              {tr("settings")}
            </button>
            <button className="ghost-button" onClick={onLogout}>
              {tr("logout")}
            </button>
          </div>
        ) : null}
      </header>

      {error ? <p className="message error">{error}</p> : null}
      {success ? <p className="message success">{success}</p> : null}

      {!token ? (
        <AuthPanel loading={loading} tr={tr} onAuthenticate={onAuthenticate} />
      ) : (
        <section className="dashboard-grid">
          {!hasMinimumSetup ? <OnboardingPanel tr={tr} onJumpToDataManager={onJumpToDataManager} /> : null}

          <BrewPlannerPanel
            loading={loading}
            tr={tr}
            batches={batches}
            equipmentProfiles={equipmentProfiles}
            waterProfiles={waterProfiles}
            selectedBatchId={selectedBatchId}
            selectedEquipmentId={selectedEquipmentId}
            selectedWaterProfileId={selectedWaterProfileId}
            overrideUnitSystem={overrideUnitSystem}
            overrideTemperatureUnit={overrideTemperatureUnit}
            overrideLanguage={overrideLanguage}
            applyResult={applyResult}
            hasMinimumSetup={hasMinimumSetup}
            onSelectedBatchChange={setSelectedBatchId}
            onSelectedEquipmentChange={setSelectedEquipmentId}
            onSelectedWaterProfileChange={setSelectedWaterProfileId}
            onOverrideUnitSystemChange={setOverrideUnitSystem}
            onOverrideTemperatureUnitChange={setOverrideTemperatureUnit}
            onOverrideLanguageChange={setOverrideLanguage}
            onGeneratePlan={onGenerateBrewPlan}
            onApplyTimeline={onApplyTimeline}
            onJumpToDataManager={onJumpToDataManager}
          />

          <BrewSummaryPanel tr={tr} brewPlan={brewPlan} onJumpToDataManager={onJumpToDataManager} />

          <AIAssistantPanel
            loading={loading}
            tr={tr}
            recipes={recipes}
            batches={batches}
            selectedBatchId={selectedBatchId}
            onOptimizeRecipe={onOptimizeRecipe}
            onDiagnoseFermentation={onDiagnoseFermentation}
            onClientError={(message) => {
              setSuccess(null);
              setError(message);
            }}
          />

          <InventoryPanel
            loading={loading}
            tr={tr}
            items={inventoryItems}
            alerts={lowStockAlerts}
            onCreateItem={onCreateInventoryItem}
            onRefresh={onRefreshInventory}
            onClientError={(message) => {
              setSuccess(null);
              setError(message);
            }}
          />

          <FermentationPanel
            loading={loading}
            tr={tr}
            batches={batches}
            selectedBatchId={selectedBatchId}
            readings={fermentationReadings}
            trend={fermentationTrend}
            onSelectedBatchChange={setSelectedBatchId}
            onCreateReading={onCreateFermentationReading}
            onRefresh={onRefreshFermentation}
            onJumpToDataManager={onJumpToDataManager}
            onClientError={(message) => {
              setSuccess(null);
              setError(message);
            }}
          />

          <TimerPanel
            tr={tr}
            brewPlan={brewPlan}
            timer={timer}
            onStartPause={onStartPause}
            onNextStep={onNextStep}
            onReset={onResetTimer}
            onJumpToDataManager={onJumpToDataManager}
          />

          <ShoppingListPanel tr={tr} brewPlan={brewPlan} onJumpToDataManager={onJumpToDataManager} />
          <NotesPanel tr={tr} brewPlan={brewPlan} onJumpToDataManager={onJumpToDataManager} />

          <DataManagerPanel
            loading={loading}
            tr={tr}
            recipes={recipes}
            batches={batches}
            ingredientProfiles={ingredientProfiles}
            equipmentProfiles={equipmentProfiles}
            onRefresh={onRefreshDataManager}
            onCreateIngredient={onCreateIngredient}
            onCreateEquipment={onCreateEquipment}
            onCreateRecipe={onCreateRecipe}
            onCreateBatch={onCreateBatch}
            onClientError={(message) => {
              setSuccess(null);
              setError(message);
            }}
            panelId={DATA_MANAGER_SECTION_ID}
          />
        </section>
      )}

      {token && showPreferences ? (
        <div className="modal-backdrop" onClick={() => setShowPreferences(false)}>
          <div className="modal-content" onClick={(event) => event.stopPropagation()}>
            <PreferencesPanel
              loading={loading}
              tr={tr}
              unitSystem={prefUnitSystem}
              temperatureUnit={prefTemperatureUnit}
              language={prefLanguage}
              onUnitSystemChange={setPrefUnitSystem}
              onTemperatureUnitChange={setPrefTemperatureUnit}
              onLanguageChange={setPrefLanguage}
              onSave={onSavePreferences}
            />
            <div className="button-row">
              <button className="ghost-button" onClick={() => setShowPreferences(false)}>
                {tr("close")}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}

function secondsForStep(step: { duration_minutes: number | null }): number {
  const minutes = step.duration_minutes ?? 0;
  return Math.max(0, minutes * 60);
}

function readStoredUser(): User | null {
  const raw = localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

function sortIngredientProfiles(items: IngredientProfile[]): IngredientProfile[] {
  return [...items].sort((left, right) => {
    const typeCmp = left.ingredient_type.localeCompare(right.ingredient_type);
    if (typeCmp !== 0) {
      return typeCmp;
    }
    return left.name.localeCompare(right.name);
  });
}

function sortInventoryItems(items: InventoryItem[]): InventoryItem[] {
  return [...items].sort((left, right) => left.name.localeCompare(right.name));
}

function sortFermentationReadings(items: FermentationReading[]): FermentationReading[] {
  return [...items].sort((left, right) => {
    const timeCmp = left.recorded_at.localeCompare(right.recorded_at);
    if (timeCmp !== 0) {
      return timeCmp;
    }
    return left.id - right.id;
  });
}

function toMessage(error: unknown): string {
  if (error instanceof APIError) {
    return `${error.status}: ${error.message}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected error";
}

export default App;
