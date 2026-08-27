-- ============================================================
-- AgriSense (VectaMind) - AI-Driven Vegetable Production and
-- Price Optimization System - Sri Lanka - MySQL Database
-- Extended for KivyMD mobile app (Farmer / Trader / Policymaker)
-- ============================================================

DROP DATABASE IF EXISTS vectamind_db;
CREATE DATABASE vectamind_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE vectamind_db;

-- ============================================================
-- REGION
-- ============================================================
CREATE TABLE region (
    region_id INT AUTO_INCREMENT PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    CONSTRAINT uq_region UNIQUE (region_name, district)
) ENGINE=InnoDB;

-- ============================================================
-- USER  (role now: farmer / trader / policymaker / admin)
-- Added email-confirmation workflow fields
-- ============================================================
CREATE TABLE user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,          -- bcrypt hash
    user_type ENUM('farmer', 'trader', 'policymaker', 'admin') NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    region_id INT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,       -- becomes TRUE after email confirm
    confirmation_token VARCHAR(255) NULL,
    token_created_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_region FOREIGN KEY (region_id)
        REFERENCES region(region_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- USER PREFERENCES (selected crops + notification pref)
-- ============================================================
CREATE TABLE user_preferences (
    user_id INT PRIMARY KEY,
    notification_settings TEXT DEFAULT 'enabled',
    preferred_crops TEXT,                    -- comma separated crop_ids
    CONSTRAINT fk_preferences_user FOREIGN KEY (user_id)
        REFERENCES user(user_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- CROP  (fixed 5: Okra, Cabbage, Beans, Carrots, Leeks)
-- ============================================================
CREATE TABLE crop (
    crop_id INT AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- ============================================================
-- PRODUCTION
-- ============================================================
CREATE TABLE production (
    production_id INT AUTO_INCREMENT PRIMARY KEY,
    season VARCHAR(50) NOT NULL,             -- Maha / Yala
    quantity DECIMAL(12,2) NOT NULL,         -- hectares/kg basis, see column below
    unit VARCHAR(20) NOT NULL DEFAULT 'kg',
    record_date DATE NOT NULL,
    crop_id INT NOT NULL,
    region_id INT NOT NULL,
    CONSTRAINT chk_production_quantity CHECK (quantity >= 0),
    CONSTRAINT fk_production_crop FOREIGN KEY (crop_id)
        REFERENCES crop(crop_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_production_region FOREIGN KEY (region_id)
        REFERENCES region(region_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- PRICE  (LKR per kg)
-- ============================================================
CREATE TABLE price (
    price_id INT AUTO_INCREMENT PRIMARY KEY,
    price DECIMAL(10,2) NOT NULL,            -- LKR per kg
    date DATE NOT NULL,
    crop_id INT NOT NULL,
    region_id INT NOT NULL,
    CONSTRAINT chk_price CHECK (price >= 0),
    CONSTRAINT fk_price_crop FOREIGN KEY (crop_id)
        REFERENCES crop(crop_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_price_region FOREIGN KEY (region_id)
        REFERENCES region(region_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- CLIMATE (feature source for the models)
-- ============================================================
CREATE TABLE climate (
    climate_id INT AUTO_INCREMENT PRIMARY KEY,
    record_date DATE NOT NULL,
    region_id INT NOT NULL,
    rainfall_mm DECIMAL(8,2),
    avg_temp_c DECIMAL(5,2),
    humidity_pct DECIMAL(5,2),
    CONSTRAINT fk_climate_region FOREIGN KEY (region_id)
        REFERENCES region(region_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- PREDICTION  (price / production, output of trained models)
-- ============================================================
CREATE TABLE prediction (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    prediction_type VARCHAR(50) NOT NULL,     -- price | production
    prediction_value DECIMAL(12,2) NOT NULL,
    prediction_date DATE NOT NULL,
    crop_id INT NOT NULL,
    region_id INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_prediction_type CHECK (prediction_type IN ('price', 'production')),
    CONSTRAINT fk_prediction_crop FOREIGN KEY (crop_id)
        REFERENCES crop(crop_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_prediction_region FOREIGN KEY (region_id)
        REFERENCES region(region_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- ALERT
-- ============================================================
CREATE TABLE alert (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,          -- price_spike | price_drop | oversupply | shortage
    message TEXT NOT NULL,
    prediction_id INT NULL,
    user_id INT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alert_prediction FOREIGN KEY (prediction_id)
        REFERENCES prediction(prediction_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_alert_user FOREIGN KEY (user_id)
        REFERENCES user(user_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- RECOMMENDATION
-- ============================================================
CREATE TABLE recommendation (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    user_id INT NOT NULL,
    prediction_id INT NULL,
    region_id INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_recommendation_user FOREIGN KEY (user_id)
        REFERENCES user(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_recommendation_prediction FOREIGN KEY (prediction_id)
        REFERENCES prediction(prediction_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_recommendation_region FOREIGN KEY (region_id)
        REFERENCES region(region_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- FEEDBACK  (user -> admin)
-- ============================================================
CREATE TABLE feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    rating TINYINT NULL,                          -- 1 to 5 stars
    user_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'new',   -- new | reviewed
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_feedback_rating CHECK (rating IS NULL OR (rating BETWEEN 1 AND 5)),
    CONSTRAINT fk_feedback_user FOREIGN KEY (user_id)
        REFERENCES user(user_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_region_district ON region(district);
CREATE INDEX idx_user_region ON user(region_id);
CREATE INDEX idx_user_type ON user(user_type);
CREATE INDEX idx_production_crop_region ON production(crop_id, region_id);
CREATE INDEX idx_price_crop_region_date ON price(crop_id, region_id, date);
CREATE INDEX idx_climate_region_date ON climate(region_id, record_date);
CREATE INDEX idx_prediction_crop_date ON prediction(crop_id, prediction_date);
CREATE INDEX idx_alert_user ON alert(user_id);
CREATE INDEX idx_recommendation_user ON recommendation(user_id);
CREATE INDEX idx_feedback_user ON feedback(user_id);

-- ============================================================
-- SEED: crops (fixed list) + Matale/Kandy regions
-- ============================================================
INSERT INTO crop (crop_name, category) VALUES
('Okra', 'Vegetable'),
('Cabbage', 'Vegetable'),
('Beans', 'Vegetable'),
('Carrots', 'Vegetable'),
('Leeks', 'Vegetable');

INSERT INTO region (region_name, district) VALUES
('Matale Region', 'Matale'),
('Kandy Region', 'Kandy');

SHOW TABLES;
-- ============================================================
-- END OF SCHEMA
-- ============================================================
