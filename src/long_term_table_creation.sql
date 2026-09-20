CREATE SCHEMA IF NOT EXISTS short_url;

CREATE TYPE short_url.surl_status AS ENUM ('ACTIVE', 'EXPIRED', 'RECLAIMED');

CREATE TABLE IF NOT EXISTS short_url.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS short_url.url (
    url_hash VARCHAR(64) PRIMARY KEY,
    original_url TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS short_url.surl (
    surl VARCHAR(7) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES short_url.users(id) ON DELETE CASCADE,
    url_hash VARCHAR(64) NOT NULL REFERENCES short_url.url(url_hash) ON DELETE RESTRICT,
    status short_url.surl_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE TABLE clicks (
    id BIGSERIAL PRIMARY KEY,
    surl VARCHAR(7) NOT NULL REFERENCES surl(surl) ON DELETE CASCADE,
    clicked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Group by surl, sorted by clicked at. Optimized for traffic calculations
CREATE INDEX click_rate ON clicks (surl, clicked_at);
