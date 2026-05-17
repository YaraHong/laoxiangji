-- =========================================================
-- Franchise CRM / RAG System Database Init Script
-- PostgreSQL 15+
-- =========================================================

BEGIN;

-- =========================================================
-- 1. "system_user"（最基础依赖）
-- =========================================================
CREATE TABLE "system_user"
(
    id            BIGSERIAL PRIMARY KEY,
    username      VARCHAR(80)  NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    display_name  VARCHAR(80)  NOT NULL,
    role          VARCHAR(40)  NOT NULL,
    status        VARCHAR(24)  NOT NULL DEFAULT 'active',
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- =========================================================
-- 2. consultant
-- =========================================================
CREATE TABLE consultant
(
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT,
    name       VARCHAR(80) NOT NULL,
    phone      VARCHAR(32),
    region     VARCHAR(80),
    status     VARCHAR(24) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================
-- 3. customer_lead
-- =========================================================
CREATE TABLE customer_lead
(
    id                     BIGSERIAL PRIMARY KEY,
    lead_no                VARCHAR(64) NOT NULL UNIQUE,
    name                   VARCHAR(80),
    phone                  VARCHAR(32),
    wechat                 VARCHAR(80),
    city                   VARCHAR(80),
    source_channel         VARCHAR(32) NOT NULL DEFAULT 'web',
    intent_level           VARCHAR(8)  NOT NULL DEFAULT 'D',
    score                  INTEGER     NOT NULL DEFAULT 0,
    follow_status          VARCHAR(32) NOT NULL DEFAULT 'new',
    assigned_consultant_id BIGINT,
    latest_session_id      BIGINT,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_customer_lead_level ON customer_lead (intent_level);
CREATE INDEX idx_customer_lead_city ON customer_lead (city);
CREATE INDEX idx_customer_lead_phone ON customer_lead (phone);

-- =========================================================
-- 4. chat_session
-- =========================================================
CREATE TABLE chat_session
(
    id              BIGSERIAL PRIMARY KEY,
    session_no      VARCHAR(64) NOT NULL UNIQUE,
    channel         VARCHAR(32) NOT NULL DEFAULT 'web',
    visitor_id      VARCHAR(64),
    lead_id         BIGINT,
    status          VARCHAR(24) NOT NULL DEFAULT 'active',
    summary         TEXT,
    last_message_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_session_visitor ON chat_session (visitor_id);
CREATE INDEX idx_chat_session_status ON chat_session (status);

-- =========================================================
-- 5. chat_message
-- =========================================================
CREATE TABLE chat_message
(
    id           BIGSERIAL PRIMARY KEY,
    session_id   BIGINT      NOT NULL REFERENCES chat_session (id),
    role         VARCHAR(24) NOT NULL,
    content      TEXT        NOT NULL,
    message_type VARCHAR(24) NOT NULL DEFAULT 'text',
    confidence   NUMERIC(5, 4),
    metadata     JSONB       NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_message_session ON chat_message (session_id, id);
CREATE INDEX idx_chat_message_role ON chat_message (role);

-- =========================================================
-- 6. rag_citation
-- =========================================================
CREATE TABLE rag_citation
(
    id             BIGSERIAL PRIMARY KEY,
    message_id     BIGINT        NOT NULL REFERENCES chat_message (id),
    chunk_id       BIGINT        NOT NULL,
    document_title VARCHAR(200)  NOT NULL,
    score          NUMERIC(8, 6) NOT NULL,
    snippet        TEXT          NOT NULL,
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_citation_message ON rag_citation (message_id);

-- =========================================================
-- 7. customer_profile
-- =========================================================
CREATE TABLE customer_profile
(
    id                        BIGSERIAL PRIMARY KEY,
    lead_id                   BIGINT      NOT NULL UNIQUE REFERENCES customer_lead (id),
    budget_range              VARCHAR(80),
    has_store                 BOOLEAN,
    store_area                NUMERIC(10, 2),
    catering_experience       TEXT,
    open_timeline             VARCHAR(80),
    concerns                  JSONB       NOT NULL DEFAULT '[]',
    extracted_fields          JSONB       NOT NULL DEFAULT '{}',
    confirmed_fields          JSONB       NOT NULL DEFAULT '{}',
    last_extracted_message_id BIGINT,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================
-- 8. customer_tag
-- =========================================================
CREATE TABLE customer_tag
(
    id         BIGSERIAL PRIMARY KEY,
    lead_id    BIGINT      NOT NULL REFERENCES customer_lead (id),
    tag_code   VARCHAR(64) NOT NULL,
    tag_name   VARCHAR(80) NOT NULL,
    source     VARCHAR(24) NOT NULL DEFAULT 'ai',
    confidence NUMERIC(5, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_customer_tag_lead ON customer_tag (lead_id);
CREATE UNIQUE INDEX uk_customer_tag ON customer_tag (lead_id, tag_code);

-- =========================================================
-- 9. lead_score_record
-- =========================================================
CREATE TABLE lead_score_record
(
    id           BIGSERIAL PRIMARY KEY,
    lead_id      BIGINT      NOT NULL REFERENCES customer_lead (id),
    score        INTEGER     NOT NULL,
    intent_level VARCHAR(8)  NOT NULL,
    reasons      JSONB       NOT NULL DEFAULT '[]',
    rule_version VARCHAR(32) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lead_score_record_lead ON lead_score_record (lead_id, id);

-- =========================================================
-- 10. human_takeover
-- =========================================================
CREATE TABLE human_takeover
(
    id             BIGSERIAL PRIMARY KEY,
    session_id     BIGINT      NOT NULL REFERENCES chat_session (id),
    lead_id        BIGINT REFERENCES customer_lead (id),
    consultant_id  BIGINT REFERENCES consultant (id),
    status         VARCHAR(24) NOT NULL DEFAULT 'pending',
    trigger_reason VARCHAR(80) NOT NULL,
    note           TEXT,
    started_at     TIMESTAMPTZ,
    closed_at      TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_human_takeover_status ON human_takeover (status);

-- =========================================================
-- 11. knowledge_document
-- =========================================================
CREATE TABLE knowledge_document
(
    id         BIGSERIAL PRIMARY KEY,
    title      VARCHAR(200) NOT NULL,
    doc_type   VARCHAR(40)  NOT NULL,
    version    VARCHAR(32)  NOT NULL DEFAULT 'v1',
    file_url   TEXT,
    status     VARCHAR(24)  NOT NULL DEFAULT 'uploaded',
    enabled    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_by BIGINT REFERENCES "system_user" (id),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_knowledge_document_status ON knowledge_document (status);

-- =========================================================
-- 12. knowledge_chunk
-- =========================================================
CREATE TABLE knowledge_chunk
(
    id          BIGSERIAL PRIMARY KEY,
    document_id BIGINT      NOT NULL REFERENCES knowledge_document (id),
    chunk_index INTEGER     NOT NULL,
    content     TEXT        NOT NULL,
    token_count INTEGER     NOT NULL DEFAULT 0,
    milvus_pk   VARCHAR(120),
    enabled     BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uk_knowledge_chunk ON knowledge_chunk (document_id, chunk_index);
CREATE INDEX idx_knowledge_chunk_milvus ON knowledge_chunk (milvus_pk);

-- =========================================================
-- 13. faq_item
-- =========================================================
CREATE TABLE faq_item
(
    id         BIGSERIAL PRIMARY KEY,
    question   VARCHAR(300) NOT NULL,
    answer     TEXT         NOT NULL,
    category   VARCHAR(80)  NOT NULL,
    priority   INTEGER      NOT NULL DEFAULT 0,
    enabled    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_by BIGINT REFERENCES "system_user" (id),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_faq_item_category ON faq_item (category);

-- =========================================================
-- 14. feedback_record
-- =========================================================
CREATE TABLE feedback_record
(
    id         BIGSERIAL PRIMARY KEY,
    session_id BIGINT      NOT NULL REFERENCES chat_session (id),
    message_id BIGINT REFERENCES chat_message (id),
    rating     VARCHAR(16) NOT NULL,
    comment    TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================
-- 15. prompt_template
-- =========================================================
CREATE TABLE prompt_template
(
    id         BIGSERIAL PRIMARY KEY,
    code       VARCHAR(80)  NOT NULL UNIQUE,
    name       VARCHAR(120) NOT NULL,
    template   TEXT         NOT NULL,
    version    VARCHAR(32)  NOT NULL DEFAULT 'v1',
    enabled    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- =========================================================
-- 16. model_config
-- =========================================================
CREATE TABLE model_config
(
    id         BIGSERIAL PRIMARY KEY,
    config_key VARCHAR(80)  NOT NULL UNIQUE,
    provider   VARCHAR(80)  NOT NULL,
    model_name VARCHAR(120) NOT NULL,
    config     JSONB        NOT NULL DEFAULT '{}',
    enabled    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMIT;