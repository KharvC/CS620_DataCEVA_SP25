DROP TABLE IF EXISTS ChatLogs;

CREATE TABLE ChatLogs(
    user_input TEXT,
    ai_text TEXT,
    ai_img_id SERIAL PRIMARY KEY,
    ai_img_name VARCHAR(255),
    ai_img_data BYTEA
);