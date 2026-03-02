import { FormEvent, useEffect, useMemo, useState } from "react";

import { apiRequest, APIError, apiBaseUrl } from "./api";
import type {
  Batch,
  BrewPlan,
  BrewPlanApplyResult,
  EquipmentProfileCreate,
  EquipmentProfile,
  IngredientProfile,
  IngredientProfileCreate,
  Language,
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

type TranslationKey =
  | "app_title"
  | "login"
  | "register"
  | "email"
  | "password"
  | "username"
  | "submit"
  | "logout"
  | "preferences"
  | "save_preferences"
  | "unit_system"
  | "temperature_unit"
  | "language"
  | "dashboard"
  | "select_batch"
  | "equipment_profile"
  | "water_profile"
  | "generate_plan"
  | "apply_timeline"
  | "overrides"
  | "default_value"
  | "timer"
  | "start"
  | "pause"
  | "next_step"
  | "reset"
  | "shopping_list"
  | "notes"
  | "summary"
  | "grain_bill"
  | "mash_water"
  | "sparge_water"
  | "total_water"
  | "pre_boil"
  | "post_boil"
  | "boil_off"
  | "mash_target_temp"
  | "strike_temp"
  | "step"
  | "of"
  | "missing"
  | "api_base"
  | "not_loaded"
  | "data_manager"
  | "recipes"
  | "ingredients"
  | "equipment"
  | "refresh"
  | "create"
  | "new_recipe"
  | "recipe_name"
  | "style"
  | "target_og"
  | "target_fg"
  | "target_ibu"
  | "target_srm"
  | "efficiency"
  | "ingredient_name"
  | "ingredient_type"
  | "amount"
  | "unit"
  | "stage"
  | "minute_added"
  | "add_ingredient"
  | "new_ingredient"
  | "default_unit"
  | "new_equipment"
  | "batch_volume"
  | "mash_tun_volume"
  | "boil_kettle_volume"
  | "boil_off_rate"
  | "trub_loss"
  | "brewhouse_efficiency"
  | "list_empty"
  | "remove";

const translations: Record<Language, Record<TranslationKey, string>> = {
  en: {
    app_title: "BrewPilot",
    login: "Login",
    register: "Register",
    email: "Email",
    password: "Password",
    username: "Username",
    submit: "Submit",
    logout: "Logout",
    preferences: "Preferences",
    save_preferences: "Save Preferences",
    unit_system: "Unit System",
    temperature_unit: "Temperature Unit",
    language: "Language",
    dashboard: "Brew-Day Dashboard",
    select_batch: "Batch",
    equipment_profile: "Equipment",
    water_profile: "Water Profile",
    generate_plan: "Generate Brew Plan",
    apply_timeline: "Apply Plan To Timeline",
    overrides: "Plan Overrides",
    default_value: "Default",
    timer: "Step Timer",
    start: "Start",
    pause: "Pause",
    next_step: "Next Step",
    reset: "Reset",
    shopping_list: "Shopping List",
    notes: "Notes",
    summary: "Display Summary",
    grain_bill: "Grain bill",
    mash_water: "Mash water",
    sparge_water: "Sparge water",
    total_water: "Total water",
    pre_boil: "Pre-boil volume",
    post_boil: "Post-boil volume",
    boil_off: "Boil-off",
    mash_target_temp: "Mash target temp",
    strike_temp: "Strike water temp",
    step: "Step",
    of: "of",
    missing: "Missing",
    api_base: "API base",
    not_loaded: "No brew plan loaded yet.",
    data_manager: "Data Manager",
    recipes: "Recipes",
    ingredients: "Ingredients",
    equipment: "Equipment",
    refresh: "Refresh",
    create: "Create",
    new_recipe: "New Recipe",
    recipe_name: "Recipe Name",
    style: "Style",
    target_og: "Target OG",
    target_fg: "Target FG",
    target_ibu: "Target IBU",
    target_srm: "Target SRM",
    efficiency: "Efficiency %",
    ingredient_name: "Ingredient Name",
    ingredient_type: "Ingredient Type",
    amount: "Amount",
    unit: "Unit",
    stage: "Stage",
    minute_added: "Minute Added",
    add_ingredient: "Add Ingredient",
    new_ingredient: "New Ingredient",
    default_unit: "Default Unit",
    new_equipment: "New Equipment",
    batch_volume: "Batch Volume (L)",
    mash_tun_volume: "Mash Tun Volume (L)",
    boil_kettle_volume: "Boil Kettle Volume (L)",
    boil_off_rate: "Boil Off Rate (L/hr)",
    trub_loss: "Trub Loss (L)",
    brewhouse_efficiency: "Brewhouse Efficiency %",
    list_empty: "No records yet.",
    remove: "Remove",
  },
  es: {
    app_title: "BrewPilot",
    login: "Iniciar sesion",
    register: "Registrar",
    email: "Correo",
    password: "Contrasena",
    username: "Usuario",
    submit: "Enviar",
    logout: "Cerrar sesion",
    preferences: "Preferencias",
    save_preferences: "Guardar Preferencias",
    unit_system: "Sistema de unidades",
    temperature_unit: "Unidad de temperatura",
    language: "Idioma",
    dashboard: "Panel de Brew Day",
    select_batch: "Lote",
    equipment_profile: "Equipo",
    water_profile: "Perfil de agua",
    generate_plan: "Generar Brew Plan",
    apply_timeline: "Aplicar Plan al Timeline",
    overrides: "Overrides del Plan",
    default_value: "Por defecto",
    timer: "Temporizador de pasos",
    start: "Iniciar",
    pause: "Pausar",
    next_step: "Siguiente paso",
    reset: "Reiniciar",
    shopping_list: "Lista de compras",
    notes: "Notas",
    summary: "Resumen de visualizacion",
    grain_bill: "Carga de grano",
    mash_water: "Agua de macerado",
    sparge_water: "Agua de lavado",
    total_water: "Agua total",
    pre_boil: "Volumen pre-hervor",
    post_boil: "Volumen post-hervor",
    boil_off: "Evaporacion",
    mash_target_temp: "Temp objetivo de macerado",
    strike_temp: "Temp agua de entrada",
    step: "Paso",
    of: "de",
    missing: "Faltante",
    api_base: "Base API",
    not_loaded: "No hay brew plan cargado.",
    data_manager: "Gestor de datos",
    recipes: "Recetas",
    ingredients: "Ingredientes",
    equipment: "Equipos",
    refresh: "Actualizar",
    create: "Crear",
    new_recipe: "Nueva receta",
    recipe_name: "Nombre de receta",
    style: "Estilo",
    target_og: "OG objetivo",
    target_fg: "FG objetivo",
    target_ibu: "IBU objetivo",
    target_srm: "SRM objetivo",
    efficiency: "Eficiencia %",
    ingredient_name: "Nombre del ingrediente",
    ingredient_type: "Tipo de ingrediente",
    amount: "Cantidad",
    unit: "Unidad",
    stage: "Etapa",
    minute_added: "Minuto agregado",
    add_ingredient: "Agregar ingrediente",
    new_ingredient: "Nuevo ingrediente",
    default_unit: "Unidad por defecto",
    new_equipment: "Nuevo equipo",
    batch_volume: "Volumen del lote (L)",
    mash_tun_volume: "Volumen de macerador (L)",
    boil_kettle_volume: "Volumen de olla (L)",
    boil_off_rate: "Evaporacion (L/h)",
    trub_loss: "Perdida de turbio (L)",
    brewhouse_efficiency: "Eficiencia de sala %",
    list_empty: "Sin registros aun.",
    remove: "Quitar",
  },
};

interface TimerState {
  stepIndex: number;
  running: boolean;
  remainingSeconds: number;
}

type DataTab = "recipes" | "ingredients" | "equipment";

function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState<User | null>(() => readStoredUser());

  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [prefUnitSystem, setPrefUnitSystem] = useState<UnitSystem>("metric");
  const [prefTemperatureUnit, setPrefTemperatureUnit] = useState<TemperatureUnit>("C");
  const [prefLanguage, setPrefLanguage] = useState<Language>("en");

  const [batches, setBatches] = useState<Batch[]>([]);
  const [equipmentProfiles, setEquipmentProfiles] = useState<EquipmentProfile[]>([]);
  const [waterProfiles, setWaterProfiles] = useState<WaterProfile[]>([]);
  const [ingredientProfiles, setIngredientProfiles] = useState<IngredientProfile[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [activeDataTab, setActiveDataTab] = useState<DataTab>("recipes");

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

  const uiLanguage: Language = overrideLanguage || user?.preferred_language || "en";
  const tr = (key: TranslationKey): string => translations[uiLanguage][key];

  useEffect(() => {
    if (!token) {
      return;
    }
    void loadDashboard();
  }, [token]);

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
      const [freshUser, batchList, equipmentList, waterList, ingredientList, recipeList] = await Promise.all([
        apiRequest<User>("/auth/me", {}, token),
        apiRequest<Batch[]>("/batches", {}, token),
        apiRequest<EquipmentProfile[]>("/equipment", {}, token),
        apiRequest<WaterProfile[]>("/water-profiles", {}, token),
        apiRequest<IngredientProfile[]>("/ingredients", {}, token),
        apiRequest<Recipe[]>("/recipes", {}, token),
      ]);

      setUser(freshUser);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(freshUser));
      setBatches(batchList);
      setEquipmentProfiles(equipmentList);
      setWaterProfiles(waterList);
      setIngredientProfiles(ingredientList);
      setRecipes(recipeList);

      if (batchList.length > 0 && selectedBatchId === null) {
        setSelectedBatchId(batchList[0].id);
      }
      return true;
    } catch (err) {
      setError(toMessage(err));
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function onAuthenticate(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const path = authMode === "login" ? "/auth/login" : "/auth/register";
      const body =
        authMode === "login"
          ? { email, password }
          : {
              username,
              email,
              password,
            };

      const result = await apiRequest<TokenResponse>(path, {
        method: "POST",
        body: JSON.stringify(body),
      });

      setToken(result.access_token);
      setUser(result.user);
      localStorage.setItem(TOKEN_STORAGE_KEY, result.access_token);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(result.user));

      setEmail("");
      setPassword("");
      setUsername("");
      setSuccess(authMode === "login" ? "Authenticated." : "Account created.");
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function onLogout(): void {
    setToken(null);
    setUser(null);
    setBatches([]);
    setEquipmentProfiles([]);
    setWaterProfiles([]);
    setIngredientProfiles([]);
    setRecipes([]);
    setBrewPlan(null);
    setApplyResult(null);
    setTimer({ stepIndex: 0, running: false, remainingSeconds: 0 });
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
  }

  async function onSavePreferences(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
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
      setError(toMessage(err));
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

  async function onCreateIngredient(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const payload: IngredientProfileCreate = {
        name: ingredientName.trim(),
        ingredient_type: ingredientType.trim(),
        default_unit: ingredientUnit.trim(),
        notes: ingredientNotes.trim(),
      };
      const created = await apiRequest<IngredientProfile>(
        "/ingredients",
        { method: "POST", body: JSON.stringify(payload) },
        token,
      );
      setIngredientProfiles((previous) => [...previous, created]);
      setIngredientName("");
      setIngredientNotes("");
      setSuccess("Ingredient created.");
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function onCreateEquipment(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!token) {
      return;
    }
    const batchVolume = Number(equipmentBatchVolume);
    const efficiency = Number(equipmentEfficiency);
    if (!Number.isFinite(batchVolume) || batchVolume <= 0 || !Number.isFinite(efficiency) || efficiency <= 0) {
      setError("Equipment volume and efficiency must be valid positive numbers.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const payload: EquipmentProfileCreate = {
        name: equipmentName.trim(),
        batch_volume_liters: batchVolume,
        mash_tun_volume_liters: parseOptionalNumber(equipmentMashTunVolume),
        boil_kettle_volume_liters: parseOptionalNumber(equipmentBoilKettleVolume),
        brewhouse_efficiency_pct: efficiency,
        boil_off_rate_l_per_hour: parseOptionalNumber(equipmentBoilOffRate),
        trub_loss_liters: parseOptionalNumber(equipmentTrubLoss),
        notes: equipmentNotes.trim(),
      };
      const created = await apiRequest<EquipmentProfile>(
        "/equipment",
        { method: "POST", body: JSON.stringify(payload) },
        token,
      );
      setEquipmentProfiles((previous) => [created, ...previous]);
      setSelectedEquipmentId(created.id);
      setEquipmentName("");
      setEquipmentBatchVolume("20");
      setEquipmentMashTunVolume("");
      setEquipmentBoilKettleVolume("");
      setEquipmentEfficiency("72");
      setEquipmentBoilOffRate("");
      setEquipmentTrubLoss("");
      setEquipmentNotes("");
      setSuccess("Equipment profile created.");
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function onAddRecipeIngredient(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const amount = Number(recipeIngredientAmount);
    const minuteAdded = Number(recipeIngredientMinute);
    if (!Number.isFinite(amount) || amount <= 0 || !Number.isFinite(minuteAdded) || minuteAdded < 0) {
      setError("Ingredient amount/minute must be valid numbers.");
      return;
    }

    setError(null);
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

  function onRemoveRecipeIngredient(index: number): void {
    setRecipeIngredientsDraft((previous) => previous.filter((_, itemIndex) => itemIndex !== index));
  }

  async function onCreateRecipe(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!token) {
      return;
    }
    if (!recipeIngredientsDraft.length) {
      setError("Add at least one ingredient before creating a recipe.");
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
      setError("Recipe numeric fields must be valid numbers.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const created = await apiRequest<Recipe>("/recipes", { method: "POST", body: JSON.stringify(payload) }, token);
      setRecipes((previous) => [created, ...previous]);
      setRecipeName("");
      setRecipeNotes("");
      setRecipeIngredientsDraft([]);
      setSuccess("Recipe created.");
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
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
      setError(toMessage(err));
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
      setError(toMessage(err));
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

  const activeStep = useMemo(() => {
    if (!brewPlan?.timer_plan.length) {
      return null;
    }
    return brewPlan.timer_plan[timer.stepIndex] ?? null;
  }, [brewPlan, timer.stepIndex]);

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <h1>{tr("app_title")}</h1>
          <p>{tr("api_base")}: <code>{apiBaseUrl}</code></p>
        </div>
        {token ? (
          <button className="ghost-button" onClick={onLogout}>
            {tr("logout")}
          </button>
        ) : null}
      </header>

      {error ? <p className="message error">{error}</p> : null}
      {success ? <p className="message success">{success}</p> : null}

      {!token ? (
        <section className="panel auth-panel">
          <div className="tab-row">
            <button
              className={authMode === "login" ? "tab active" : "tab"}
              onClick={() => setAuthMode("login")}
            >
              {tr("login")}
            </button>
            <button
              className={authMode === "register" ? "tab active" : "tab"}
              onClick={() => setAuthMode("register")}
            >
              {tr("register")}
            </button>
          </div>
          <form onSubmit={onAuthenticate}>
            {authMode === "register" ? (
              <label>
                {tr("username")}
                <input value={username} onChange={(event) => setUsername(event.target.value)} required />
              </label>
            ) : null}
            <label>
              {tr("email")}
              <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
            </label>
            <label>
              {tr("password")}
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </label>
            <button className="primary-button" type="submit" disabled={loading}>
              {tr("submit")}
            </button>
          </form>
        </section>
      ) : (
        <section className="dashboard-grid">
          <section className="panel">
            <h2>{tr("preferences")}</h2>
            <form onSubmit={onSavePreferences} className="stack-form">
              <label>
                {tr("unit_system")}
                <select value={prefUnitSystem} onChange={(event) => setPrefUnitSystem(event.target.value as UnitSystem)}>
                  <option value="metric">metric</option>
                  <option value="imperial">imperial</option>
                </select>
              </label>
              <label>
                {tr("temperature_unit")}
                <select
                  value={prefTemperatureUnit}
                  onChange={(event) => setPrefTemperatureUnit(event.target.value as TemperatureUnit)}
                >
                  <option value="C">C</option>
                  <option value="F">F</option>
                </select>
              </label>
              <label>
                {tr("language")}
                <select value={prefLanguage} onChange={(event) => setPrefLanguage(event.target.value as Language)}>
                  <option value="en">en</option>
                  <option value="es">es</option>
                </select>
              </label>
              <button className="primary-button" type="submit" disabled={loading}>
                {tr("save_preferences")}
              </button>
            </form>
          </section>

          <section className="panel">
            <h2>{tr("dashboard")}</h2>
            <div className="stack-form">
              <label>
                {tr("select_batch")}
                <select
                  value={selectedBatchId ?? ""}
                  onChange={(event) => setSelectedBatchId(event.target.value ? Number(event.target.value) : null)}
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
                  onChange={(event) => setSelectedEquipmentId(event.target.value ? Number(event.target.value) : null)}
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
                  onChange={(event) => setSelectedWaterProfileId(event.target.value ? Number(event.target.value) : null)}
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
            <div className="override-grid">
              <label>
                {tr("unit_system")}
                <select
                  value={overrideUnitSystem}
                  onChange={(event) => setOverrideUnitSystem((event.target.value as UnitSystem | "") || "")}
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
                  onChange={(event) => setOverrideTemperatureUnit((event.target.value as TemperatureUnit | "") || "")}
                >
                  <option value="">{tr("default_value")}</option>
                  <option value="C">C</option>
                  <option value="F">F</option>
                </select>
              </label>
              <label>
                {tr("language")}
                <select
                  value={overrideLanguage}
                  onChange={(event) => setOverrideLanguage((event.target.value as Language | "") || "")}
                >
                  <option value="">{tr("default_value")}</option>
                  <option value="en">en</option>
                  <option value="es">es</option>
                </select>
              </label>
            </div>

            <div className="button-row">
              <button className="primary-button" onClick={() => void onGenerateBrewPlan()} disabled={loading || !selectedBatchId}>
                {tr("generate_plan")}
              </button>
              <button className="ghost-button" onClick={() => void onApplyTimeline()} disabled={loading || !selectedBatchId}>
                {tr("apply_timeline")}
              </button>
            </div>
            {applyResult ? (
              <p className="inline-note">
                created: {applyResult.created_step_count}, deleted: {applyResult.deleted_step_count}, preserved:{" "}
                {applyResult.preserved_step_count}
              </p>
            ) : null}
          </section>

          <section className="panel span-two">
            <h2>{tr("summary")}</h2>
            {brewPlan ? (
              <div className="summary-grid">
                <DataRow label={tr("grain_bill")} value={brewPlan.display.grain_bill} unit={brewPlan.display_units.grain_unit} />
                <DataRow label={tr("mash_water")} value={brewPlan.display.mash_water} unit={brewPlan.display_units.volume_unit} />
                <DataRow label={tr("sparge_water")} value={brewPlan.display.sparge_water} unit={brewPlan.display_units.volume_unit} />
                <DataRow label={tr("total_water")} value={brewPlan.display.total_water} unit={brewPlan.display_units.volume_unit} />
                <DataRow label={tr("pre_boil")} value={brewPlan.display.pre_boil_volume} unit={brewPlan.display_units.volume_unit} />
                <DataRow label={tr("post_boil")} value={brewPlan.display.post_boil_volume} unit={brewPlan.display_units.volume_unit} />
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
              <p>{tr("not_loaded")}</p>
            )}
          </section>

          <section className="panel span-two">
            <h2>{tr("timer")}</h2>
            {brewPlan && activeStep ? (
              <>
                <p className="timer-title">
                  {tr("step")} {timer.stepIndex + 1} {tr("of")} {brewPlan.timer_plan.length}: {activeStep.name}
                </p>
                <p className="timer-readout">{formatTimer(timer.remainingSeconds)}</p>
                <div className="button-row">
                  <button className="primary-button" onClick={onStartPause}>
                    {timer.running ? tr("pause") : tr("start")}
                  </button>
                  <button className="ghost-button" onClick={onNextStep}>
                    {tr("next_step")}
                  </button>
                  <button className="ghost-button" onClick={onResetTimer}>
                    {tr("reset")}
                  </button>
                </div>
              </>
            ) : (
              <p>{tr("not_loaded")}</p>
            )}
          </section>

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

          <section className="panel">
            <h2>{tr("notes")}</h2>
            {brewPlan?.notes.length ? (
              <ul className="list">
                {brewPlan.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            ) : (
              <p>-</p>
            )}
          </section>

          <section className="panel span-two">
            <h2>{tr("data_manager")}</h2>
            <div className="tab-row manager-tabs">
              <button
                className={activeDataTab === "recipes" ? "tab active" : "tab"}
                onClick={() => setActiveDataTab("recipes")}
              >
                {tr("recipes")}
              </button>
              <button
                className={activeDataTab === "ingredients" ? "tab active" : "tab"}
                onClick={() => setActiveDataTab("ingredients")}
              >
                {tr("ingredients")}
              </button>
              <button
                className={activeDataTab === "equipment" ? "tab active" : "tab"}
                onClick={() => setActiveDataTab("equipment")}
              >
                {tr("equipment")}
              </button>
            </div>
            <div className="button-row">
              <button className="ghost-button" onClick={() => void onRefreshDataManager()} disabled={loading}>
                {tr("refresh")}
              </button>
            </div>

            {activeDataTab === "recipes" ? (
              <div className="manager-grid">
                <div>
                  <h3>{tr("add_ingredient")}</h3>
                  <form onSubmit={onAddRecipeIngredient} className="stack-form">
                    <label>
                      {tr("ingredient_name")}
                      <input
                        value={recipeIngredientName}
                        onChange={(event) => setRecipeIngredientName(event.target.value)}
                        required
                      />
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
                        <input
                          value={recipeIngredientUnit}
                          onChange={(event) => setRecipeIngredientUnit(event.target.value)}
                          required
                        />
                      </label>
                    </div>
                    <div className="inline-grid">
                      <label>
                        {tr("stage")}
                        <input
                          value={recipeIngredientStage}
                          onChange={(event) => setRecipeIngredientStage(event.target.value)}
                          required
                        />
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
                          <button className="ghost-button" onClick={() => onRemoveRecipeIngredient(index)}>
                            {tr("remove")}
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="inline-note">{tr("list_empty")}</p>
                  )}

                  <h3>{tr("new_recipe")}</h3>
                  <form onSubmit={onCreateRecipe} className="stack-form">
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

            {activeDataTab === "ingredients" ? (
              <div className="manager-grid">
                <div>
                  <h3>{tr("new_ingredient")}</h3>
                  <form onSubmit={onCreateIngredient} className="stack-form">
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

            {activeDataTab === "equipment" ? (
              <div className="manager-grid">
                <div>
                  <h3>{tr("new_equipment")}</h3>
                  <form onSubmit={onCreateEquipment} className="stack-form">
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
        </section>
      )}
    </main>
  );
}

function DataRow({ label, value, unit }: { label: string; value: number; unit: string }) {
  return (
    <div className="data-row">
      <span>{label}</span>
      <strong>
        {value} {unit}
      </strong>
    </div>
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

function formatTimer(totalSeconds: number): string {
  const safeSeconds = Math.max(0, totalSeconds);
  const minutes = Math.floor(safeSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = Math.floor(safeSeconds % 60)
    .toString()
    .padStart(2, "0");
  return `${minutes}:${seconds}`;
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
