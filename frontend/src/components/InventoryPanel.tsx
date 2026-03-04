import { FormEvent, useMemo, useState } from "react";

import type { Translator } from "../i18n";
import type { InventoryItem, InventoryItemCreate, LowStockAlertResponse } from "../types";

interface InventoryPanelProps {
  loading: boolean;
  tr: Translator;
  items: InventoryItem[];
  alerts: LowStockAlertResponse;
  onCreateItem: (payload: InventoryItemCreate) => Promise<boolean>;
  onRefresh: () => Promise<void>;
  onClientError: (message: string) => void;
}

export function InventoryPanel({ loading, tr, items, alerts, onCreateItem, onRefresh, onClientError }: InventoryPanelProps) {
  const [name, setName] = useState("");
  const [ingredientType, setIngredientType] = useState("hop");
  const [quantity, setQuantity] = useState("0");
  const [unit, setUnit] = useState("g");
  const [lowStockThreshold, setLowStockThreshold] = useState("0");
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);

  const visibleItems = useMemo(() => {
    if (!showLowStockOnly) {
      return items;
    }
    return items.filter((item) => item.is_low_stock);
  }, [items, showLowStockOnly]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const parsedQuantity = Number(quantity);
    const parsedThreshold = Number(lowStockThreshold);

    if (
      !Number.isFinite(parsedQuantity) ||
      parsedQuantity < 0 ||
      !Number.isFinite(parsedThreshold) ||
      parsedThreshold < 0
    ) {
      onClientError("Inventory quantity and low-stock threshold must be valid non-negative numbers.");
      return;
    }

    const created = await onCreateItem({
      name: name.trim(),
      ingredient_type: ingredientType.trim(),
      quantity: parsedQuantity,
      unit: unit.trim(),
      low_stock_threshold: parsedThreshold,
    });

    if (created) {
      setName("");
      setQuantity("0");
      setLowStockThreshold("0");
    }
  }

  return (
    <section className="panel span-two">
      <h2>{tr("inventory")}</h2>

      <div className="button-row">
        <button className="ghost-button" onClick={() => void onRefresh()} disabled={loading}>
          {tr("refresh")}
        </button>
      </div>

      <p className="inline-note">
        <strong>{tr("low_stock_alerts")}:</strong> {alerts.count}
      </p>

      {alerts.items.length ? (
        <ul className="list compact-list">
          {alerts.items.map((item) => (
            <li key={item.id}>
              <strong>{item.name}</strong> ({item.ingredient_type}) - {item.quantity} {item.unit}
            </li>
          ))}
        </ul>
      ) : null}

      <h3>{tr("new_inventory_item")}</h3>
      <form onSubmit={(event) => void handleSubmit(event)} className="stack-form">
        <label>
          {tr("ingredient_name")}
          <input value={name} onChange={(event) => setName(event.target.value)} required />
        </label>

        <div className="inline-grid">
          <label>
            {tr("ingredient_type")}
            <input value={ingredientType} onChange={(event) => setIngredientType(event.target.value)} required />
          </label>
          <label>
            {tr("unit")}
            <input value={unit} onChange={(event) => setUnit(event.target.value)} required />
          </label>
        </div>

        <div className="inline-grid">
          <label>
            {tr("quantity")}
            <input
              type="number"
              min="0"
              step="0.01"
              value={quantity}
              onChange={(event) => setQuantity(event.target.value)}
              required
            />
          </label>
          <label>
            {tr("low_stock_threshold")}
            <input
              type="number"
              min="0"
              step="0.01"
              value={lowStockThreshold}
              onChange={(event) => setLowStockThreshold(event.target.value)}
              required
            />
          </label>
        </div>

        <button className="primary-button" type="submit" disabled={loading}>
          {tr("create")}
        </button>
      </form>

      <label className="inventory-toggle">
        <input
          type="checkbox"
          checked={showLowStockOnly}
          onChange={(event) => setShowLowStockOnly(event.target.checked)}
        />
        <span>{tr("show_low_stock_only")}</span>
      </label>

      {visibleItems.length ? (
        <ul className="list compact-list">
          {visibleItems.map((item) => (
            <li key={item.id}>
              <strong>{item.name}</strong> ({item.ingredient_type}) - {item.quantity} {item.unit}
              {item.is_low_stock ? <span className="low-stock-pill">{tr("low_stock")}</span> : null}
            </li>
          ))}
        </ul>
      ) : (
        <p className="inline-note">{tr("list_empty")}</p>
      )}
    </section>
  );
}
