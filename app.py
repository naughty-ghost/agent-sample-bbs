from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import re
import os
from datetime import datetime, timedelta

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
        
        # Create posts table if it doesn't exist
        cur.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                post_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
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
    # Get posts from database for timeline
    conn = get_db_connection()
    posts = []
    
    if conn:
        try:
            cur = conn.cursor()
            # Get posts with user information, ordered by newest first
            cur.execute('''
                SELECT p.post_id, p.title, p.content, p.created_at, u.username
                FROM posts p
                JOIN users u ON p.user_id = u.user_id
                ORDER BY p.created_at DESC
            ''')
            posts = cur.fetchall()
            cur.close()
            conn.close()
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            if conn:
                cur.close()
                conn.close()
    
    return render_template('index.html', posts=posts, timedelta=timedelta)

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

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validation
        if not username:
            flash('ユーザー名は必須です。', 'error')
            return render_template('signin.html', username=username)
        
        if not password:
            flash('パスワードは必須です。', 'error')
            return render_template('signin.html', username=username)
        
        # Authenticate user
        conn = get_db_connection()
        if conn is None:
            flash('データベース接続エラーが発生しました。', 'error')
            return render_template('signin.html', username=username)
        
        try:
            cur = conn.cursor()
            
            # Get user from database
            cur.execute('SELECT user_id, username, password_hash FROM users WHERE username = %s', (username,))
            user = cur.fetchone()
            
            cur.close()
            conn.close()
            
            if user and check_password_hash(user[2], password):
                # Successful authentication
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash(f'サインインしました。ようこそ {username} さん！', 'success')
                return redirect(url_for('index'))
            else:
                flash('ユーザー名またはパスワードが正しくありません。', 'error')
                return render_template('signin.html', username=username)
                
        except psycopg2.Error as e:
            if conn:
                cur.close()
                conn.close()
            
            print(f"Database error: {e}")
            flash('サインイン中にエラーが発生しました。', 'error')
            return render_template('signin.html', username=username)
    
    return render_template('signin.html')

@app.route('/signout')
def signout():
    session.clear()
    flash('サインアウトしました。', 'success')
    return redirect(url_for('index'))

@app.route('/post', methods=['GET', 'POST'])
def post():
    # Check if user is signed in
    if 'user_id' not in session:
        flash('投稿するにはサインインが必要です。', 'error')
        return redirect(url_for('signin'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        # Validation
        errors = []
        
        if not title:
            errors.append('タイトルは必須です。')
        elif len(title) > 255:
            errors.append('タイトルは255文字以下で入力してください。')
        
        if not content:
            errors.append('内容は必須です。')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('post.html', title=title, content=content)
        
        # Save post to database
        conn = get_db_connection()
        if conn is None:
            flash('データベース接続エラーが発生しました。', 'error')
            return render_template('post.html', title=title, content=content)
        
        try:
            cur = conn.cursor()
            
            # Insert post into database
            cur.execute('''
                INSERT INTO posts (user_id, title, content, created_at, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (session['user_id'], title, content))
            
            conn.commit()
            cur.close()
            conn.close()
            
            flash('投稿が完了しました。', 'success')
            return redirect(url_for('index'))
            
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
                cur.close()
                conn.close()
            
            print(f"Database error: {e}")
            flash('投稿中にエラーが発生しました。', 'error')
            return render_template('post.html', title=title, content=content)
    
    return render_template('post.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)