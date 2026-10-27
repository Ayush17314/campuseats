-- CampusEats Catalogue Service — MySQL Schema & Seed Data
-- Assignment 7 of 12: Build one CampusEats service in GraphQL

CREATE DATABASE IF NOT EXISTS campuseats;
USE campuseats;

-- 1. Table Definition
CREATE TABLE IF NOT EXISTS dishes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    available BOOLEAN NOT NULL DEFAULT TRUE,
    category VARCHAR(50) DEFAULT 'General',
    description VARCHAR(255)
);

-- 2. Clean previous records for repeatable seeding
TRUNCATE TABLE dishes;

-- 3. Seed Rows (Initial Menu Items)
INSERT INTO dishes (name, price, available, category, description) VALUES
('Paneer Tikka Roll', 90.00, TRUE, 'Rolls', 'Grilled cottage cheese wrapped in fresh wheat paratha with mint chutney'),
('Veg Dum Biryani', 130.00, TRUE, 'Rice', 'Aromatic basmati rice cooked with fresh seasonal vegetables and spices'),
('Masala Dosa', 65.00, TRUE, 'South Indian', 'Crisp rice crepe stuffed with tempered mashed potatoes, served with sambar'),
('Cold Coffee Frappe', 45.00, FALSE, 'Beverages', 'Chilled blended milk coffee topped with chocolate syrup');
