# Database migrations

Your schema uses `users.id BIGSERIAL` and `user_id BIGINT` in `user_book_views`, `user_activity`, `user_reading_profile`, and `refresh_tokens`. The backend is aligned to that.

## fix_user_id_to_integer.sql

**Skip this** if you already created tables with `user_id BIGINT` (as in your main schema).

**Run only when:** You previously had `user_book_views.user_id` or `user_activity.user_id` as UUID and see errors like  
`invalid UUID '4': length must be between 32..36 characters`.

**What it does:** Drops and re-adds those columns as `BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE` to match `users.id`.
