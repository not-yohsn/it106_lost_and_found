-- Lost and Found Tracking System — MySQL schema
-- Run this once in phpMyAdmin (SQL tab) or via the MySQL CLI.

CREATE DATABASE IF NOT EXISTS lost_and_found
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE lost_and_found;

-- 1. USERS
-- Note: existing databases must also run `ALTER TABLE users ADD COLUMN api_token_hash VARCHAR(255) NULL;` before the M2 API will function.
CREATE TABLE IF NOT EXISTS users (
  user_id        INT AUTO_INCREMENT PRIMARY KEY,
  name           VARCHAR(120) NOT NULL,
  email          VARCHAR(120) NOT NULL UNIQUE,
  phone          VARCHAR(20),
  role           ENUM('student','staff','admin') NOT NULL DEFAULT 'student',
  password_hash  VARCHAR(255) NOT NULL,
  api_token_hash VARCHAR(255) NULL,
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. FINDERS (people who turn in items, may be unregistered)
CREATE TABLE IF NOT EXISTS finders (
  finder_id  INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(120) NOT NULL,
  email      VARCHAR(120),
  phone      VARCHAR(20),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. LOST REPORTS
CREATE TABLE IF NOT EXISTS lost_reports (
  report_id   INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT NOT NULL,
  item_name   VARCHAR(120) NOT NULL,
  description TEXT,
  category    VARCHAR(60),
  location    VARCHAR(120),
  date_lost   DATE,
  photo_path  VARCHAR(255),
  status      ENUM('reported','matched','claimed','closed') DEFAULT 'reported',
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 4. FOUND ITEMS
CREATE TABLE IF NOT EXISTS found_items (
  item_id        INT AUTO_INCREMENT PRIMARY KEY,
  finder_id      INT,
  logged_by      INT,
  item_name      VARCHAR(120) NOT NULL,
  description    TEXT,
  category       VARCHAR(60),
  location_found VARCHAR(120),
  date_found     DATE,
  photo_path     VARCHAR(255),
  status         ENUM('logged','matched','released') DEFAULT 'logged',
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (finder_id) REFERENCES finders(finder_id) ON DELETE SET NULL,
  FOREIGN KEY (logged_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 5. MATCHES (1:1 between a lost report and a found item)
CREATE TABLE IF NOT EXISTS matches (
  match_id          INT AUTO_INCREMENT PRIMARY KEY,
  lost_report_id    INT NOT NULL UNIQUE,
  found_item_id     INT NOT NULL UNIQUE,
  matched_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
  confidence_score  FLOAT,
  FOREIGN KEY (lost_report_id) REFERENCES lost_reports(report_id) ON DELETE CASCADE,
  FOREIGN KEY (found_item_id)  REFERENCES found_items(item_id)    ON DELETE CASCADE
);

-- 6. CLAIMS
CREATE TABLE IF NOT EXISTS claims (
  claim_id     INT AUTO_INCREMENT PRIMARY KEY,
  match_id     INT NOT NULL,
  claimant_id  INT NOT NULL,
  verified_by  INT,
  status       ENUM('pending','approved','rejected','released') DEFAULT 'pending',
  notes        TEXT,
  submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  resolved_at  DATETIME,
  FOREIGN KEY (match_id)    REFERENCES matches(match_id) ON DELETE CASCADE,
  FOREIGN KEY (claimant_id) REFERENCES users(user_id),
  FOREIGN KEY (verified_by) REFERENCES users(user_id)
);

-- 7. NOTIFICATIONS (in-app)
CREATE TABLE IF NOT EXISTS notifications (
  notification_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id         INT NOT NULL,
  title           VARCHAR(160) NOT NULL,
  body            TEXT,
  link            VARCHAR(255),
  is_read         BOOLEAN DEFAULT FALSE,
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_unread (user_id, is_read),
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
