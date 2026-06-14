-- OmniCore-AI WhatsApp Bot Blueprint
-- This SQL should be executed by the developer in their external database.

-- Conversations Table: Tracks the current state of every user
CREATE TABLE IF NOT EXISTS whatsapp_conversations (
    phone_number VARCHAR(20) PRIMARY KEY,
    current_menu VARCHAR(100) DEFAULT 'main',
    last_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_human_intervening BOOLEAN DEFAULT FALSE,
    user_context JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'ACTIVE' -- ACTIVE, BLOCKED, ARCHIVED
);

-- Menus Table: Defines the bot's navigation structure
CREATE TABLE IF NOT EXISTS whatsapp_menus (
    menu_id SERIAL PRIMARY KEY,
    menu_name VARCHAR(100) UNIQUE NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Menu Options Table: The choices available in each menu
CREATE TABLE IF NOT EXISTS whatsapp_menu_options (
    option_id SERIAL PRIMARY KEY,
    menu_id INTEGER REFERENCES whatsapp_menus(menu_id) ON DELETE CASCADE,
    label VARCHAR(255) NOT NULL,
    value VARCHAR(100) NOT NULL, -- The keyword or menu_name to trigger next
    action_type VARCHAR(50) DEFAULT 'NAVIGATE', -- NAVIGATE, COMMAND, HUMAN
    command_name VARCHAR(100), -- The CommandDispatcher command to execute
    sort_order INTEGER DEFAULT 0
);

CREATE INDEX idx_conv_status ON whatsapp_conversations(status);
CREATE INDEX idx_menu_name ON whatsapp_menus(menu_name);
