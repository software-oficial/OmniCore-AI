-- WHATSAPP SECTOR: MULTI-ACCOUNT ARCHITECTURE

-- 1. Contacts (The "Who")
CREATE TABLE IF NOT EXISTS contacts (
    phone VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255),
    label VARCHAR(50), -- 'lead', 'customer', 'vip'
    last_interaction TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Chat Sessions (The "Conversation State" linked to a specific credential)
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id TEXT PRIMARY KEY,
    credential_id TEXT REFERENCES service_credentials(id) ON DELETE CASCADE,
    phone VARCHAR(20) REFERENCES contacts(phone),
    current_node TEXT, -- Current state in the bot flow
    context_data JSONB, -- Temporary variables during the chat
    status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'COMPLETED', 'PENDING_HUMAN'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Message History (The "Audit" linked to a specific credential)
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id TEXT REFERENCES chat_sessions(session_id),
    credential_id TEXT REFERENCES service_credentials(id),
    sender VARCHAR(10) NOT NULL, -- 'BOT' or 'USER'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) -- 'sent', 'delivered', 'read'
);

-- 4. Bot Flow Definitions (The "Logic" tied to a credential or global)
CREATE TABLE IF NOT EXISTS bot_flows (
    node_id TEXT PRIMARY KEY,
    credential_id TEXT REFERENCES service_credentials(id), -- NULL if global flow
    prompt TEXT NOT NULL,
    options JSONB, -- Possible responses and their destination nodes
    required_permission TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_cred ON chat_sessions(credential_id);
CREATE INDEX IF NOT EXISTS idx_messages_cred ON messages(credential_id);
