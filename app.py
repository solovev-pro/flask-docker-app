import os
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'hackathon-sphera-secret-key'

base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'hackathon.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

sferum_context = {
    'school_name': 'Школа №1',
    'grade': '5А',
    'class_teacher': 'Иванова А.А.',
    'attendance_rate': 95
}

ai_hints = {
    'case_question': 'Вспомни вопросы падежей. «К кому? Чему?» — это дательный падеж.',
    'literature_personification': 'Олицетворение — когда неживому предмету дают свойства живого.',
    'common_denominator': 'Приведи дроби к общему знаменателю.',
    'egypt_river': 'Главная река Египта начинается на "Н".',
    'map_water_color': 'Воду на плане обозначают цветом неба и моря.',
    'cell_nucleus': 'Этот органоид содержит ДНК и управляет клеткой.',
    'art_primary_colors': 'Из этих трёх цветов можно получить все остальные.',
    'music_strings': 'Скрипка звучит за счёт вибрации струн.',
    'tech_file': 'Напильник снимает тонкий слой материала для гладкости.',
    'pe_basketball': 'В баскетболе мяч передают руками.',
    'present_simple_he': 'С he/she/it к глаголу добавляется -s.'
}

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    school = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)

class SchoolClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    school = db.Column(db.String(100), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('school_class.id'), nullable=False)
    last_reminder = db.Column(db.DateTime, default=datetime.utcnow)
    missed_topics = db.Column(db.PickleType, default=list)
    completed_topics = db.Column(db.PickleType, default=list)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    topic_id = db.Column(db.Integer, nullable=True)
    skip_type = db.Column(db.String(100), nullable=False)
    task_text = db.Column(db.Text, nullable=False)

SUBJECTS_DATA = {
    "Русский язык": [
        "Падежи имен существительных",
        "Орфография и пунктуация",
        "Члены предложения",
        "Лексика и фразеология",
        "Правописание приставок",
        "Типы текстов",
    ],
    "Литература": [
        "Устное народное творчество",
        "Басни И.А. Крылова",
        "А.С. Пушкин. Сказки",
    ],
    "Иностранный язык": [
        "Present Simple",
        "Мои увлечения и хобби",
        "Чтение: работа с текстом",
    ],
    "Математика": [
        "Обыкновенные и десятичные дроби",
        "Таблица умножения и деления",
        "Проценты",
        "Задачи на движение",
        "Геометрические фигуры и площади",
    ],
    "История": [
        "Древняя Русь",
        "Московское государство",
        "История нашего края",
        "Великая Отечественная война",
    ],
    "Биология": [
        "Клеточное строение организмов",
        "Царство Растений",
        "Экология и охрана природы",
    ],
    "География": [
        "План и карта",
        "Рельеф и полезные ископаемые России",
        "Климат России",
    ],
    "Изобразительное искусство (ИЗО)": [
        "Основные и составные цвета",
        "Пейзаж и перспектива",
    ],
    "Музыка": [
        "Музыкальные инструменты",
        "Жанры музыки: марш, песня, танец",
    ],
    "Труд (технология)": [
        "Работа с деревом: напильник и шлифовка",
        "Проект: полезная вещь своими руками",
    ],
    "Физическая культура": [
        "Техника передачи мяча в баскетболе",
        "Подтягивания и нормативы",
    ],
    "ОБЗР": [
        "Правила поведения при пожаре",
        "Первая помощь: вызов экстренных служб",
    ],
}

