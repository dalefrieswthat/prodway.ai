-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Multi-tenant: Organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',  -- free, pro, enterprise
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'member',  -- owner, admin, member
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Connected integrations per org
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    platform VARCHAR(50) NOT NULL,  -- slack, github, gmail, notion, linear, jira
    credentials JSONB NOT NULL,  -- encrypted tokens
    settings JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Projects/Workspaces
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    context_paths TEXT[],  -- Local paths for cursor-context
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ingested messages/content
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    source VARCHAR(50) NOT NULL,  -- slack, github, gmail, cursor, etc.
    message_type VARCHAR(50) NOT NULL,  -- chat, email, commit, pr_review, document

    content TEXT NOT NULL,
    content_hash VARCHAR(64),  -- For deduplication

    author VARCHAR(255),
    author_id VARCHAR(255),
    channel VARCHAR(255),

    metadata JSONB DEFAULT '{}',

    embedding_id VARCHAR(255),  -- Reference to vector store

    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learned patterns
CREATE TABLE patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    pattern_type VARCHAR(50) NOT NULL,  -- communication, code_style, template
    name VARCHAR(255),
    description TEXT,
    examples TEXT[],

    embedding_id VARCHAR(255),

    frequency INTEGER DEFAULT 1,
    confidence FLOAT DEFAULT 0.5,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Drafts awaiting approval
CREATE TABLE drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    draft_type VARCHAR(50) NOT NULL,  -- slack, email, pr_review
    target_platform VARCHAR(50),
    target_id VARCHAR(255),  -- channel ID, email address, PR number

    context TEXT NOT NULL,  -- Original message/situation
    content TEXT NOT NULL,  -- Generated draft

    confidence FLOAT,
    sources_used TEXT[],

    status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected, sent
    edits TEXT,  -- User edits before sending
    feedback TEXT,  -- User feedback for learning

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE
);

-- Audit log for all agent actions
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,

    details JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- SowFlow: SOW Generation & Deal Flow
-- ============================================================

-- Slack workspace installations (multi-tenant via OAuth)
CREATE TABLE slack_installations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id VARCHAR(50) UNIQUE NOT NULL,       -- Slack workspace ID
    team_name VARCHAR(255),
    bot_token TEXT NOT NULL,                    -- Encrypted bot OAuth token
    bot_user_id VARCHAR(50),
    installer_user_id VARCHAR(50),
    scopes TEXT[],
    is_active BOOLEAN DEFAULT true,
    installed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Generated SOWs
CREATE TABLE sows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    short_id VARCHAR(8) UNIQUE NOT NULL,       -- Human-friendly ID
    team_id VARCHAR(50) NOT NULL,              -- Slack workspace
    created_by VARCHAR(50),                    -- Slack user ID
    channel_id VARCHAR(50),                    -- Where /sow was run

    -- SOW content
    title VARCHAR(255),
    executive_summary TEXT,
    content JSONB NOT NULL,                    -- Full SOW data (scope, deliverables, etc.)
    original_request TEXT,                     -- What the user typed in /sow

    -- Client info
    client_name VARCHAR(255),
    client_email VARCHAR(255),
    company_name VARCHAR(255),

    -- Pricing
    total_value DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    pricing_structure JSONB,

    -- Integration references
    docusign_envelope_id VARCHAR(255),
    stripe_payment_url TEXT,
    stripe_invoice_id VARCHAR(255),

    -- Status tracking
    status VARCHAR(50) DEFAULT 'draft',        -- draft, sent, viewed, signed, paid, dismissed
    sent_at TIMESTAMP WITH TIME ZONE,
    viewed_at TIMESTAMP WITH TIME ZONE,
    signed_at TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SOW activity log
CREATE TABLE sow_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sow_id UUID REFERENCES sows(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,           -- created, sent, signed, paid, edited, dismissed
    actor VARCHAR(255),                        -- Who performed the action
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_messages_org_id ON messages(org_id);
CREATE INDEX idx_messages_source ON messages(source);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_messages_content_hash ON messages(content_hash);

CREATE INDEX idx_patterns_org_id ON patterns(org_id);
CREATE INDEX idx_patterns_user_id ON patterns(user_id);

CREATE INDEX idx_drafts_org_id ON drafts(org_id);
CREATE INDEX idx_drafts_status ON drafts(status);

CREATE INDEX idx_audit_log_org_id ON audit_log(org_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);

-- SowFlow indexes
CREATE INDEX idx_slack_installations_team_id ON slack_installations(team_id);
CREATE INDEX idx_sows_team_id ON sows(team_id);
CREATE INDEX idx_sows_short_id ON sows(short_id);
CREATE INDEX idx_sows_status ON sows(status);
CREATE INDEX idx_sows_created_at ON sows(created_at DESC);
CREATE INDEX idx_sow_events_sow_id ON sow_events(sow_id);

-- Row Level Security (for multi-tenancy)
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE slack_installations ENABLE ROW LEVEL SECURITY;
ALTER TABLE sows ENABLE ROW LEVEL SECURITY;
ALTER TABLE sow_events ENABLE ROW LEVEL SECURITY;
