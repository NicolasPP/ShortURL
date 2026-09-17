CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE surl_status AS ENUM ('ACTIVE', 'EXPIRED', 'RECLAIMED');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
);

CREATE TABLE url (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    original_url TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

# Use hash of url intead of id

CREATE TABLE surl (
    surl VARCHAR(7) PRIMARY KEY,
    url_id UUID NOT NULL REFERENCES url(id) ON DELETE RESTRICT,
    status surl_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);