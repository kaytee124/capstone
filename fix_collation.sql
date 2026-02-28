-- Fix collation mismatch issue
-- This script fixes the collation mismatch between utf8mb4_0900_ai_ci and utf8mb4_unicode_ci
-- The error occurs in the generate_order_number trigger when using LIKE operation

USE `laundry_management_system`;

-- Fix the trigger to use explicit collation matching
DROP TRIGGER IF EXISTS `generate_order_number`;

DELIMITER $$

CREATE DEFINER=`root`@`localhost` TRIGGER `generate_order_number`
BEFORE INSERT ON `orders`
FOR EACH ROW
BEGIN
    DECLARE year_prefix VARCHAR(4);
    DECLARE sequence_num INT;
    
    SET year_prefix = DATE_FORMAT(CURDATE(), '%Y');
    
    -- Get the next sequence number for this year
    -- Use COLLATE to ensure both sides of LIKE use the same collation (matching the table's collation)
    SELECT COALESCE(MAX(CAST(SUBSTRING_INDEX(order_number, '-', -1) AS UNSIGNED)), 0) + 1
    INTO sequence_num
    FROM orders
    WHERE order_number COLLATE utf8mb4_unicode_ci LIKE CONCAT('LND-', year_prefix, '-%') COLLATE utf8mb4_unicode_ci;
    
    IF sequence_num IS NULL OR sequence_num = 0 THEN
        SET sequence_num = 1;
    END IF;
    
    SET NEW.order_number = CONCAT('LND-', year_prefix, '-', LPAD(sequence_num, 6, '0'));
END$$

DELIMITER ;

-- Verify the trigger was created
SHOW TRIGGERS LIKE 'generate_order_number';
