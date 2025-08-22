from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os, random

# Instance dir for SQLite away from System32
instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
os.makedirs(instance_dir, exist_ok=True)

app = Flask(__name__, instance_path=instance_dir)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_dir, 'quiz.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey-change-me'

db = SQLAlchemy(app)

# Models
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    question_type = db.Column(db.String(10), nullable=False)  # 'MCQ', 'TF', 'OPEN'
    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    correct_answer = db.Column(db.String(1))  # A, B, C, D (None/empty for OPEN)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()
    # Seed demo questions if empty
    if Question.query.count() == 0:
        demo = [
            # MCQs
            Question(question_text="Cual de las tabuelas es clarividente",
                     question_type="MCQ",
                     option_a="Chela", option_b="Aurora", option_c="Margarita", option_d="Lucila",
                     correct_answer="B"),
            Question(question_text="Cual es el apellido de Uli",
                     question_type="MCQ",
                     option_a="Mendez", option_b="Espina", option_c="Reyes", option_d="Manzano",
                     correct_answer="B"),
            Question(question_text="Que significa el DMA",
                     question_type="MCQ",
                     option_a="Decalogo Mejores Amigas", option_b="Diez Maneras de matar Abejas", option_c="Diario mejores amistades", option_d="Diagrama mejores Amistades",
                     correct_answer="A"),
            Question(question_text="¿Que rol cumple Emiliano en Creta?",
                     question_type="MCQ",
                     option_a="Director artistico", option_b="Bajista", option_c="Baterista", option_d="Vocalista",
                     correct_answer="D"),
            Question(question_text="¿Cuantos Hermanos tiene Uli?",
                     question_type="MCQ",
                     option_a="2", option_b="5", option_c="1", option_d="3",
                     correct_answer="D"),
            Question(question_text="¿De que murio Nicolas?",
                     question_type="MCQ",
                     option_a="Síndrome de muerte súbita del lactante", option_b="SARS", option_c="Meningitis", option_d="Leucemia",
                     correct_answer="C"),
            Question(question_text="Quien era el novio de Isabel",
                     question_type="MCQ",
                     option_a="Paulo", option_b="Leo", option_c="Emanuel", option_d="No tenia pareja",
                     correct_answer="B"),
            Question(question_text="En que Curso quedaron Niki y Uli?",
                     question_type="MCQ",
                     option_a="1C", option_b="2B", option_c="3C", option_d="6A",
                     correct_answer="C"),
            Question(question_text="¿Quien le gustaba a Paulo?",
                     question_type="MCQ",
                     option_a="Simon", option_b="Lucila", option_c="Marcia", option_d="Margarita",
                     correct_answer="A"),
            Question(question_text="¿Quien le gustaba a Uli?",
                     question_type="MCQ",
                     option_a="Paulo", option_b="Emi", option_c="Horacio", option_d="Simon",
                     correct_answer="A"),            
            # True/False
            Question(question_text="La familia de Paulo reconoce algo bueno de el.",
                     question_type="TF",
                     option_a="Verdadero", option_b="Falso",
                     correct_answer="B"),
            Question(question_text="Nicole es hija unica",
                     question_type="TF",
                     option_a="Verdadero", option_b="Falso",
                     correct_answer="B"),
            Question(question_text="Las tabuelas se llaman Chela y Aurora",
                     question_type="TF",
                     option_a="Verdadero", option_b="Falso",
                     correct_answer="B"),
            Question(question_text="Leonel no le fue infiel a Isabel",
                     question_type="TF",
                     option_a="Verdadero", option_b="Falso",
                     correct_answer="B"),
            Question(question_text="Lucila Hace Atletismo.",
                     question_type="TF",
                     option_a="Verdadero", option_b="Falso",
                     correct_answer="A"),
            # OPEN (skipped in scoring)
            Question(question_text="Nombra a los amigos de Julieta.",
                     question_type="OPEN"),
            Question(question_text="Qué edad tiene Juli en la historia?",
                     question_type="OPEN"),
        ]
        db.session.add_all(demo)
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session.clear()
        session['name'] = request.form.get('name', 'Anonymous')
        ids = [q.id for q in Question.query.all()]
        random.shuffle(ids)
        session['order'] = ids
        session['i'] = 0
        session['score'] = 0
        session['saved'] = False
        return redirect(url_for('play'))
    return render_template('index.html')

@app.route('/play', methods=['GET', 'POST'])
def play():
    order = session.get('order', [])
    i = session.get('i', 0)

    # If finished, go to leaderboard (and save there)
    if not order or i >= len(order):
        return redirect(url_for('leaderboard'))

    q = Question.query.get(order[i])

    if request.method == 'POST':
        # Auto-advance after processing answer
        if q.question_type != 'OPEN':
            answer = request.form.get('answer', '').strip().upper()
            if q.correct_answer and answer == q.correct_answer:
                session['score'] = session.get('score', 0) + 1

        session['i'] = i + 1
        return redirect(url_for('play'))

    return render_template('question.html', question=q, index=i+1, total=len(order))

@app.route('/leaderboard')
def leaderboard():
    # Save score once
    if not session.get('saved') and 'name' in session:
        s = Score(name=session.get('name', 'Anonymous'),
                  score=session.get('score', 0))
        db.session.add(s)
        db.session.commit()
        session['saved'] = True

    scores = Score.query.order_by(Score.score.desc()).all()
    return render_template('leaderboard.html',
                           scores=scores,
                           name=session.get('name', 'Anonymous'),
                           score=session.get('score', 0))

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 locally if PORT not set
    app.run(host="0.0.0.0", port=port)

