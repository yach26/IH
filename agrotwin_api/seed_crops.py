import sqlite3

def seed():
    conn = sqlite3.connect('agrotwin.db')
    cursor = conn.cursor()
    
    # Ensure Rice exists
    cursor.execute("INSERT OR IGNORE INTO crops (crop_code, crop_name, is_pilot) VALUES ('RICE', 'Rice', 1)")
    
    # Assign different crops to REAL-002, REAL-003, REAL-004
    cursor.execute("UPDATE field_crops SET crop_id = (SELECT crop_id FROM crops WHERE crop_code = 'BANANA') WHERE field_id = (SELECT field_id FROM fields WHERE field_code = 'REAL-002')")
    cursor.execute("UPDATE field_crops SET crop_id = (SELECT crop_id FROM crops WHERE crop_code = 'COTTON') WHERE field_id = (SELECT field_id FROM fields WHERE field_code = 'REAL-003')")
    cursor.execute("UPDATE field_crops SET crop_id = (SELECT crop_id FROM crops WHERE crop_code = 'RICE') WHERE field_id = (SELECT field_id FROM fields WHERE field_code = 'REAL-004')")
    
    conn.commit()
    conn.close()
    print("Database seeded with different crops for REAL-002, 003, and 004.")

if __name__ == '__main__':
    seed()
