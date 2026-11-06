"""
國立金門大學 校務資訊系統 (簡化版)
National Quemoy University Academic Affairs System Demo
習題專案 - 模擬學生端校務系統
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = 'nqu_academic_system_secret_key_2024'

DATABASE = 'nqu_system.db'


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化資料庫與範例資料"""
    conn = get_db()
    c = conn.cursor()

    # 學生資料表
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            department TEXT,
            grade INTEGER,
            email TEXT,
            phone TEXT,
            id_last4 TEXT
        )
    ''')

    # 課程資料表
    c.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            course_id TEXT PRIMARY KEY,
            course_name TEXT NOT NULL,
            teacher TEXT,
            credits REAL,
            capacity INTEGER,
            enrolled INTEGER DEFAULT 0,
            day TEXT,
            period TEXT,
            classroom TEXT,
            department TEXT
        )
    ''')

    # 選課紀錄
    c.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            course_id TEXT,
            enroll_time TEXT,
            UNIQUE(student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id)
        )
    ''')

    # 成績
    c.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            course_id TEXT,
            semester TEXT,
            score REAL,
            grade_point REAL,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id)
        )
    ''')

    # 請假申請
    c.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            leave_type TEXT,
            start_date TEXT,
            end_date TEXT,
            reason TEXT,
            status TEXT DEFAULT '待審核',
            apply_time TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')

    # 檢查是否已有資料
    c.execute('SELECT COUNT(*) FROM students')
    if c.fetchone()[0] == 0:
        # 範例學生 (密碼皆為 1234 或身分證後四碼模擬)
        students = [
            ('11201001', generate_password_hash('1234'), '王小明', '資訊工程學系', 2, 's11201001@stu.nqu.edu.tw', '0912-345-678', '1234'),
            ('11202015', generate_password_hash('5678'), '陳美華', '企業管理學系', 3, 's11202015@stu.nqu.edu.tw', '0923-456-789', '5678'),
            ('11303008', generate_password_hash('9012'), '林志豪', '觀光管理學系', 1, 's11303008@stu.nqu.edu.tw', '0934-567-890', '9012'),
            ('11104022', generate_password_hash('3456'), '張雅婷', '護理學系', 4, 's11104022@stu.nqu.edu.tw', '0945-678-901', '3456'),
        ]
        c.executemany('INSERT INTO students VALUES (?,?,?,?,?,?,?,?)', students)

        # 範例課程
        courses = [
            ('CS101', '程式設計(一)', '李教授', 3.0, 50, 12, '一', '3-4', '圖資大樓A101', '資訊工程學系'),
            ('CS201', '資料結構', '王老師', 3.0, 40, 8, '二', '5-6', '圖資大樓A201', '資訊工程學系'),
            ('CS301', '資料庫系統', '陳教授', 3.0, 45, 15, '三', '1-2', '圖資大樓B102', '資訊工程學系'),
            ('BA101', '管理學', '林老師', 3.0, 60, 25, '一', '5-6', '管理大樓M101', '企業管理學系'),
            ('BA201', '行銷管理', '黃教授', 3.0, 50, 18, '四', '3-4', '管理大樓M201', '企業管理學系'),
            ('TM101', '觀光概論', '蔡老師', 2.0, 55, 30, '二', '1-2', '人文大樓H101', '觀光管理學系'),
            ('TM201', '旅館管理', '吳教授', 3.0, 40, 10, '五', '5-6', '人文大樓H201', '觀光管理學系'),
            ('NU101', '基礎護理學', '張護理師', 3.0, 35, 20, '一', '1-2', '健康大樓N101', '護理學系'),
            ('GE101', '國文', '劉老師', 2.0, 80, 45, '三', '5-6', '綜合大樓C101', '通識教育中心'),
            ('GE102', '英文(一)', 'Smith', 2.0, 70, 38, '四', '1-2', '綜合大樓C201', '通識教育中心'),
            ('PE101', '體育(一)', '許教練', 1.0, 40, 22, '五', '3-4', '體育館', '體育室'),
            ('CS401', '人工智慧導論', '周教授', 3.0, 35, 5, '二', '3-4', '圖資大樓A301', '資訊工程學系'),
        ]
        c.executemany('INSERT INTO courses VALUES (?,?,?,?,?,?,?,?,?,?)', courses)

        # 範例選課
        enrollments = [
            ('11201001', 'CS101', '2025-09-01 10:00:00'),
            ('11201001', 'CS201', '2025-09-01 10:05:00'),
            ('11201001', 'GE101', '2025-09-01 10:10:00'),
            ('11201001', 'PE101', '2025-09-01 10:15:00'),
            ('11202015', 'BA101', '2025-09-01 11:00:00'),
            ('11202015', 'BA201', '2025-09-01 11:05:00'),
            ('11202015', 'GE102', '2025-09-01 11:10:00'),
            ('11303008', 'TM101', '2025-09-01 12:00:00'),
            ('11303008', 'GE101', '2025-09-01 12:05:00'),
            ('11104022', 'NU101', '2025-09-01 09:00:00'),
            ('11104022', 'GE102', '2025-09-01 09:05:00'),
        ]
        c.executemany('INSERT INTO enrollments (student_id, course_id, enroll_time) VALUES (?,?,?)', enrollments)

        # 更新已選人數
        for course_id in ['CS101', 'CS201', 'GE101', 'PE101', 'BA101', 'BA201', 'GE102', 'TM101', 'NU101']:
            c.execute('UPDATE courses SET enrolled = (SELECT COUNT(*) FROM enrollments WHERE course_id=?) WHERE course_id=?', (course_id, course_id))

        # 範例成績 (前一學期)
        grades = [
            ('11201001', 'CS101', '113-2', 85, 3.7),
            ('11201001', 'GE101', '113-2', 78, 3.0),
            ('11201001', 'PE101', '113-2', 90, 4.0),
            ('11202015', 'BA101', '113-2', 88, 3.7),
            ('11202015', 'GE102', '113-2', 82, 3.3),
            ('11104022', 'NU101', '113-2', 92, 4.0),
            ('11104022', 'GE102', '113-2', 86, 3.7),
        ]
        c.executemany('INSERT INTO grades (student_id, course_id, semester, score, grade_point) VALUES (?,?,?,?,?)', grades)

    conn.commit()
    conn.close()


