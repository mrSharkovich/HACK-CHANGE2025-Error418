import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g, flash, jsonify, send_from_directory
from database import get_db, init_app

app = Flask(__name__)
app.secret_key = 'dev'
app.config['DATABASE'] = os.path.join(app.instance_path, 'learning_platform.db')

init_app(app)


# Главная страница
@app.route('/')
def index():
    return render_template('index.html')


# Страница регистрации
@app.route('/register')
def register_page():
    return render_template('register.html')


# API для регистрации
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    db = get_db()

    try:
        # Проверяем, существует ли пользователь
        existing_user = db.execute(
            'SELECT * FROM users WHERE login = ?', (data['username'],)
        ).fetchone()

        if existing_user:
            return jsonify({'error': 'Пользователь с таким логином уже существует'}), 400

        cursor = db.execute(
            "INSERT INTO users (login, password, first_name, last_name) VALUES (?, ?, ?, ?)",
            (data['username'], data['password'], data['name'], data['surname'])
        )
        db.commit()

        # Автоматически входим после регистрации
        session['user_id'] = cursor.lastrowid

        # Добавляем пользователю доступ к курсу по умолчанию
        db.execute(
            'INSERT INTO user_courses (user_id, course_id) VALUES (?, ?)',
            (cursor.lastrowid, 1)  # курс с id=1
        )
        db.commit()

        return jsonify({'success': True, 'user_id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Страница входа
@app.route('/login')
def login_page():
    return render_template('login.html')


# API для входа
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    db = get_db()

    user = db.execute(
        'SELECT * FROM users WHERE login = ? AND password = ?',
        (data['username'], data['password'])
    ).fetchone()

    if user:
        session['user_id'] = user['id']
        return jsonify({'success': True, 'user_id': user['id']})
    else:
        return jsonify({'error': 'Неверный логин или пароль'}), 401


# Загрузка пользователя перед запросом
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()


# Выход
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# Личный кабинет
@app.route('/dashboard')
def dashboard():
    if g.user is None:
        return redirect(url_for('login_page'))

    db = get_db()
    # Получаем только курсы, доступные пользователю
    courses = db.execute('''
        SELECT c.* FROM courses c
        JOIN user_courses uc ON c.id = uc.course_id
        WHERE uc.user_id = ?
    ''', (g.user['id'],)).fetchall()

    return render_template('dashboard.html', courses=courses, user=g.user)


# Страница курса
@app.route('/course/<int:course_id>')
def course(course_id):
    if g.user is None:
        return redirect(url_for('login_page'))

    db = get_db()

    # Проверяем, есть ли у пользователя доступ к курсу
    user_course = db.execute(
        'SELECT * FROM user_courses WHERE user_id = ? AND course_id = ?',
        (g.user['id'], course_id)
    ).fetchone()

    if not user_course:
        flash('У вас нет доступа к этому курсу')
        return redirect(url_for('dashboard'))

    course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if not course:
        flash('Курс не найден')
        return redirect(url_for('dashboard'))

    return render_template('course.html', course=course, user=g.user)


# API для получения уроков
@app.route('/api/lessons/<int:lesson_id>')
def get_lesson(lesson_id):
    if g.user is None:
        return jsonify({'error': 'Not authorized'}), 401

    db = get_db()
    lesson = db.execute('SELECT * FROM lessons WHERE id = ?', (lesson_id,)).fetchone()

    if lesson:
        # Получаем материалы урока
        materials = db.execute(
            'SELECT * FROM lesson_materials WHERE lesson_id = ?', (lesson_id,)
        ).fetchall()

        materials_list = []
        for material in materials:
            materials_list.append({
                'id': material['id'],
                'type': material['type'],
                'title': material['title'],
                'youtube_id': material['youtube_id'],
                'file_path': material['file_path']
            })

        # Получаем решение пользователя для этого урока
        submission = db.execute('''
            SELECT ha.*, c.comment 
            FROM homework_answers ha 
            LEFT JOIN comments c ON ha.comment_id = c.id 
            WHERE ha.lesson_id = ? AND ha.user_id = ?
            ORDER BY ha.submitted_at DESC 
            LIMIT 1
        ''', (lesson_id, g.user['id'])).fetchone()

        submission_data = None
        if submission:
            submission_data = {
                'id': submission['id'],
                'answer_text': submission['answer_text'],
                'submitted_at': submission['submitted_at'],
                'status': submission['status'],
                'comment': submission['comment'] if submission['comment'] else None
            }

        lesson_dict = {
            'id': lesson['id'],
            'title': lesson['title'],
            'content': lesson['content'],
            'tasks': [
                {
                    'id': lesson['id'],
                    'question': 'Опишите своими словами основные концепции, рассмотренные в этом уроке.'
                }
            ],
            'materials': materials_list,
            'submission': submission_data
        }
        return jsonify(lesson_dict)
    return jsonify({'error': 'Lesson not found'}), 404


# API для получения секций курса
@app.route('/api/courses/<int:course_id>/sections')
def get_course_sections(course_id):
    if g.user is None:
        return jsonify({'error': 'Not authorized'}), 401

    db = get_db()

    # Проверяем существование курса
    course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    # Получаем уроки курса
    lessons = db.execute(
        'SELECT * FROM lessons WHERE course_id = ? ORDER BY order_index', (course_id,)
    ).fetchall()

    # Создаем одну секцию с уроками
    sections = [{
        'id': 1,
        'title': 'Основные модули',
        'order_index': 1,
        'lessons': []
    }]

    for lesson in lessons:
        # Проверяем, пройден ли урок
        progress = db.execute(
            'SELECT 1 FROM user_progress WHERE user_id = ? AND lesson_id = ?',
            (g.user['id'], lesson['id'])
        ).fetchone()

        sections[0]['lessons'].append({
            'id': lesson['id'],
            'title': lesson['title'],
            'order_index': lesson['order_index'],
            'is_completed': progress is not None
        })

    return jsonify(sections)


# API для отправки решений
@app.route('/api/submissions', methods=['POST'])
def create_submission():
    if g.user is None:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    db = get_db()

    try:
        # Вставляем решение
        db.execute(
            'INSERT INTO homework_answers (lesson_id, user_id, answer_text, status) VALUES (?, ?, ?, ?)',
            (data['task_id'], g.user['id'], data['answer'], 'submitted')
        )

        # Отмечаем урок как пройденный
        db.execute(
            'INSERT OR REPLACE INTO user_progress (user_id, lesson_id, completed) VALUES (?, ?, ?)',
            (g.user['id'], data['task_id'], True)
        )

        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# API для получения решений и комментариев пользователя
@app.route('/api/submissions/<int:lesson_id>')
def get_submission(lesson_id):
    if g.user is None:
        return jsonify({'error': 'Not authorized'}), 401

    db = get_db()

    # Получаем решение пользователя для этого урока
    submission = db.execute('''
        SELECT ha.*, c.comment 
        FROM homework_answers ha 
        LEFT JOIN comments c ON ha.comment_id = c.id 
        WHERE ha.lesson_id = ? AND ha.user_id = ?
        ORDER BY ha.submitted_at DESC 
        LIMIT 1
    ''', (lesson_id, g.user['id'])).fetchone()

    if submission:
        submission_data = {
            'id': submission['id'],
            'answer_text': submission['answer_text'],
            'submitted_at': submission['submitted_at'],
            'status': submission['status'],
            'comment': submission['comment'] if submission['comment'] else None
        }
        return jsonify(submission_data)
    else:
        return jsonify({'submission': None})


# Новый endpoint для получения прогресса пользователя
@app.route('/api/user/progress')
def get_user_progress():
    if g.user is None:
        return jsonify({'error': 'Not authorized'}), 401

    db = get_db()
    course_id = request.args.get('course_id', type=int)

    # Если указан course_id, считаем прогресс только для этого курса
    if course_id:
        # Получаем общее количество уроков в курсе
        total_lessons = db.execute(
            'SELECT COUNT(*) as count FROM lessons WHERE course_id = ?',
            (course_id,)
        ).fetchone()['count']

        # Получаем количество пройденных уроков в курсе
        completed_lessons = db.execute(
            '''SELECT COUNT(*) as count 
               FROM user_progress up 
               JOIN lessons l ON up.lesson_id = l.id 
               WHERE up.user_id = ? AND up.completed = 1 AND l.course_id = ?''',
            (g.user['id'], course_id)
        ).fetchone()['count']
    else:
        # Получаем общее количество уроков
        total_lessons = db.execute(
            'SELECT COUNT(*) as count FROM lessons'
        ).fetchone()['count']

        # Получаем количество пройденных уроков
        completed_lessons = db.execute(
            'SELECT COUNT(*) as count FROM user_progress WHERE user_id = ? AND completed = 1',
            (g.user['id'],)
        ).fetchone()['count']

    progress = 0
    if total_lessons > 0:
        progress = int((completed_lessons / total_lessons) * 100)

    return jsonify({
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'progress': progress
    })


# Маршрут для обслуживания статических файлов из папки materials
@app.route('/materials/<path:filename>')
def serve_materials(filename):
    return send_from_directory('materials', filename)


# Функция для инициализации базы данных
def init_db():
    with app.app_context():
        db = get_db()

        # Проверяем существование таблиц и создаем недостающие
        check_and_create_tables(db)
        db.commit()


def check_and_create_tables(db):
    """Проверяет существование таблиц и создает недостающие"""

    # Проверяем существование таблицы courses
    try:
        db.execute("SELECT 1 FROM courses LIMIT 1")
    except sqlite3.OperationalError:
        # Создаем таблицу courses
        db.execute('''
            CREATE TABLE courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(100) NOT NULL
            )
        ''')
        print("Создана таблица courses")

    # Проверяем существование таблицы users
    try:
        db.execute("SELECT 1 FROM users LIMIT 1")
    except sqlite3.OperationalError:
        # Создаем таблицу users
        db.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login VARCHAR(25) NOT NULL UNIQUE,
                password VARCHAR(25) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                first_name VARCHAR(50) NOT NULL
            )
        ''')
        print("Создана таблица users")

    # Проверяем существование таблицы lessons
    try:
        db.execute("SELECT 1 FROM lessons LIMIT 1")
    except sqlite3.OperationalError:
        # Создаем таблицу lessons
        db.execute('''
            CREATE TABLE lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                home_work INTEGER NOT NULL,
                order_index INTEGER NOT NULL,
                course_id INTEGER NOT NULL
            )
        ''')
        print("Создана таблица lessons")

    # Проверяем существование таблицы user_progress
    try:
        db.execute("SELECT 1 FROM user_progress LIMIT 1")
    except sqlite3.OperationalError:
        # Создаем таблицу user_progress
        db.execute('''
            CREATE TABLE user_progress (
                user_id INTEGER NOT NULL,
                lesson_id INTEGER NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, lesson_id)
            )
        ''')
        print("Создана таблица user_progress")

    # Проверяем существование таблицы homework_answers
    try:
        db.execute("SELECT 1 FROM homework_answers LIMIT 1")
    except sqlite3.OperationalError:
        # Создаем таблицу homework_answers
        db.execute('''
            CREATE TABLE homework_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                answer_text TEXT,
                file_path VARCHAR(255),
                file_name VARCHAR(255),
                submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending',
                comment_id INTEGER
            )
        ''')
        print("Создана таблица homework_answers")

    # Проверяем существование таблицы comments
    try:
        db.execute("SELECT 1 FROM comments LIMIT 1")
    except sqlite3.OperationalError:
        # Создаем таблицу comments
        db.execute('''
            CREATE TABLE comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment TEXT NOT NULL
            )
        ''')
        print("Создана таблица comments")

    # Проверяем существование таблицы lesson_materials
    try:
        db.execute("SELECT 1 FROM lesson_materials LIMIT 1")
    except sqlite3.OperationalError:
        # Создаем таблицу lesson_materials
        db.execute('''
            CREATE TABLE lesson_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                youtube_id TEXT,
                file_path TEXT
            )
        ''')
        print("Создана таблица lesson_materials")

    # Проверяем существование таблицы user_courses
    try:
        db.execute("SELECT 1 FROM user_courses LIMIT 1")
    except sqlite3.OperationalError:
        # Создаем таблицу user_courses
        db.execute('''
            CREATE TABLE user_courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL
            )
        ''')
        print("Создана таблица user_courses")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)