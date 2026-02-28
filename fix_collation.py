"""
Script to fix MySQL collation mismatch issue
Run this script to fix the generate_order_number trigger
"""
import mysql.connector
from mysql.connector import Error

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'laundry_management_system',
    'user': 'root',
    'password': 'Vicky@2017',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# SQL to fix the trigger
FIX_TRIGGER_SQL = """
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
    -- Use COLLATE to ensure both sides of LIKE use the same collation
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
"""

def fix_trigger():
    """Fix the generate_order_number trigger to handle collation mismatch"""
    connection = None
    cursor = None
    
    try:
        # Connect to MySQL
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("Connected to MySQL database")
        
        # Read and execute the SQL file
        with open('fix_collation.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Split by DELIMITER statements and execute
        statements = []
        current_statement = []
        in_delimiter_block = False
        
        for line in sql_script.split('\n'):
            if 'DELIMITER' in line.upper():
                if '$$' in line:
                    in_delimiter_block = True
                else:
                    in_delimiter_block = False
                    if current_statement:
                        statements.append('\n'.join(current_statement))
                        current_statement = []
                continue
            
            if in_delimiter_block:
                current_statement.append(line)
                if line.strip().endswith('$$'):
                    statements.append('\n'.join(current_statement))
                    current_statement = []
            else:
                if line.strip() and not line.strip().startswith('--'):
                    statements.append(line)
        
        # Execute each statement
        for statement in statements:
            if statement.strip():
                try:
                    # Remove DELIMITER lines and $$ markers
                    clean_statement = statement.replace('DELIMITER $$', '').replace('DELIMITER ;', '').strip()
                    if clean_statement and not clean_statement.startswith('--'):
                        # Execute multi-statement
                        for result in cursor.execute(clean_statement, multi=True):
                            if result.with_rows:
                                result.fetchall()
                    connection.commit()
                except Error as e:
                    print(f"Error executing statement: {e}")
                    print(f"Statement: {statement[:200]}...")
                    raise
        
        print("Trigger fixed successfully!")
        
        # Verify the trigger exists
        cursor.execute("SHOW TRIGGERS LIKE 'generate_order_number'")
        triggers = cursor.fetchall()
        if triggers:
            print(f"Trigger verified: {triggers[0]}")
        else:
            print("Warning: Trigger not found after creation")
        
    except Error as e:
        print(f"Error: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            print("MySQL connection closed")

if __name__ == '__main__':
    fix_trigger()
