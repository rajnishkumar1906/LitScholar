-- Only run this if your user_book_views / user_activity had user_id as UUID.
-- If you already created tables with user_id BIGINT REFERENCES users(id), skip this file.
-- users.id is BIGSERIAL (BIGINT); these columns must match.

-- user_book_views
ALTER TABLE user_book_views DROP COLUMN IF EXISTS user_id;
ALTER TABLE user_book_views ADD COLUMN user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE;

-- user_activity
ALTER TABLE user_activity DROP COLUMN IF EXISTS user_id;
ALTER TABLE user_activity ADD COLUMN user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE;
