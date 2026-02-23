-- =====================================================
-- Laundry Management System Database Schema
-- MySQL Implementation with Auto-Increment IDs
-- =====================================================

-- Drop database if exists and create new one
DROP DATABASE IF EXISTS laundry_management_system;
CREATE DATABASE laundry_management_system;
USE laundry_management_system;

-- =====================================================
-- Table: users
-- Custom user model for authentication and role management
-- =====================================================
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    role ENUM('superadmin', 'admin', 'employee', 'client') NOT NULL DEFAULT 'client',
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP NULL,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by BIGINT NULL,
    
    -- Foreign key for self-reference (who updated this user)
    CONSTRAINT fk_users_updated_by 
        FOREIGN KEY (updated_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    -- Indexes for performance
    INDEX idx_users_role (role),
    INDEX idx_users_email (email),
    INDEX idx_users_is_active (is_active),
    INDEX idx_users_date_joined (date_joined)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: customers
-- Extended profile information for client users
-- =====================================================
CREATE TABLE customers (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    whatsapp_number VARCHAR(20),
    address TEXT NOT NULL,
    preferred_contact_method VARCHAR(20) DEFAULT 'phone',
    notes TEXT,
    total_orders INT DEFAULT 0,
    total_spent DECIMAL(12, 2) DEFAULT 0,
    last_order_date TIMESTAMP NULL,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by BIGINT,
    
    -- Foreign key constraints
    CONSTRAINT fk_customers_user 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_customers_created_by 
        FOREIGN KEY (created_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT fk_customers_updated_by 
        FOREIGN KEY (updated_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT customers_phone_number_key UNIQUE (phone_number),
    CONSTRAINT customers_whatsapp_number_key UNIQUE (whatsapp_number),
    
    -- Indexes for customer queries
    INDEX idx_customers_user_id (user_id),
    INDEX idx_customers_phone (phone_number),
    INDEX idx_customers_created_by (created_by),
    INDEX idx_customers_total_orders (total_orders DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: services
-- Laundry service types and pricing
-- =====================================================
CREATE TABLE services (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(50) DEFAULT 'per item',
    category VARCHAR(50),
    estimated_days INT DEFAULT 2,
    is_active BOOLEAN DEFAULT TRUE,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by BIGINT,
    
    -- Foreign key constraints
    CONSTRAINT fk_services_created_by 
        FOREIGN KEY (created_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT fk_services_updated_by 
        FOREIGN KEY (updated_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT services_name_key UNIQUE (name),
    CONSTRAINT services_price_positive CHECK (price >= 0),
    
    -- Indexes for services
    INDEX idx_services_is_active (is_active),
    INDEX idx_services_category (category),
    INDEX idx_services_price (price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: orders
-- Main order tracking table
-- =====================================================
CREATE TABLE orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id BIGINT NOT NULL,
    assigned_to BIGINT,
    order_status ENUM('pending', 'in_progress', 'ready', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
    payment_status ENUM('pending', 'partially_paid', 'paid') NOT NULL DEFAULT 'pending',
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0,
    amount_paid DECIMAL(12, 2) NOT NULL DEFAULT 0,
    discount_amount DECIMAL(12, 2) DEFAULT 0,
    delivery_notes TEXT,
    special_instructions TEXT,
    pickup_date DATE,
    delivery_date DATE,
    estimated_completion_date DATE,
    completed_at TIMESTAMP NULL,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by BIGINT,
    
    -- Foreign key constraints
    CONSTRAINT fk_orders_customer 
        FOREIGN KEY (customer_id) 
        REFERENCES customers(id) 
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_orders_assigned_to 
        FOREIGN KEY (assigned_to) 
        REFERENCES users(id) 
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_orders_created_by 
        FOREIGN KEY (created_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT fk_orders_updated_by 
        FOREIGN KEY (updated_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT orders_total_amount_positive CHECK (total_amount >= 0),
    CONSTRAINT orders_amount_paid_valid CHECK (amount_paid >= 0 AND amount_paid <= total_amount),
    CONSTRAINT orders_discount_valid CHECK (discount_amount >= 0 AND discount_amount <= total_amount),
    
    -- Comprehensive indexes for orders
    INDEX idx_orders_customer_id (customer_id),
    INDEX idx_orders_assigned_to (assigned_to),
    INDEX idx_orders_order_status (order_status),
    INDEX idx_orders_payment_status (payment_status),
    INDEX idx_orders_created_at (created_at),
    INDEX idx_orders_created_by (created_by),
    INDEX idx_orders_completion_date (estimated_completion_date),
    INDEX idx_orders_pickup_date (pickup_date),
    INDEX idx_orders_amount_range (total_amount, amount_paid),
    
    -- Composite indexes for common queries
    INDEX idx_orders_customer_status (customer_id, order_status),
    INDEX idx_orders_staff_status (assigned_to, order_status),
    INDEX idx_orders_date_status (created_at, order_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: order_items
-- Individual items within an order
-- =====================================================
CREATE TABLE order_items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    service_id BIGINT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    description TEXT,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_order_items_order 
        FOREIGN KEY (order_id) 
        REFERENCES orders(id) 
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_order_items_service 
        FOREIGN KEY (service_id) 
        REFERENCES services(id) 
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    
    -- Constraints
    CONSTRAINT order_items_quantity_positive CHECK (quantity > 0),
    CONSTRAINT order_items_unit_price_positive CHECK (unit_price >= 0),
    CONSTRAINT order_items_subtotal_correct CHECK (subtotal = quantity * unit_price),
    
    -- Indexes for order items
    INDEX idx_order_items_order_id (order_id),
    INDEX idx_order_items_service_id (service_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: payments
-- Payment transaction records
-- =====================================================
CREATE TABLE payments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    reference VARCHAR(100) UNIQUE NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    status ENUM('success', 'failed', 'pending', 'abandoned') NOT NULL DEFAULT 'pending',
    payment_method ENUM('paystack', 'cash', 'bank_transfer', 'ussd') NOT NULL,
    transaction_id VARCHAR(100),
    payer_phone VARCHAR(20),
    currency VARCHAR(3) DEFAULT 'NGN',
    fees DECIMAL(12, 2) DEFAULT 0,
    metadata JSON,
    verified_at TIMESTAMP NULL,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by BIGINT,
    
    -- Foreign key constraints
    CONSTRAINT fk_payments_order 
        FOREIGN KEY (order_id) 
        REFERENCES orders(id) 
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_payments_created_by 
        FOREIGN KEY (created_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT fk_payments_updated_by 
        FOREIGN KEY (updated_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT payments_amount_positive CHECK (amount > 0),
    CONSTRAINT payments_fees_non_negative CHECK (fees >= 0),
    
    -- Indexes for payments
    INDEX idx_payments_order_id (order_id),
    INDEX idx_payments_reference (reference),
    INDEX idx_payments_status (status),
    INDEX idx_payments_method (payment_method),
    INDEX idx_payments_created_at (created_at),
    INDEX idx_payments_created_by (created_by),
    INDEX idx_payments_verified_at (verified_at),
    
    -- Composite index for reconciliation
    INDEX idx_payments_status_date (status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: order_status_history
-- Audit trail for order status changes
-- =====================================================
CREATE TABLE order_status_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    previous_status ENUM('pending', 'in_progress', 'ready', 'completed', 'cancelled'),
    new_status ENUM('pending', 'in_progress', 'ready', 'completed', 'cancelled') NOT NULL,
    changed_by BIGINT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_status_history_order 
        FOREIGN KEY (order_id) 
        REFERENCES orders(id) 
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_status_history_changed_by 
        FOREIGN KEY (changed_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    -- Indexes for status history
    INDEX idx_status_history_order (order_id),
    INDEX idx_status_history_changed_by (changed_by),
    INDEX idx_status_history_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: inventory_items
-- Track laundry items inventory (optional expansion)
-- =====================================================
CREATE TABLE inventory_items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    quantity_in_stock INT DEFAULT 0,
    reorder_level INT DEFAULT 10,
    unit_cost DECIMAL(10, 2),
    selling_price DECIMAL(10, 2),
    supplier_info TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by BIGINT,
    
    CONSTRAINT fk_inventory_created_by 
        FOREIGN KEY (created_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT fk_inventory_updated_by 
        FOREIGN KEY (updated_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT inventory_items_quantity_non_negative CHECK (quantity_in_stock >= 0),
    CONSTRAINT inventory_items_reorder_level_positive CHECK (reorder_level >= 0),
    
    INDEX idx_inventory_items_category (category),
    INDEX idx_inventory_items_reorder (quantity_in_stock, reorder_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: notifications
-- User notification system
-- =====================================================
CREATE TABLE notifications (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    related_entity_type VARCHAR(50),
    related_entity_id BIGINT,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_notifications_user 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT fk_notifications_created_by 
        FOREIGN KEY (created_by) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
    
    INDEX idx_notifications_user (user_id),
    INDEX idx_notifications_user_unread (user_id, is_read),
    INDEX idx_notifications_created (created_at),
    INDEX idx_notifications_created_by (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Functions and Triggers for Business Logic
-- =====================================================

-- Delimiter change for trigger creation
DELIMITER $$

-- Trigger to generate order number
CREATE TRIGGER generate_order_number
    BEFORE INSERT ON orders
    FOR EACH ROW
BEGIN
    DECLARE year_prefix VARCHAR(4);
    DECLARE sequence_num INT;
    
    SET year_prefix = DATE_FORMAT(CURDATE(), '%Y');
    
    -- Get the next sequence number for this year
    SELECT COALESCE(MAX(CAST(SUBSTRING_INDEX(order_number, '-', -1) AS UNSIGNED)), 0) + 1
    INTO sequence_num
    FROM orders
    WHERE order_number LIKE CONCAT('LND-', year_prefix, '-%');
    
    IF sequence_num IS NULL OR sequence_num = 0 THEN
        SET sequence_num = 1;
    END IF;
    
    SET NEW.order_number = CONCAT('LND-', year_prefix, '-', LPAD(sequence_num, 6, '0'));
END$$

-- Trigger to update order totals when items are inserted
CREATE TRIGGER update_order_totals_after_insert
    AFTER INSERT ON order_items
    FOR EACH ROW
BEGIN
    UPDATE orders 
    SET total_amount = (
        SELECT COALESCE(SUM(subtotal), 0)
        FROM order_items
        WHERE order_id = NEW.order_id
    )
    WHERE id = NEW.order_id;
END$$

-- Trigger to update order totals when items are updated
CREATE TRIGGER update_order_totals_after_update
    AFTER UPDATE ON order_items
    FOR EACH ROW
BEGIN
    UPDATE orders 
    SET total_amount = (
        SELECT COALESCE(SUM(subtotal), 0)
        FROM order_items
        WHERE order_id = NEW.order_id
    )
    WHERE id = NEW.order_id;
END$$

-- Trigger to update order totals when items are deleted
CREATE TRIGGER update_order_totals_after_delete
    AFTER DELETE ON order_items
    FOR EACH ROW
BEGIN
    UPDATE orders 
    SET total_amount = (
        SELECT COALESCE(SUM(subtotal), 0)
        FROM order_items
        WHERE order_id = OLD.order_id
    )
    WHERE id = OLD.order_id;
END$$

-- Trigger to update customer stats when order is created
CREATE TRIGGER update_customer_stats_after_order_insert
    AFTER INSERT ON orders
    FOR EACH ROW
BEGIN
    UPDATE customers 
    SET 
        total_orders = total_orders + 1,
        total_spent = total_spent + NEW.total_amount,
        last_order_date = NEW.created_at
    WHERE id = NEW.customer_id;
END$$

-- Trigger to update order payment status after payment insert
CREATE TRIGGER update_order_payment_status
    AFTER INSERT ON payments
    FOR EACH ROW
BEGIN
    DECLARE order_total DECIMAL(12, 2);
    DECLARE total_paid DECIMAL(12, 2);
    
    IF NEW.status = 'success' THEN
        -- Get order total
        SELECT total_amount INTO order_total
        FROM orders
        WHERE id = NEW.order_id;
        
        -- Calculate total paid for this order
        SELECT COALESCE(SUM(amount), 0) INTO total_paid
        FROM payments
        WHERE order_id = NEW.order_id AND status = 'success';
        
        -- Update order amount_paid and payment_status
        UPDATE orders
        SET 
            amount_paid = total_paid,
            payment_status = CASE 
                WHEN total_paid <= 0 THEN 'pending'
                WHEN total_paid < order_total THEN 'partially_paid'
                WHEN total_paid >= order_total THEN 'paid'
                ELSE payment_status
            END
        WHERE id = NEW.order_id;
    END IF;
END$$

-- Trigger to log order status changes
CREATE TRIGGER log_order_status_change
    AFTER UPDATE ON orders
    FOR EACH ROW
BEGIN
    IF OLD.order_status != NEW.order_status THEN
        INSERT INTO order_status_history (
            order_id, previous_status, new_status, changed_by
        ) VALUES (
            NEW.id, OLD.order_status, NEW.order_status, NEW.updated_by
        );
    END IF;
END$$

DELIMITER ;

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- View: order_summary
CREATE VIEW order_summary AS
SELECT 
    o.id,
    o.order_number,
    CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
    c.phone_number,
    o.total_amount,
    o.amount_paid,
    o.total_amount - o.amount_paid AS balance_due,
    o.order_status,
    o.payment_status,
    o.estimated_completion_date,
    o.created_at,
    CONCAT(assigned.first_name, ' ', assigned.last_name) AS assigned_staff,
    CONCAT(creator.first_name, ' ', creator.last_name) AS created_by_name
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN users u ON c.user_id = u.id
LEFT JOIN users assigned ON o.assigned_to = assigned.id
LEFT JOIN users creator ON o.created_by = creator.id;

-- View: customer_payment_history
CREATE VIEW customer_payment_history AS
SELECT 
    c.id AS customer_id,
    CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
    o.order_number,
    p.reference,
    p.amount,
    p.payment_method,
    p.status,
    p.created_at AS payment_date,
    CONCAT(creator.first_name, ' ', creator.last_name) AS recorded_by
FROM payments p
JOIN orders o ON p.order_id = o.id
JOIN customers c ON o.customer_id = c.id
JOIN users u ON c.user_id = u.id
LEFT JOIN users creator ON p.created_by = creator.id
WHERE p.status = 'success';

-- View: daily_revenue
CREATE VIEW daily_revenue AS
SELECT 
    DATE(created_at) AS revenue_date,
    COUNT(DISTINCT order_id) AS transaction_count,
    SUM(amount) AS total_revenue,
    SUM(CASE WHEN payment_method = 'paystack' THEN amount ELSE 0 END) as online_payments,
    SUM(CASE WHEN payment_method = 'cash' THEN amount ELSE 0 END) as cash_payments
FROM payments
WHERE status = 'success'
GROUP BY DATE(created_at)
ORDER BY revenue_date DESC;

-- View: staff_performance
CREATE VIEW staff_performance AS
SELECT 
    u.id AS staff_id,
    CONCAT(u.first_name, ' ', u.last_name) AS staff_name,
    u.role,
    COUNT(DISTINCT o.id) AS orders_handled,
    SUM(CASE WHEN o.order_status = 'completed' THEN 1 ELSE 0 END) AS orders_completed,
    SUM(o.total_amount) AS revenue_generated,
    AVG(o.total_amount) AS avg_order_value
FROM users u
LEFT JOIN orders o ON u.id = o.assigned_to
WHERE u.role IN ('admin', 'employee')
GROUP BY u.id, u.first_name, u.last_name, u.role;

-- View: customer_lifetime_value
CREATE VIEW customer_lifetime_value AS
SELECT 
    c.id AS customer_id,
    CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
    c.phone_number,
    c.total_orders,
    c.total_spent,
    c.last_order_date,
    ROUND(c.total_spent / NULLIF(c.total_orders, 0), 2) AS avg_order_value,
    DATEDIFF(CURDATE(), c.last_order_date) AS days_since_last_order,
    CONCAT(creator.first_name, ' ', creator.last_name) AS created_by
FROM customers c
JOIN users u ON c.user_id = u.id
LEFT JOIN users creator ON c.created_by = creator.id;

-- View: pending_orders_summary
CREATE VIEW pending_orders_summary AS
SELECT 
    o.order_status,
    COUNT(*) AS order_count,
    SUM(o.total_amount) AS total_value,
    SUM(o.total_amount - o.amount_paid) AS outstanding_balance
FROM orders o
WHERE o.order_status IN ('pending', 'in_progress')
GROUP BY o.order_status;

-- =====================================================
-- Stored Procedures for Common Operations
-- =====================================================

DELIMITER $$

-- Procedure: Get dashboard metrics based on user role
CREATE PROCEDURE GetDashboardMetrics(
    IN p_user_role VARCHAR(20),
    IN p_user_id BIGINT
)
BEGIN
    IF p_user_role = 'superadmin' THEN
        -- Superadmin sees everything
        SELECT 
            (SELECT COUNT(*) FROM users WHERE role = 'client') AS total_customers,
            (SELECT COUNT(*) FROM users WHERE role IN ('admin', 'employee')) AS total_staff,
            (SELECT COUNT(*) FROM orders) AS total_orders,
            (SELECT COALESCE(SUM(total_amount), 0) FROM orders) AS total_revenue,
            (SELECT COUNT(*) FROM orders WHERE DATE(created_at) = CURDATE()) AS today_orders,
            (SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE DATE(created_at) = CURDATE()) AS today_revenue,
            (SELECT COUNT(*) FROM orders WHERE order_status = 'pending') AS pending_orders,
            (SELECT COUNT(*) FROM orders WHERE order_status = 'in_progress') AS in_progress_orders,
            (SELECT COUNT(*) FROM orders WHERE order_status = 'ready') AS ready_for_pickup,
            (SELECT COALESCE(SUM(total_amount - amount_paid), 0) FROM orders WHERE payment_status != 'paid') AS total_outstanding;
    ELSEIF p_user_role = 'admin' THEN
        -- Admin sees all orders but limited staff view
        SELECT 
            (SELECT COUNT(*) FROM users WHERE role = 'client') AS total_customers,
            (SELECT COUNT(*) FROM orders) AS total_orders,
            (SELECT COALESCE(SUM(total_amount), 0) FROM orders) AS total_revenue,
            (SELECT COUNT(*) FROM orders WHERE DATE(created_at) = CURDATE()) AS today_orders,
            (SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE DATE(created_at) = CURDATE()) AS today_revenue,
            (SELECT COUNT(*) FROM orders WHERE order_status = 'pending') AS pending_orders,
            (SELECT COUNT(*) FROM orders WHERE order_status = 'ready') AS ready_for_pickup;
    ELSEIF p_user_role = 'employee' THEN
        -- Employee sees only their assigned orders
        SELECT 
            (SELECT COUNT(*) FROM orders WHERE assigned_to = p_user_id) AS my_orders,
            (SELECT COUNT(*) FROM orders WHERE assigned_to = p_user_id AND order_status = 'pending') AS my_pending,
            (SELECT COUNT(*) FROM orders WHERE assigned_to = p_user_id AND order_status = 'in_progress') AS my_in_progress,
            (SELECT COUNT(*) FROM orders WHERE assigned_to = p_user_id AND DATE(created_at) = CURDATE()) AS my_today_orders,
            (SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE assigned_to = p_user_id) AS my_revenue;
    END IF;
END$$

-- Procedure: Process a payment (with transaction support)
CREATE PROCEDURE ProcessPayment(
    IN p_order_id BIGINT,
    IN p_amount DECIMAL(12, 2),
    IN p_method VARCHAR(20),
    IN p_reference VARCHAR(100),
    IN p_created_by BIGINT,
    IN p_payer_phone VARCHAR(20)
)
BEGIN
    DECLARE v_order_total DECIMAL(12, 2);
    DECLARE v_current_paid DECIMAL(12, 2);
    DECLARE v_new_paid DECIMAL(12, 2);
    DECLARE v_payment_id BIGINT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    -- Start transaction
    START TRANSACTION;
    
    -- Get order total and current paid amount (lock the row)
    SELECT total_amount, amount_paid INTO v_order_total, v_current_paid
    FROM orders
    WHERE id = p_order_id
    FOR UPDATE;
    
    -- Calculate new paid amount
    SET v_new_paid = v_current_paid + p_amount;
    
    -- Insert payment record
    INSERT INTO payments (
        order_id, reference, amount, status, 
        payment_method, created_by, payer_phone
    ) VALUES (
        p_order_id, p_reference, p_amount, 'success',
        p_method, p_created_by, p_payer_phone
    );
    
    SET v_payment_id = LAST_INSERT_ID();
    
    -- Update order
    UPDATE orders
    SET 
        amount_paid = v_new_paid,
        payment_status = CASE 
            WHEN v_new_paid <= 0 THEN 'pending'
            WHEN v_new_paid < v_order_total THEN 'partially_paid'
            WHEN v_new_paid >= v_order_total THEN 'paid'
        END,
        updated_by = p_created_by
    WHERE id = p_order_id;
    
    -- Commit transaction
    COMMIT;
    
    -- Return payment details
    SELECT v_payment_id AS payment_id, 'Payment processed successfully' AS message;
END$$

-- Procedure: Get customer order history
CREATE PROCEDURE GetCustomerOrderHistory(
    IN p_customer_id BIGINT
)
BEGIN
    SELECT 
        o.id,
        o.order_number,
        o.total_amount,
        o.amount_paid,
        o.total_amount - o.amount_paid AS balance,
        o.order_status,
        o.payment_status,
        o.created_at,
        o.estimated_completion_date,
        o.completed_at,
        COUNT(oi.id) AS total_items,
        GROUP_CONCAT(DISTINCT oi.item_name SEPARATOR ', ') AS items_summary,
        CONCAT(creator.first_name, ' ', creator.last_name) AS taken_by
    FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN users creator ON o.created_by = creator.id
    WHERE o.customer_id = p_customer_id
    GROUP BY o.id
    ORDER BY o.created_at DESC;
END$$

-- Procedure: Get revenue report by date range
CREATE PROCEDURE GetRevenueReport(
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    SELECT 
        DATE(p.created_at) AS transaction_date,
        p.payment_method,
        COUNT(*) AS transaction_count,
        SUM(p.amount) AS total_amount,
        AVG(p.amount) AS average_amount,
        CONCAT(creator.first_name, ' ', creator.last_name) AS recorded_by
    FROM payments p
    LEFT JOIN users creator ON p.created_by = creator.id
    WHERE p.status = 'success'
        AND DATE(p.created_at) BETWEEN p_start_date AND p_end_date
    GROUP BY DATE(p.created_at), p.payment_method, creator.id
    ORDER BY transaction_date DESC, payment_method;
    
    -- Also return summary
    SELECT 
        COUNT(DISTINCT order_id) AS unique_orders,
        COUNT(*) AS total_transactions,
        SUM(amount) AS grand_total,
        MIN(amount) AS min_transaction,
        MAX(amount) AS max_transaction
    FROM payments
    WHERE status = 'success'
        AND DATE(created_at) BETWEEN p_start_date AND p_end_date;
END$$

DELIMITER ;

-- =====================================================
-- Initial Data Seed
-- =====================================================

-- Insert default services
INSERT INTO services (name, description, price, category, estimated_days) VALUES
    ('Wash & Fold', 'Regular washing and folding', 500.00, 'Washing', 2),
    ('Wash & Iron', 'Washing with professional ironing', 800.00, 'Washing', 2),
    ('Dry Cleaning', 'Professional dry cleaning service', 1500.00, 'Specialty', 3),
    ('Iron Only', 'Professional ironing service only', 300.00, 'Ironing', 1),
    ('Stain Removal', 'Specialized stain treatment', 1000.00, 'Specialty', 3),
    ('Curtain Cleaning', 'Special care for curtains', 2500.00, 'Home Items', 4),
    ('Bed Sheet Set', 'Complete bed sheet cleaning', 1200.00, 'Home Items', 2),
    ('Shoe Cleaning', 'Professional shoe cleaning', 800.00, 'Specialty', 2);

-- Create superadmin user (password will be set in application)
INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_superuser, is_staff) 
VALUES (
    'superadmin',
    'admin@laundry.com',
    'temp_password_hash_change_me',  -- This should be replaced with proper bcrypt hash
    'System',
    'Administrator',
    'superadmin',
    TRUE,
    TRUE
);

-- Update the superadmin's updated_by to self
UPDATE users SET updated_by = id WHERE username = 'superadmin';

-- =====================================================
-- Create Indexes for Foreign Key Performance
-- =====================================================

-- Additional indexes for better join performance
CREATE INDEX idx_orders_customer_id_created ON orders(customer_id, created_at);
CREATE INDEX idx_orders_created_by_created ON orders(created_by, created_at);
CREATE INDEX idx_payments_order_id_created ON payments(order_id, created_at);
CREATE INDEX idx_payments_created_by_created ON payments(created_by, created_at);
CREATE INDEX idx_order_items_order_id_service ON order_items(order_id, service_id);
CREATE INDEX idx_customers_created_by_created ON customers(created_by, created_at);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read, created_at);

-- =====================================================
-- Create Application User and Grant Permissions
-- =====================================================

-- Create application user (run these separately as root with appropriate password)
-- CREATE USER 'laundry_app'@'localhost' IDENTIFIED BY 'your_secure_password_here';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON laundry_management_system.* TO 'laundry_app'@'localhost';
-- GRANT EXECUTE ON PROCEDURE laundry_management_system.GetDashboardMetrics TO 'laundry_app'@'localhost';
-- GRANT EXECUTE ON PROCEDURE laundry_management_system.ProcessPayment TO 'laundry_app'@'localhost';
-- GRANT EXECUTE ON PROCEDURE laundry_management_system.GetCustomerOrderHistory TO 'laundry_app'@'localhost';
-- GRANT EXECUTE ON PROCEDURE laundry_management_system.GetRevenueReport TO 'laundry_app'@'localhost';
-- GRANT SELECT ON laundry_management_system.order_summary TO 'laundry_app'@'localhost';
-- GRANT SELECT ON laundry_management_system.customer_payment_history TO 'laundry_app'@'localhost';
-- GRANT SELECT ON laundry_management_system.daily_revenue TO 'laundry_app'@'localhost';
-- GRANT SELECT ON laundry_management_system.staff_performance TO 'laundry_app'@'localhost';
-- GRANT SELECT ON laundry_management_system.customer_lifetime_value TO 'laundry_app'@'localhost';
-- GRANT SELECT ON laundry_management_system.pending_orders_summary TO 'laundry_app'@'localhost';
-- FLUSH PRIVILEGES;

-- =====================================================
-- Add Comments for Documentation
-- =====================================================

-- Add comments to tables
ALTER TABLE users COMMENT = 'Custom user model storing all system users with role-based access';
ALTER TABLE customers COMMENT = 'Extended profile information for client users, tracks which admin created them';
ALTER TABLE services COMMENT = 'Laundry service catalog with pricing, tracks which admin created/updated them';
ALTER TABLE orders COMMENT = 'Main order tracking and management, tracks which staff created/updated them';
ALTER TABLE order_items COMMENT = 'Individual line items within orders';
ALTER TABLE payments COMMENT = 'Payment transaction records, tracks which staff recorded them';
ALTER TABLE order_status_history COMMENT = 'Audit trail for all order status changes';
ALTER TABLE notifications COMMENT = 'User notification system for alerts and updates';

-- Add comments to columns
ALTER TABLE orders MODIFY COLUMN order_number VARCHAR(50) COMMENT 'Human-readable unique order identifier (e.g., LND-2024-000001)';
ALTER TABLE payments MODIFY COLUMN reference VARCHAR(100) COMMENT 'Unique payment reference from payment gateway';
ALTER TABLE customers MODIFY COLUMN created_by BIGINT COMMENT 'ID of admin/superadmin who created this customer record';
ALTER TABLE orders MODIFY COLUMN created_by BIGINT COMMENT 'ID of staff who created this order';
ALTER TABLE orders MODIFY COLUMN updated_by BIGINT COMMENT 'ID of staff who last updated this order';

-- =====================================================
-- Verify Database Setup
-- =====================================================

-- Show all tables
SHOW TABLES;

-- Show table structures
DESCRIBE users;
DESCRIBE customers;
DESCRIBE services;
DESCRIBE orders;
DESCRIBE order_items;
DESCRIBE payments;
DESCRIBE order_status_history;
DESCRIBE notifications;

-- Show triggers
SHOW TRIGGERS;

-- Show views
SHOW FULL TABLES IN laundry_management_system WHERE TABLE_TYPE LIKE 'VIEW';

-- =====================================================
-- End of Schema
-- =====================================================