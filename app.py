from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import re
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flash messages

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://bbs_user:bbs_password@localhost:5432/bbs_db')

def get_db_connection():
    """Get a database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize the database with user table"""
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cur = conn.cursor()
        
        # Create users table if it doesn't exist
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
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"Database initialization error: {e}")
        if conn:
            conn.close()
        return False

# Initialize database on startup
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Validation
        errors = []
        
        # Username validation: alphanumeric and underscore only, max 8 characters
        if not username:
            errors.append('ユーザー名は必須です。')
        elif len(username) > 8:
            errors.append('ユーザー名は8文字以下で入力してください。')
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('ユーザー名は英数字とアンダースコアのみ使用可能です。')
        
        # Email validation
        if not email:
            errors.append('メールアドレスは必須です。')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('有効なメールアドレスを入力してください。')
        
        # Password validation: minimum 8 characters
        if not password:
            errors.append('パスワードは必須です。')
        elif len(password) < 8:
            errors.append('パスワードは8文字以上で入力してください。')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('signup.html', username=username, email=email)
        
        # Save user to database
        conn = get_db_connection()
        if conn is None:
            flash('データベース接続エラーが発生しました。', 'error')
            return render_template('signup.html', username=username, email=email)
        
        try:
            cur = conn.cursor()
            
            # Hash the password
            password_hash = generate_password_hash(password)
            
            # Insert user into database
            cur.execute('''
                INSERT INTO users (username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (username, email, password_hash))
            
            conn.commit()
            cur.close()
            conn.close()
            
            flash(f'ユーザー登録が完了しました。ユーザー名: {username}', 'success')
            return redirect(url_for('index'))
            
        except psycopg2.IntegrityError as e:
            conn.rollback()
            cur.close()
            conn.close()
            
            # Handle unique constraint violations
            if 'username' in str(e):
                flash('このユーザー名は既に使用されています。', 'error')
            elif 'email' in str(e):
                flash('このメールアドレスは既に登録されています。', 'error')
            else:
                flash('ユーザー登録に失敗しました。', 'error')
            
            return render_template('signup.html', username=username, email=email)
            
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
                cur.close()
                conn.close()
            
            print(f"Database error: {e}")
            flash('ユーザー登録中にエラーが発生しました。', 'error')
            return render_template('signup.html', username=username, email=email)
    
    return render_template('signup.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)