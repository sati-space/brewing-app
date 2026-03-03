import type { Language } from "./types";

export type TranslationKey =
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
  | "batches"
  | "new_batch"
  | "recipe"
  | "batch_name"
  | "brewed_on"
  | "status"
  | "volume_liters"
  | "measured_og"
  | "measured_fg"
  | "choose_recipe"
  | "no_recipes_yet"
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
  | "remove"
  | "jump_data_manager"
  | "empty_plan_hint"
  | "getting_started_title"
  | "getting_started_intro"
  | "getting_started_step_1"
  | "getting_started_step_2"
  | "getting_started_step_3"
  | "open_api_docs";

export type Translator = (key: TranslationKey) => string;

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
    batches: "Batches",
    new_batch: "New Batch",
    recipe: "Recipe",
    batch_name: "Batch Name",
    brewed_on: "Brewed On",
    status: "Status",
    volume_liters: "Volume (L)",
    measured_og: "Measured OG",
    measured_fg: "Measured FG",
    choose_recipe: "Choose recipe",
    no_recipes_yet: "Create at least one recipe first.",
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
    jump_data_manager: "Go To Data Manager",
    empty_plan_hint: "Create recipes and equipment first, then generate your first brew plan.",
    getting_started_title: "Get Started",
    getting_started_intro: "Set up your brew workspace in three quick steps.",
    getting_started_step_1: "Create one recipe and one equipment profile in Data Manager.",
    getting_started_step_2: "Create a batch in Data Manager (Batches tab).",
    getting_started_step_3: "Return here, select your batch, and generate a brew plan.",
    open_api_docs: "Open API Docs",
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
    batches: "Lotes",
    new_batch: "Nuevo lote",
    recipe: "Receta",
    batch_name: "Nombre del lote",
    brewed_on: "Fecha de brew",
    status: "Estado",
    volume_liters: "Volumen (L)",
    measured_og: "OG medida",
    measured_fg: "FG medida",
    choose_recipe: "Selecciona receta",
    no_recipes_yet: "Crea al menos una receta primero.",
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
    jump_data_manager: "Ir al gestor de datos",
    empty_plan_hint: "Crea recetas y equipos primero, luego genera tu primer brew plan.",
    getting_started_title: "Primeros pasos",
    getting_started_intro: "Configura tu espacio de brew en tres pasos.",
    getting_started_step_1: "Crea una receta y un perfil de equipo en el gestor de datos.",
    getting_started_step_2: "Crea un lote en el gestor de datos (pestaña Lotes).",
    getting_started_step_3: "Vuelve aqui, selecciona el lote y genera un brew plan.",
    open_api_docs: "Abrir API Docs",
  },
};

export function translate(language: Language, key: TranslationKey): string {
  return translations[language][key];
}
