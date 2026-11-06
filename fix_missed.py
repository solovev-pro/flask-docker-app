from app import app, db, Student

with app.app_context():
    for s in Student.query.all():
        s.missed_topics = [101, 201, 301]
        s.completed_topics = []  
    db.session.commit()
    print("Готово: всем ученикам добавлены темы 101, 201, 301 как пропущенные")