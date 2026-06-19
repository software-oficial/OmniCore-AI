-- CORE IDENTITY SECTOR
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY REFERENCES users(id),
    full_name VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    avatar_url TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC'
);

CREATE TABLE IF NOT EXISTS user_permissions (
    user_id TEXT REFERENCES users(id),
    permission_key TEXT,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, permission_key)
);

-- SERVICE VARIANTS SECTOR (Multi-Account Management)
CREATE TABLE IF NOT EXISTS service_credentials (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    service_type VARCHAR(50) NOT NULL, -- 'WHATSAPP', 'MERCADOPAGO', 'STRIPE', 'PAYPAL', etc.
    provider_id VARCHAR(255), -- External ID from the provider
    config JSONB NOT NULL, -- Store tokens, secrets, keys here
    label VARCHAR(255), -- e.g., "Store North", "Support Bot"
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_credentials_user ON service_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_credentials_type ON service_credentials(service_type);

-- INFRASTRUCTURE REGISTRY
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    owner_user_id TEXT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_tokens (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    agent_id TEXT,
    token_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apps (
    id TEXT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_id TEXT REFERENCES agents(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_infrastructure (
    app_id TEXT PRIMARY KEY REFERENCES apps(id),
    db_host VARCHAR(255) NOT NULL,
    db_port INTEGER NOT NULL,
    db_user VARCHAR(255) NOT NULL,
    db_password TEXT NOT NULL,
    db_name VARCHAR(255) NOT NULL,
    tier VARCHAR(50) DEFAULT 'FREE'
);

CREATE TABLE IF NOT EXISTS agent_app_mapping (
    agent_id TEXT REFERENCES agents(id),
    app_id TEXT REFERENCES apps(id),
    PRIMARY KEY (agent_id, app_id)
);

CREATE TABLE IF NOT EXISTS governance_tiers (
    tier_name TEXT PRIMARY KEY,
    level INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS governance_commands (
    command_name TEXT PRIMARY KEY,
    permission_key TEXT,
    min_tier TEXT REFERENCES governance_tiers(tier_name)
);

CREATE TABLE IF NOT EXISTS system_audit_log (
    id SERIAL PRIMARY KEY,
    agent_id TEXT,
    app_id TEXT,
    command TEXT,
    status TEXT,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS common_errors_kb (
    id SERIAL PRIMARY KEY,
    error_pattern TEXT UNIQUE,
    solution_guide TEXT,
    occurrence_count INTEGER DEFAULT 1,
    impact_level TEXT DEFAULT 'LOW',
    status TEXT DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level TEXT,
    category TEXT,
    message TEXT,
    app_id TEXT,
    agent_id TEXT,
    payload TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
