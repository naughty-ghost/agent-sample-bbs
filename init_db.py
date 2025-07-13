#!/usr/bin/env python3
"""
Database initialization script for the BBS application
"""

import psycopg2
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://bbs_user:bbs_password@localhost:5432/bbs_db')

def init_database():
    """Initialize the database with required tables"""
    print("Initializing database...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Create users table
        print("Creating users table...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(8) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        print("Creating indexes...")
        cur.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("Database initialization completed successfully!")
        return True
        
    except psycopg2.Error as e:
        print(f"Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    exit(0 if success else 1)