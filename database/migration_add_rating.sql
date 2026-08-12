-- Run this ONLY if you already created vectamind_db before the rating
-- feature was added. If you're setting up fresh, just use schema.sql
-- (it already includes this column) and skip this file.

USE vectamind_db;

ALTER TABLE feedback
    ADD COLUMN rating TINYINT NULL AFTER message,
    ADD CONSTRAINT chk_feedback_rating CHECK (rating IS NULL OR (rating BETWEEN 1 AND 5));
