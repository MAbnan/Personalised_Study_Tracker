from flask import Flask, render_template_string, redirect, url_for, request, session, Blueprint, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from textblob import TextBlob
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from sklearn.preprocessing import LabelEncoder
import random

# Initialize Flask app and database
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_tracker.db'
db = SQLAlchemy(app)

# AI Model Setup
X = np.array([[i] for i in range(1, 11)])
y = [
    "Light review and 1 practice quiz",
    "Topic-focused revision + 2 practice problems",
    "Revise weak points + daily quizzes",
    "Practice test + concept videos",
    "Timed study sessions + review notes",
    "Mock test + doubt clearing",
    "Mixed problem solving + flashcards",
    "Intensive revision + 1 mock exam",
    "Full syllabus review + test simulation",
    "Daily mock tests + active recall"
]
le = LabelEncoder()
y_encoded = le.fit_transform(y)

model = Sequential([
    Dense(10, input_dim=1, activation='relu'),
    Dense(20, activation='relu'),
    Dense(10, activation='softmax')
])
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.fit(X, y_encoded, epochs=300, verbose=0)

def get_study_recommendation(hours: int) -> str:
    inp = np.array([[hours]])
    pred = model.predict(inp, verbose=0)
    return le.inverse_transform([np.argmax(pred)])[0]

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class StudyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject = db.Column(db.String(100))
    hours_per_day = db.Column(db.Integer)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date, nullable=True)
    user = db.relationship('User', backref=db.backref('study_plans', lazy=True))

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(5), nullable=False)

# Utility Functions
def correct_spelling(text):
    return str(TextBlob(text).correct())

def generate_study_suggestion(subject, hours):
    if hours < 1:
        return f"Try to dedicate at least 1 hour daily to {subject} for consistency."
    elif hours < 2:
        return f"{subject} is important. Consider increasing your study time gradually."
    elif hours >= 4:
        return f"You're investing a lot in {subject}. Make sure to include breaks to avoid burnout!"
    else:
        return f"A solid {hours} hours daily for {subject} sounds like a good balance."

# Blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
main_bp = Blueprint('main', __name__)

# Routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_guest'] = False
            return redirect(url_for('main.dashboard'))
        error = 'Invalid email or password. Please try again.'
    return render_template_string(login_template, error=error)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already exists. Please log in.', 'warning')
            return redirect(url_for('auth.signup'))
        hashed_password = generate_password_hash(password)
        db.session.add(User(name=name, email=email, password=hashed_password))
        db.session.commit()
        return redirect(url_for('auth.login'))
    return render_template_string(signup_template)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@main_bp.route('/')
def index():
    return render_template_string(index_template)

@main_bp.route('/dashboard')
def dashboard():
    user = {'name': 'Guest'} if session.get('is_guest') else User.query.get(session.get('user_id'))
    study_plan = None if session.get('is_guest') else StudyPlan.query.filter_by(user_id=session.get('user_id')).all()
    return render_template_string(dashboard_template, user=user, study_plan=study_plan)

@main_bp.route('/study_plan', methods=['GET', 'POST'])
def study_plan():
    recommendation = None
    if request.method == 'POST':
        subject = correct_spelling(request.form.get('subject'))
        try:
            hours = int(request.form.get('hours'))
            recommendation = f"For <strong>{subject}</strong>, we recommend: <em>{get_study_recommendation(hours)}</em>"
        except ValueError:
            recommendation = "Please enter a valid number for study hours."
    return render_template_string(study_plan_template, recommendation=recommendation)

@main_bp.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if request.method == 'POST':
        db.session.add(Reminder(task=request.form['task'], date=request.form['date'], time=request.form['time']))
        db.session.commit()
        return redirect(url_for('main.reminders'))
    return render_template_string(reminders_template, reminders=Reminder.query.all())

@main_bp.route('/all_reminders')
def all_reminders():
    return render_template_string(all_reminders_template, reminders=Reminder.query.all())

@main_bp.route('/progress-tracking', methods=['GET', 'POST'])
def progress_tracking():
    global study_progress_db
    if request.method == 'POST':
        study_progress_db.append({"date": datetime.now().strftime("%Y-%m-%d"), "hours": int(request.form['hours_studied'])})
    progress_data = {"dates": [entry["date"] for entry in study_progress_db], "hours": [entry["hours"] for entry in study_progress_db]}
    return render_template_string(progress_tracking_template, progress_data=progress_data)

@main_bp.route('/motivational-tips', methods=['GET', 'POST'])
def motivational_tips():
    tip = random.choice(motivational_tips_list) if request.method == 'POST' else None
    return render_template_string(motivational_tips_template, tip=tip)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)

# Run
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
