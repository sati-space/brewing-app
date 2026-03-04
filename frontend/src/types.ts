export type UnitSystem = "metric" | "imperial";
export type TemperatureUnit = "C" | "F";
export type Language = "en" | "es";

export interface User {
  id: number;
  username: string;
  email: string;
  preferred_unit_system: UnitSystem;
  preferred_temperature_unit: TemperatureUnit;
  preferred_language: Language;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Batch {
  id: number;
  recipe_id: number;
  name: string;
  brewed_on: string;
  status: string;
  volume_liters: number;
  measured_og: number | null;
  measured_fg: number | null;
  notes: string;
  created_at: string;
}

export interface BatchCreate {
  recipe_id: number;
  name: string;
  brewed_on: string;
  status: string;
  volume_liters: number;
  measured_og: number | null;
  measured_fg: number | null;
  notes: string;
}

export interface EquipmentProfile {
  id: number;
  name: string;
  batch_volume_liters?: number;
  mash_tun_volume_liters?: number | null;
  boil_kettle_volume_liters?: number | null;
  brewhouse_efficiency_pct?: number;
  boil_off_rate_l_per_hour?: number | null;
  trub_loss_liters?: number | null;
  notes?: string;
  source_provider?: string;
  source_external_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface WaterProfile {
  id: number;
  name: string;
}

export interface IngredientProfile {
  id: number;
  name: string;
  ingredient_type: string;
  default_unit: string;
  notes: string;
  source_provider?: string | null;
  source_external_id?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface IngredientProfileCreate {
  name: string;
  ingredient_type: string;
  default_unit: string;
  notes: string;
}

export interface InventoryItem {
  id: number;
  name: string;
  ingredient_type: string;
  quantity: number;
  unit: string;
  low_stock_threshold: number;
  updated_at: string;
  is_low_stock: boolean;
}

export interface InventoryItemCreate {
  name: string;
  ingredient_type: string;
  quantity: number;
  unit: string;
  low_stock_threshold: number;
}

export interface LowStockAlertResponse {
  count: number;
  items: InventoryItem[];
}

export interface EquipmentProfileCreate {
  name: string;
  batch_volume_liters: number;
  mash_tun_volume_liters: number | null;
  boil_kettle_volume_liters: number | null;
  brewhouse_efficiency_pct: number;
  boil_off_rate_l_per_hour: number | null;
  trub_loss_liters: number | null;
  notes: string;
}

export interface RecipeIngredient {
  id?: number;
  name: string;
  ingredient_type: string;
  amount: number;
  unit: string;
  stage: string;
  minute_added: number;
}

export interface Recipe {
  id: number;
  name: string;
  style: string;
  target_og: number;
  target_fg: number;
  target_ibu: number;
  target_srm: number;
  efficiency_pct: number;
  notes: string;
  created_at?: string;
  ingredients: RecipeIngredient[];
}

export interface RecipeCreate {
  name: string;
  style: string;
  target_og: number;
  target_fg: number;
  target_ibu: number;
  target_srm: number;
  efficiency_pct: number;
  notes: string;
  ingredients: RecipeIngredient[];
}

export interface BrewPlanStep {
  step_order: number;
  timer_key: string;
  name: string;
  duration_minutes: number;
  target_temp_c: number | null;
  start_offset_minutes: number;
  planned_start_at: string | null;
  planned_end_at: string | null;
}

export interface BrewPlanShoppingItem {
  name: string;
  ingredient_type: string;
  shortage_amount: number;
  required_unit: string;
}

export interface BrewPlanDisplayUnits {
  unit_system: UnitSystem;
  language: Language;
  grain_unit: string;
  volume_unit: string;
  temperature_unit: TemperatureUnit;
}

export interface BrewPlanDisplay {
  grain_bill: number;
  mash_water: number;
  sparge_water: number;
  total_water: number;
  pre_boil_volume: number;
  post_boil_volume: number;
  boil_off: number;
  mash_target_temp: number;
  strike_water_temp: number;
}

export interface BrewPlan {
  batch_id: number;
  batch_name: string;
  style: string;
  generated_at: string;
  unit_system: UnitSystem;
  temperature_unit: TemperatureUnit;
  language: Language;
  inventory_shortage_count: number;
  notes: string[];
  timer_plan: BrewPlanStep[];
  shopping_list: BrewPlanShoppingItem[];
  display_units: BrewPlanDisplayUnits;
  display: BrewPlanDisplay;
}

export interface BrewPlanApplyResult {
  batch_id: number;
  generated_at: string;
  deleted_step_count: number;
  preserved_step_count: number;
  created_step_count: number;
  notes: string[];
}

export interface AISuggestion {
  title: string;
  rationale: string;
  action: string;
  priority: string;
}

export interface AIAnalysisResponse {
  summary: string;
  suggestions: AISuggestion[];
  source: string;
}
