import { FormEvent, useEffect, useMemo, useState } from "react";

import { apiRequest, APIError, apiBaseUrl } from "./api";
import type {
  Batch,
  BrewPlan,
  BrewPlanApplyResult,
  EquipmentProfile,
  Language,
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
  | "not_loaded";

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
  },
};

interface TimerState {
  stepIndex: number;
  running: boolean;
  remainingSeconds: number;
}

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

  async function loadDashboard(): Promise<void> {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [freshUser, batchList, equipmentList, waterList] = await Promise.all([
        apiRequest<User>("/auth/me", {}, token),
        apiRequest<Batch[]>("/batches", {}, token),
        apiRequest<EquipmentProfile[]>("/equipment", {}, token),
        apiRequest<WaterProfile[]>("/water-profiles", {}, token),
      ]);

      setUser(freshUser);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(freshUser));
      setBatches(batchList);
      setEquipmentProfiles(equipmentList);
      setWaterProfiles(waterList);

      if (batchList.length > 0 && selectedBatchId === null) {
        setSelectedBatchId(batchList[0].id);
      }
    } catch (err) {
      setError(toMessage(err));
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
