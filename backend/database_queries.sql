CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Store BCrypt/Argon2 hash, NEVER plain text
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE files (
    file_hash CHAR(64) PRIMARY KEY, -- SHA-256 is 64 hex characters
    file_name VARCHAR(255) NOT NULL, -- Canonical name (usually the first name it was uploaded with)
    file_size BIGINT NOT NULL, -- Size in bytes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE active_peers (
    peer_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    file_hash CHAR(64) NOT NULL,
    ip_address VARCHAR(45) NOT NULL, -- Supports IPv4 and IPv6
    port INT NOT NULL,
    public_url TEXT,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (file_hash) REFERENCES files(file_hash) ON DELETE CASCADE,
    
    -- Ensure a user is not listed twice for the same file
    UNIQUE (user_id, file_hash) 
);
-- 1. Index for fast searching by filename (e.g., "Find all files with 'Physics'")
-- TRGM index (requires pg_trgm extension) is best for partial matching, 
-- but a standard index works for exact prefix matches.
CREATE INDEX idx_files_name ON files(file_name);

-- 2. Index to quickly find who has a specific file
CREATE INDEX idx_active_peers_hash ON active_peers(file_hash);

-- 3. Index for the Heartbeat Cleanup Job (to quickly find offline users)
CREATE INDEX idx_last_heartbeat ON active_peers(last_heartbeat);