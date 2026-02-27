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

export interface EquipmentProfile {
  id: number;
  name: string;
}

export interface WaterProfile {
  id: number;
  name: string;
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