TASK_CONTENT = {
    # Русский язык
    101: {"text": "Определи падеж существительного: подошёл (к дому)", "answer": "дательный", "rule": "case_question"},
    102: {"text": "Вставь пропущенную букву: с(?)мка — напиши только букву", "answer": "у", "rule": "case_question"},
    103: {"text": "Найди грамматическую основу: «Утренний ветер гонит облака»", "answer": "ветер гонит", "rule": "literature_personification"},

    # Математика
    201: {"text": "Приведи дроби 1/2 и 1/3 к общему знаменателю. Напиши только число", "answer": "6", "rule": "common_denominator"},
    202: {"text": "Вычисли: 3/4 + 1/4. Напиши ответ дробью", "answer": "1", "rule": "common_denominator"},
    203: {"text": "Найди 20% от числа 50. Напиши только число", "answer": "10", "rule": "common_denominator"},
    204: {"text": "Скорость велосипедиста 12 км/ч. Какой путь он проедет за 2 часа? Напиши число (км)", "answer": "24", "rule": "common_denominator"},

    # Литература
    301: {"text": "Как называется приём, когда неживому приписываются свойства живого? Например: «ветер шепчет»", "answer": "олицетворение", "rule": "literature_personification"},
    302: {"text": "Кто автор рассказа «Зелёная лампа»? Напиши только фамилию", "answer": "грин", "rule": "literature_author"},

    # Биология
    601: {"text": "Какой органоид содержит ДНК и управляет клеткой? Напиши одним словом", "answer": "ядро", "rule": "cell_nucleus"},
    602: {"text": "Что образуется в листьях растения в процессе фотосинтеза? Напиши одно слово", "answer": "глюкоза", "rule": "photosynthesis"},
}

TASKS_DATA = {
    "Русский язык": [
        {"id": 101, "title": "Падежи: определи падеж существительного", "video_url": "https://vkvideo.ru/video-19083451_456240498"},
        {"id": 102, "title": "Орфография: вставь пропущенные буквы", "video_url": None},
        {"id": 103, "title": "Подчеркни грамматическую основу", "video_url": "https://vkvideo.ru/video-19083451_456240538"},
    ],
    "Математика": [
        {"id": 201, "title": "Приведи дроби к общему знаменателю", "video_url": "https://vkvideo.ru/video-200702114_456240566"},
        {"id": 204, "title": "Задача на скорость и время", "video_url": "https://vkvideo.ru/video-200702114_456240101"},
    ],
    "Литература": [
        {"id": 301, "title": "Басня Крылова: мораль и герои", "video_url": None},
        {"id": 302, "title": "Сказка Пушкина: пересказ", "video_url": None},
        {"id": 303, "title": "Найди олицетворение в стихотворении", "video_url": None},
    ],
    "Иностранный язык": [
        {"id": 401, "title": "Раскрой скобки: Present Simple", "video_url": None},
    ],
    "История": [
        {"id": 501, "title": "Древняя Русь: даты и события", "video_url": None},
        {"id": 502, "title": "История нашего края: важные места", "video_url": None},
    ],
    "Биология": [
        {"id": 601, "title": "Найди органоид клетки", "video_url": None},
        {"id": 602, "title": "Строение растения", "video_url": None},
        {"id": 603, "title": "Правила поведения в природе", "video_url": None},
    ],
    "География": [
        {"id": 701, "title": "Определи объект по плану", "video_url": None},
    ],
    "Изобразительное искусство (ИЗО)": [
        {"id": 801, "title": "Смешай основные цвета", "video_url": None},
    ],
    "Музыка": [
        {"id": 901, "title": "Узнай инструмент по описанию", "video_url": None},
        {"id": 902, "title": "Определи жанр произведения", "video_url": None},
        {"id": 903, "title": "Струнные инструменты", "video_url": None},
    ],
    "Труд (технология)": [
        {"id": 1001, "title": "Зачем нужен напильник", "video_url": None},
    ],
    "Физическая культура": [
        {"id": 1101, "title": "Как передавать мяч в баскетболе", "video_url": None},
        {"id": 1102, "title": "Разминка перед бегом", "video_url": None},
        {"id": 1103, "title": "Правильная техника подтягивания", "video_url": None},
    ],
    "ОБЗР": [
        {"id": 1201, "title": "План действий при пожаре", "video_url": None},
    ],
}

REGIONS_DATA = {
    "Приморский край": ["Гимназия №1 (Владивосток)", "СОШ №23 (Владивосток)"],
    "Московская область": ["Лицей №1 (Подольск)", "СОШ №5 (Балашиха)"]
}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_reminder_status(student):
    if not student.missed_topics:
        return False, "", None

    days_since_last = (datetime.utcnow() - student.last_reminder).days
    if days_since_last >= 1:
        missed_topic_id = student.missed_topics[0]
        text = f"Ты пропустил тему с ID {missed_topic_id}. Давай восполним пробел прямо сейчас!"
        return True, text, missed_topic_id
    return False, "", None

