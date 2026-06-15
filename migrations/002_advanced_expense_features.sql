-- Adds transaction currency metadata for multi-currency entry and reporting.
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS currency_code VARCHAR(3) NOT NULL DEFAULT 'PKR';

-- Adds the rate used to convert transaction amount into dashboard/base currency.
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS exchange_rate DOUBLE PRECISION NOT NULL DEFAULT 1.0;

-- Adds category-level monthly budget support while preserving legacy total budgets.
ALTER TABLE budgets
ADD COLUMN IF NOT EXISTS category VARCHAR(64);

-- Adds the category-specific monthly spending limit.
ALTER TABLE budgets
ADD COLUMN IF NOT EXISTS limit_amount DOUBLE PRECISION;

-- Speeds up category/month budget lookups used by budget alert APIs.
CREATE INDEX IF NOT EXISTS ix_budgets_category
ON budgets (category);

-- Speeds up monthly transaction analytics, forecasting, and budget usage checks.
CREATE INDEX IF NOT EXISTS ix_transactions_user_type_category_date
ON transactions (user_id, entry_type, category, entry_date);
