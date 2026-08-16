-- CampusEats logical database schema
-- Each service exclusively owns its tables.
-- Cross-service references (for example user_id or order_id) are application-level
-- references and intentionally have NO database foreign key across service boundaries.

CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE addresses (
    address_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    address_line VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE restaurants (
    restaurant_id BIGINT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    location VARCHAR(255),
    status VARCHAR(30) NOT NULL
);

CREATE TABLE menus (
    menu_id BIGINT PRIMARY KEY,
    restaurant_id BIGINT NOT NULL,
    name VARCHAR(150) NOT NULL,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
);

CREATE TABLE menu_items (
    item_id BIGINT PRIMARY KEY,
    menu_id BIGINT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description VARCHAR(500),
    price DECIMAL(10,2) NOT NULL,
    available BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (menu_id) REFERENCES menus(menu_id)
);

CREATE TABLE carts (
    cart_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    status VARCHAR(30) NOT NULL
    -- user_id references Accounts Service; no cross-service FK
);

CREATE TABLE cart_items (
    cart_item_id BIGINT PRIMARY KEY,
    cart_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
    -- item_id references Catalogue Service; no cross-service FK
);

CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    address_id BIGINT NOT NULL,
    status VARCHAR(30) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP NOT NULL
    -- user_id/address_id reference Accounts Service; no cross-service FK
);

CREATE TABLE order_items (
    order_item_id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
    -- item_id references Catalogue Service; no cross-service FK
);

CREATE TABLE transactions (
    transaction_id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    status VARCHAR(30) NOT NULL,
    provider_reference VARCHAR(150),
    created_at TIMESTAMP NOT NULL
    -- order_id references Orders Service; no cross-service FK
);

CREATE TABLE refunds (
    refund_id BIGINT PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
);

CREATE TABLE riders (
    rider_id BIGINT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(30),
    status VARCHAR(30) NOT NULL
);

CREATE TABLE assignments (
    assignment_id BIGINT PRIMARY KEY,
    rider_id BIGINT NOT NULL,
    order_id BIGINT NOT NULL,
    status VARCHAR(30) NOT NULL,
    assigned_at TIMESTAMP NOT NULL,
    FOREIGN KEY (rider_id) REFERENCES riders(rider_id)
    -- order_id references Orders Service; no cross-service FK
);

CREATE TABLE message_log (
    message_id BIGINT PRIMARY KEY,
    recipient_user_id BIGINT NOT NULL,
    order_id BIGINT,
    message_type VARCHAR(50) NOT NULL,
    message_text VARCHAR(500) NOT NULL,
    status VARCHAR(30) NOT NULL,
    sent_at TIMESTAMP
    -- recipient_user_id/order_id reference other services; no cross-service FK
);