def seed_database():
    with app.app_context():
        db.create_all()
        if not SchoolClass.query.first():
            sch1 = "Гимназия №1 (Владивосток)"
            c1 = SchoolClass(name="5-А класс", school=sch1)
            c2 = SchoolClass(name="9-Б класс", school=sch1)
            db.session.add_all([c1, c2])
            db.session.commit()

            db.session.add_all([
                Student(name="Иванов Ваня", class_id=c1.id,
                        missed_topics=[101, 201, 301], completed_topics=[]),
                Student(name="Петров Петр", class_id=c1.id,
                        missed_topics=[102, 601], completed_topics=[])
            ])
            db.session.commit()
        else:
            all_ids = {t["id"] for topics in TASKS_DATA.values() for t in topics}
            for s in Student.query.all():
                missed = s.missed_topics or []
                if any(t not in all_ids for t in missed):
                    s.missed_topics = [101, 201, 301]
            db.session.commit()

# --- МАРШРУТЫ ---
@app.route('/')
def index():
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/teacher-login')
def teacher_login():
    session['role'] = 'teacher'
    return redirect(url_for('teacher_dashboard'))

@app.route('/student_home')
def student_home():
    if session.get('role') != 'student':
        return redirect(url_for('login_page'))

    student_id = session.get('student_id')
    student = Student.query.get(student_id)
    if not student:
        return redirect(url_for('login_page'))

    absences = []
    for topic_id in student.missed_topics:
        absences.append({
            'date': 'вчера',
            'subject': f'Пропущена тема с ID {topic_id}',
            'reason': 'пропущена тема'
        })
    if not absences:
        absences = [{'date': '-', 'subject': 'Нет пропущенных тем', 'reason': ''}]

    news = [
        {'date': '2026-10-27', 'title': 'Новый модуль по программированию', 'text': 'Открыт доступ к урокам по Python для 5 классов.'},
        {'date': '2026-10-26', 'title': 'Изменение расписания', 'text': 'Урок физкультуры перенесён на пятницу.'}
    ]

    tasks = []
    for topic_id in student.missed_topics:
        deadline = (datetime.utcnow() + timedelta(days=3)).strftime('%Y-%m-%d')
        tasks.append({'id': topic_id, 'title': f'Тема {topic_id}', 'deadline': deadline, 'status': 'active'})
    for topic_id in student.completed_topics:
        tasks.append({'id': topic_id, 'title': f'Тема {topic_id}', 'deadline': '-', 'status': 'done'})

    return render_template(
        'student_home.html',
        absences=absences,
        news=news,
        tasks=tasks,
        student_name=student.name,
        sferum=sferum_context
    )

@app.route('/student_dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login_page'))

    student_id = session.get('student_id')
    student = Student.query.get(student_id)
    if not student:
        return redirect(url_for('login_page'))

    show_reminder, reminder_text, missed_topic_id = get_reminder_status(student)
    if show_reminder:
        student.last_reminder = datetime.utcnow()
        db.session.commit()

    subjects = []
    for subject_name, topics in TASKS_DATA.items():
        subjects.append({
            'name': subject_name,
            'topics': topics
        })

    assigned = []
    assignments = Assignment.query.filter_by(student_id=student.id).all()
    for a in assignments:
        topic_title = None
        for items in TASKS_DATA.values():
            for t in items:
                if t["id"] == a.topic_id:
                    topic_title = t["title"]
                    break
        assigned.append({
            'id': a.id,
            'topic_id': a.topic_id,
            'title': topic_title or 'Неизвестная тема',
            'task_text': a.task_text,
            'teacher_name': Teacher.query.get(a.teacher_id).name
        })

    return render_template(
        'student_dashboard.html',
        subjects=subjects,
        student=student,
        student_name=student.name,
        sferum=sferum_context,
        show_reminder=show_reminder,
        reminder_text=reminder_text,
        missed_topic_id=missed_topic_id,
        assigned=assigned          
    )