# ==================== 路由 ====================

@app.route('/')
def index():
    if 'student_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        password = request.form.get('password', '')

        conn = get_db()
        student = conn.execute('SELECT * FROM students WHERE student_id = ?', (student_id,)).fetchone()
        conn.close()

        if student and check_password_hash(student['password'], password):
            session['student_id'] = student['student_id']
            session['name'] = student['name']
            session['department'] = student['department']
            flash(f'歡迎回來，{student["name"]}！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('學號或密碼錯誤，請重新輸入。', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功登出。', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    student = conn.execute('SELECT * FROM students WHERE student_id = ?', (session['student_id'],)).fetchone()

    # 本學期已選課程數
    enrolled_count = conn.execute(
        'SELECT COUNT(*) FROM enrollments WHERE student_id = ?', (session['student_id'],)
    ).fetchone()[0]

    # 總學分
    total_credits = conn.execute('''
        SELECT COALESCE(SUM(c.credits), 0)
        FROM enrollments e
        JOIN courses c ON e.course_id = c.course_id
        WHERE e.student_id = ?
    ''', (session['student_id'],)).fetchone()[0]

    # 待審核請假
    pending_leave = conn.execute(
        'SELECT COUNT(*) FROM leave_requests WHERE student_id = ? AND status = "待審核"',
        (session['student_id'],)
    ).fetchone()[0]

    conn.close()

    return render_template('dashboard.html',
                           student=student,
                           enrolled_count=enrolled_count,
                           total_credits=total_credits,
                           pending_leave=pending_leave)


@app.route('/profile')
def profile():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    student = conn.execute('SELECT * FROM students WHERE student_id = ?', (session['student_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', student=student)


@app.route('/courses')
def courses():
    """選課頁面 - 顯示可選課程"""
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    all_courses = conn.execute('SELECT * FROM courses ORDER BY course_id').fetchall()

    # 已選課程 ID
    enrolled = conn.execute(
        'SELECT course_id FROM enrollments WHERE student_id = ?', (session['student_id'],)
    ).fetchall()
    enrolled_ids = {row['course_id'] for row in enrolled}
    conn.close()

    return render_template('courses.html', courses=all_courses, enrolled_ids=enrolled_ids)


@app.route('/enroll/<course_id>', methods=['POST'])
def enroll(course_id):
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    course = conn.execute('SELECT * FROM courses WHERE course_id = ?', (course_id,)).fetchone()

    if not course:
        flash('課程不存在。', 'danger')
        conn.close()
        return redirect(url_for('courses'))

    if course['enrolled'] >= course['capacity']:
        flash(f'【{course["course_name"]}】已額滿，無法選課。', 'warning')
        conn.close()
        return redirect(url_for('courses'))

    # 檢查是否已選
    existing = conn.execute(
        'SELECT id FROM enrollments WHERE student_id = ? AND course_id = ?',
        (session['student_id'], course_id)
    ).fetchone()

    if existing:
        flash('您已選過此課程。', 'warning')
        conn.close()
        return redirect(url_for('courses'))

    # 選課
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        'INSERT INTO enrollments (student_id, course_id, enroll_time) VALUES (?,?,?)',
        (session['student_id'], course_id, now)
    )
    conn.execute('UPDATE courses SET enrolled = enrolled + 1 WHERE course_id = ?', (course_id,))
    conn.commit()
    conn.close()

    flash(f'成功選修【{course["course_name"]}】！', 'success')
    return redirect(url_for('courses'))


@app.route('/drop/<course_id>', methods=['POST'])
def drop(course_id):
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    course = conn.execute('SELECT * FROM courses WHERE course_id = ?', (course_id,)).fetchone()

    conn.execute(
        'DELETE FROM enrollments WHERE student_id = ? AND course_id = ?',
        (session['student_id'], course_id)
    )
    conn.execute('UPDATE courses SET enrolled = enrolled - 1 WHERE course_id = ? AND enrolled > 0', (course_id,))
    conn.commit()
    conn.close()

    if course:
        flash(f'已退選【{course["course_name"]}】。', 'info')
    return redirect(url_for('my_courses'))


@app.route('/my_courses')
def my_courses():
    """我的課表 / 已選課程"""
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    my_list = conn.execute('''
        SELECT c.*, e.enroll_time
        FROM enrollments e
        JOIN courses c ON e.course_id = c.course_id
        WHERE e.student_id = ?
        ORDER BY c.day, c.period
    ''', (session['student_id'],)).fetchall()
    conn.close()

    # 整理成課表格式 (簡易)
    days = ['一', '二', '三', '四', '五']
    schedule = {d: [] for d in days}
    for course in my_list:
        if course['day'] in schedule:
            schedule[course['day']].append(course)

    return render_template('my_courses.html', courses=my_list, schedule=schedule)


@app.route('/grades')
def grades():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    grade_list = conn.execute('''
        SELECT g.*, c.course_name, c.credits, c.teacher
        FROM grades g
        JOIN courses c ON g.course_id = c.course_id
        WHERE g.student_id = ?
        ORDER BY g.semester DESC, c.course_id
    ''', (session['student_id'],)).fetchall()

    # 計算平均
    if grade_list:
        total_points = sum(g['grade_point'] * g['credits'] for g in grade_list)
        total_credits = sum(g['credits'] for g in grade_list)
        gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0
    else:
        gpa = 0
        total_credits = 0

    conn.close()
    return render_template('grades.html', grades=grade_list, gpa=gpa, total_credits=total_credits)


@app.route('/leave', methods=['GET', 'POST'])
def leave():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':
        leave_type = request.form.get('leave_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        reason = request.form.get('reason', '').strip()

        if not all([leave_type, start_date, end_date, reason]):
            flash('請填寫完整請假資訊。', 'warning')
        else:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute('''
                INSERT INTO leave_requests (student_id, leave_type, start_date, end_date, reason, apply_time)
                VALUES (?,?,?,?,?,?)
            ''', (session['student_id'], leave_type, start_date, end_date, reason, now))
            conn.commit()
            flash('請假申請已送出，請等待審核。', 'success')
            return redirect(url_for('leave'))

    # 查詢歷史請假
    history = conn.execute('''
        SELECT * FROM leave_requests
        WHERE student_id = ?
        ORDER BY apply_time DESC
    ''', (session['student_id'],)).fetchall()
    conn.close()

    return render_template('leave.html', history=history)


# 啟動時初始化
if __name__ == '__main__':
    init_db()
    print('=' * 50)
    print('國立金門大學 校務資訊系統 (Demo)')
    print('請開啟瀏覽器前往: http://127.0.0.1:5000')
    print('=' * 50)
    print('測試帳號：')
    print('  學號: 11201001  密碼: 1234  (王小明 - 資訊工程學系)')
    print('  學號: 11202015  密碼: 5678  (陳美華 - 企業管理學系)')
    print('  學號: 11303008  密碼: 9012  (林志豪 - 觀光管理學系)')
    print('  學號: 11104022  密碼: 3456  (張雅婷 - 護理學系)')
    print('=' * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
