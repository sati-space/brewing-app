-- BrewPilot core schema (PostgreSQL-style SQL)

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(40) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recipes (
    id SERIAL PRIMARY KEY,
    owner_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(140) NOT NULL,
    style VARCHAR(80) NOT NULL DEFAULT 'Unknown',
    target_og NUMERIC(5, 3) NOT NULL,
    target_fg NUMERIC(5, 3) NOT NULL,
    target_ibu NUMERIC(6, 2) NOT NULL,
    target_srm NUMERIC(6, 2) NOT NULL,
    efficiency_pct NUMERIC(5, 2) NOT NULL DEFAULT 70.0,
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL,
    ingredient_type VARCHAR(30) NOT NULL,
    amount NUMERIC(8, 3) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    stage VARCHAR(30) NOT NULL DEFAULT 'boil',
    minute_added INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS batches (
    id SERIAL PRIMARY KEY,
    owner_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id),
    name VARCHAR(140) NOT NULL,
    brewed_on DATE NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'planned',
    volume_liters NUMERIC(8, 2) NOT NULL,
    measured_og NUMERIC(5, 3),
    measured_fg NUMERIC(5, 3),
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fermentation_readings (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    gravity NUMERIC(5, 3),
    temp_c NUMERIC(5, 2),
    ph NUMERIC(4, 2),
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS inventory_items (
    id SERIAL PRIMARY KEY,
    owner_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL,
    ingredient_type VARCHAR(30) NOT NULL,
    quantity NUMERIC(10, 3) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    low_stock_threshold NUMERIC(10, 3) NOT NULL DEFAULT 0.0,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (owner_user_id, name)
);