@app.route('/topic/<int:topic_id>')
def topic_detail(topic_id):
    task, subject = None, ""
    for subj, items in TASKS_DATA.items():
        for t in items:
            if t["id"] == topic_id:
                task, subject = t, subj
                break

    if not task:
        task = {"id": topic_id, "title": f"Тема {topic_id}", "video_url": None}

    video_embed = None
    raw = task.get("video_url")
    if raw and "vkvideo" in raw:
        tail = raw.split("video")[-1]
        oid, vid = tail.split("_")
        video_embed = f"https://vkvideo.ru/video_ext.php?oid={oid}&id={vid}&hd=2"

    content = TASK_CONTENT.get(topic_id)
    result = request.args.get('result') 

    tasks = []
    if content:
        tasks.append({
            'id': topic_id,
            'text': content['text'],
            'rule': content['rule'],
            'result': result
        })

    return render_template(
        'topic_detail.html',
        topic=task,
        has_video=video_embed is not None,
        video_embed=video_embed,
        tasks=tasks,
        sferum=sferum_context
    )

@app.route('/submit', methods=['POST'])
def submit():
    task_id = int(request.form.get('task_id', 0))
    answer = request.form.get('answer', '').strip().lower()
    student = Student.query.get(session.get('student_id'))
    if not student:
        return 'Не авторизован', 401

    content = TASK_CONTENT.get(task_id)
    correct = bool(content) and answer == content['answer'].lower()

    if correct:
        completed = list(student.completed_topics or [])
        if task_id not in completed:
            completed.append(task_id)
            student.completed_topics = completed

        missed = [t for t in (student.missed_topics or []) if t != task_id]
        student.missed_topics = missed
        db.session.commit()

    return redirect(url_for('topic_detail', topic_id=task_id,
                            result='correct' if correct else 'wrong'))
                            
@app.route('/ai-hint', methods=['POST'])
def ai_hint():
    rule = request.form.get('rule', '')
    hint = ai_hints.get(rule, 'Попробуй разбить задачу на шаги и вспомнить правила из видеоурока.')
    return hint

@app.route('/history')
def student_history():
    student_id = session.get('student_id')
    return render_template('history.html', submissions=[], student_name='Ученик', sferum=sferum_context)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# --- TEACHER DASHBOARD API ---
@app.route("/teacher_dashboard")
def teacher_dashboard():
    if "teacher_id" not in session:
        return redirect(url_for("login_page"))
    
    return render_template(
        "teacher.html",
        teacher_name=session.get("teacher_name", "Учитель"),
        teacher_school=session.get("teacher_school", "Не указана"),
        teacher_subject=session.get("teacher_subject", "Русский язык")
    )

@app.route("/api/regions", methods=["GET"])
def get_regions():
    return jsonify({"status": "success", "data": list(REGIONS_DATA.keys())})

@app.route("/api/schools", methods=["GET"])
def get_schools():
    region = request.args.get("region")
    if not region or region not in REGIONS_DATA:
        return jsonify({"status": "error", "message": "Регион не найден"}), 404
    return jsonify({"status": "success", "data": REGIONS_DATA[region]})

@app.route("/api/teacher/topics", methods=["GET"])
def get_topics():
    if "teacher_subject" not in session:
        return jsonify({"status": "error", "message": "Не авторизован"}), 401

    current_subject = session["teacher_subject"]
    topics = TASKS_DATA.get(current_subject, [])
    return jsonify({
        "status": "success",
        "data": [{"id": t["id"], "title": t["title"]} for t in topics]
    })

