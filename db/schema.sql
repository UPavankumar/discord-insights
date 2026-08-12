CREATE TABLE IF NOT EXISTS servers (
    server_id TEXT PRIMARY KEY,
    server_name TEXT NOT NULL,
    owner_id TEXT,
    creation_date TIMESTAMPTZ NOT NULL,
    region TEXT NOT NULL,
    verification_level SMALLINT NOT NULL,
    default_message_notifications SMALLINT NOT NULL,
    explicit_content_filter SMALLINT NOT NULL,
    system_channel_id TEXT,
    afk_channel_id TEXT,
    afk_timeout INTEGER,
    widget_enabled BOOLEAN NOT NULL,
    premium_tier SMALLINT NOT NULL,
    premium_subscription_count INTEGER NOT NULL,
    approximate_member_count INTEGER NOT NULL,
    approximate_presence_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS channels (
    channel_id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL REFERENCES servers(server_id),
    channel_name TEXT NOT NULL,
    channel_type TEXT NOT NULL CHECK (channel_type IN ('text', 'voice')),
    topic TEXT,
    nsfw BOOLEAN NOT NULL,
    rate_limit_per_user INTEGER NOT NULL,
    position INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS members (
    user_id TEXT NOT NULL,
    server_id TEXT NOT NULL REFERENCES servers(server_id),
    username TEXT NOT NULL,
    display_name TEXT NOT NULL,
    discriminator TEXT,
    avatar_hash TEXT,
    is_bot BOOLEAN NOT NULL,
    join_date TIMESTAMPTZ NOT NULL,
    last_active TIMESTAMPTZ,
    roles TEXT,
    messages_sent INTEGER NOT NULL,
    voice_minutes INTEGER NOT NULL,
    is_owner BOOLEAN NOT NULL,
    PRIMARY KEY (server_id, user_id)
);

CREATE TABLE IF NOT EXISTS daily_stats (
    server_id TEXT NOT NULL REFERENCES servers(server_id),
    date DATE NOT NULL,
    total_messages INTEGER NOT NULL,
    new_members INTEGER NOT NULL,
    active_members INTEGER NOT NULL,
    total_members INTEGER NOT NULL,
    day_of_week SMALLINT NOT NULL,
    is_weekend SMALLINT NOT NULL,
    PRIMARY KEY (server_id, date)
);

CREATE TABLE IF NOT EXISTS channel_daily_stats (
    channel_id TEXT NOT NULL REFERENCES channels(channel_id),
    server_id TEXT NOT NULL REFERENCES servers(server_id),
    date DATE NOT NULL,
    message_count INTEGER NOT NULL,
    active_users INTEGER NOT NULL,
    PRIMARY KEY (channel_id, date)
);

CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL REFERENCES servers(server_id),
    channel_id TEXT NOT NULL REFERENCES channels(channel_id),
    user_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    content TEXT NOT NULL,
    has_attachment BOOLEAN NOT NULL,
    has_embed BOOLEAN NOT NULL,
    reaction_count INTEGER NOT NULL,
    is_pinned BOOLEAN NOT NULL,
    length INTEGER NOT NULL,
    FOREIGN KEY (server_id, user_id)
        REFERENCES members(server_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_daily_stats_server_date
    ON daily_stats(server_id, date);

CREATE INDEX IF NOT EXISTS idx_channel_daily_stats_server_date
    ON channel_daily_stats(server_id, date);

CREATE INDEX IF NOT EXISTS idx_channel_daily_stats_channel_date
    ON channel_daily_stats(channel_id, date);

CREATE INDEX IF NOT EXISTS idx_messages_server_timestamp
    ON messages(server_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_messages_channel_timestamp
    ON messages(channel_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_messages_user_timestamp
    ON messages(server_id, user_id, timestamp);

-- Read-only role for security enforcement
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'exaqube_readonly') THEN
        CREATE ROLE exaqube_readonly WITH LOGIN PASSWORD 'exaqube_readonly_pass';
    END IF;
END $$;

GRANT CONNECT ON DATABASE exaqube TO exaqube_readonly;
GRANT USAGE ON SCHEMA public TO exaqube_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO exaqube_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO exaqube_readonly;

