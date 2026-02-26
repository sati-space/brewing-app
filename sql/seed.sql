INSERT INTO users (username, email, password_hash)
VALUES ('seed-user', 'seed-user@example.com', 'seed-password-hash');

INSERT INTO recipes (
    owner_user_id,
    name,
    style,
    target_og,
    target_fg,
    target_ibu,
    target_srm,
    efficiency_pct,
    notes
)
VALUES (
    1,
    'West Coast IPA v1',
    '21A',
    1.064,
    1.012,
    62,
    8,
    72,
    'Initial house IPA recipe'
);

INSERT INTO recipe_ingredients (recipe_id, name, ingredient_type, amount, unit, stage, minute_added)
VALUES
    (1, 'Pale Malt', 'grain', 5.2, 'kg', 'mash', 0),
    (1, 'Crystal 40L', 'grain', 0.4, 'kg', 'mash', 0),
    (1, 'Centennial', 'hop', 35, 'g', 'boil', 60),
    (1, 'Citra', 'hop', 50, 'g', 'boil', 10),
    (1, 'US-05', 'yeast', 1, 'pack', 'fermentation', 0);

INSERT INTO inventory_items (owner_user_id, name, ingredient_type, quantity, unit, low_stock_threshold)
VALUES
    (1, 'Pale Malt', 'grain', 12.5, 'kg', 3.0),
    (1, 'Citra', 'hop', 180, 'g', 80),
    (1, 'US-05', 'yeast', 3, 'pack', 1);