@app.route('/api/login', methods=['POST'])
def auth_login():
    role = request.form.get('role')
    name = request.form.get('name', '').strip()

    if not name:
        return "Введите фамилию и имя", 400

    if role == 'teacher':
        region = request.form.get('region')
        school = request.form.get('school')
        subject = request.form.get('subject')

        if not (region and school and subject):
            return "Заполните регион, школу и предмет", 400

        teacher = Teacher.query.filter_by(
            name=name, region=region, school=school, subject=subject
        ).first()

        if not teacher:
            teacher = Teacher(
                name=name,
                region=region,
                school=school,
                subject=subject
            )
            db.session.add(teacher)
            db.session.commit()

        session['role'] = 'teacher'
        session['teacher_id'] = teacher.id          
        session['teacher_name'] = teacher.name
        session['teacher_subject'] = teacher.subject
        session['teacher_school'] = teacher.school  
        return redirect(url_for('teacher_dashboard'))

    elif role == 'student':
        student = Student.query.filter_by(name=name).first()
        if not student:
            first_class = SchoolClass.query.first()
            if not first_class:
                return "Сначала нужно создать классы (запусти seed)", 500
            student = Student(
                name=name,
                class_id=first_class.id,
                missed_topics=[101, 201, 301],
                completed_topics=[]
            )
            db.session.add(student)
            db.session.commit()

        session['role'] = 'student'
        session['student_id'] = student.id
        session['student_name'] = student.name
        return redirect(url_for('student_home'))

    else:
        return "Неизвестная роль", 400

    return "Профиль не найден. Проверьте введённые данные.", 401
@app.route("/api/teacher/classes", methods=["GET"])
def get_classes():
    if "teacher_school" not in session:
        return jsonify({"status": "error", "message": "Не авторизован"}), 401
    
    current_school = session["teacher_school"]
    classes = SchoolClass.query.filter_by(school=current_school).all()
    output = [{"id": c.id, "name": c.name} for c in classes]
    return jsonify({"status": "success", "data": output})

@app.route("/api/teacher/students", methods=["GET"])
def get_students():
    if "teacher_id" not in session:
        return jsonify({"status": "error", "message": "Не авторизован"}), 401
        
    class_id = request.args.get("class_id", type=int)
    if not class_id:
        return jsonify({"status": "error", "message": "Не передан class_id"}), 400

    current_teacher_id = session["teacher_id"]
    students = Student.query.filter_by(class_id=class_id).all()
    output = []
    
    for s in students:
        teacher_tasks = Assignment.query.filter_by(
            student_id=s.id, 
            teacher_id=current_teacher_id
        ).all()
        tasks_list = [
            {"id": t.id, "skip_type": t.skip_type, "task_text": t.task_text} 
            for t in teacher_tasks
        ]
        output.append({
            "id": s.id,
            "name": s.name,
            "tasks": tasks_list
        })

    return jsonify({"status": "success", "data": output})

@app.route("/api/teacher/assignment", methods=["POST"])
def create_assignment():
    if "teacher_id" not in session:
        return jsonify({"status": "error", "message": "Не авторизован"}), 401

    data = request.get_json() or {}
    student_id = data.get("student_id")
    topic_id = data.get("topic_id")
    task_text = data.get("task_text", "").strip()

    if not student_id or not topic_id:
        return jsonify({"status": "error", "message": "Нужны student_id и topic_id"}), 400

    topic_title = None
    for items in TASKS_DATA.values():
        for t in items:
            if t["id"] == int(topic_id):
                topic_title = t["title"]
                break

    if not topic_title:
        return jsonify({"status": "error", "message": "Тема не найдена"}), 404

    new_task = Assignment(
        student_id=int(student_id),
        teacher_id=session["teacher_id"],
        topic_id=int(topic_id),
        skip_type="Задание от учителя",
        task_text=task_text or topic_title
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"status": "success", "task_id": new_task.id})

@app.route('/template-check')
def template_check():
    import os
    p = os.path.join(app.root_path, app.template_folder, 'student_dashboard.html')
    exists = os.path.exists(p)
    head = ''
    if exists:
        with open(p, encoding='utf-8') as f:
            head = f.read(500)
    return f"""
    <b>Проект Flask запущен из:</b> {app.root_path}<br>
    <b>Шаблон ищет здесь:</b> {p}<br>
    <b>Файл существует:</b> {exists}<br><br>
    <b>Первые строки файла:</b><pre>{head}</pre>
    """

# --- ЗАПУСК ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_database()
    app.run(host='0.0.0.0', port=8000)