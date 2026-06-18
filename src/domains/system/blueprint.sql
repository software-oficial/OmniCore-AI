-- Business Settings Table
-- Stores dynamic configuration for the client's business instance.
-- This allows the owner to change credentials and parameters via UI without server restarts.

CREATE TABLE IF NOT EXISTS business_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_business_settings_key ON business_settings(setting_key);
