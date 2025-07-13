from flask import Flask, render_template, request, redirect, url_for, flash
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flash messages

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
        
        # If validation passes, show success message (in a real app, save to database)
        flash(f'ユーザー登録が完了しました。ユーザー名: {username}', 'success')
        return redirect(url_for('index'))
    
    return render_template('signup.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)