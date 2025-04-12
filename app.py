from flask import Flask, render_template_string,render_template, redirect, url_for, request, session, Blueprint
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import flash
from textblob import TextBlob
# deep_model.py
# study_plan_model.py
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from sklearn.preprocessing import LabelEncoder

# Training data (dummy)
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
    label_index = np.argmax(pred)
    return le.inverse_transform([label_index])[0]

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_tracker.db'
db = SQLAlchemy(app)

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

# Templates
study_plan_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personalized Study Plan</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <h1>📘 Personalized Study Plan</h1>
    </header>

    <section>
        <p>Get AI-powered study recommendationssss based on your subject and available study hours!</p>

        <form action="{{ url_for('main.study_plan') }}" method="POST">
            <label for="subject">Subject:</label>
            <input type="text" name="subject" id="subject" required>

            <label for="hours">Study Hours per Day:</label>
            <input type="number" name="hours" id="hours" min="1" max="12" required>

            <button type="submit">Generate Study Plan</button>
        </form>

        {% if recommendation %}
        <div class="study-plan-card">
            <h2>🧠 AI-Recommended Study Plan:</h2>
            <p>{{ recommendation | safe }}</p>
        </div>
        {% endif %}
    </section>

    <footer>
        <a href="{{ url_for('main.dashboard') }}">Back to Dashboard</a>
    </footer>
</body>
</html>
'''
motivational_tips_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Motivational Tips</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <h1>💡 Motivational Tips</h1>
    </header>

    <section>
        <p>Boost your motivation with insightful tips to stay focused and productive!</p>

        <form action="{{ url_for('main.motivational_tips') }}" method="POST">
            <button type="submit">Get a Motivational Tip</button>
        </form>

        {% if tip %}
        <div class="motivation-card">
            <p>{{ tip }}</p>
        </div>
        {% endif %}
    </section>

    <footer>
        <a href="{{ url_for('main.dashboard') }}">Back to Dashboard</a>
    </footer>
</body>
</html>
'''
progress_tracking_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Progress Tracking</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <h2>Track Your Progress</h2>
    <form method="POST">
        Subject: <input type="text" name="subject" required><br>
        Hours Studied: <input type="number" name="hours_studied" required><br>
        <button type="submit">Submit</button>
    </form>

    <canvas id="progressChart" width="400" height="200"></canvas>

    <button onclick="downloadCSV()">Export CSV</button>

    <script>
        const dates = {{ progress_data['dates']|tojson }};
        const hours = {{ progress_data['hours']|tojson }};

        const ctx = document.getElementById('progressChart').getContext('2d');
        const progressChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Study Hours per Day',
                    data: hours,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    fill: false,
                    tension: 0.2
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        stepSize: 1
                    }
                }
            }
        });

        function downloadCSV() {
            let csv = "Date,Hours\\n";
            for (let i = 0; i < dates.length; i++) {
                csv += `${dates[i]},${hours[i]}\\n`;
            }

            const blob = new Blob([csv], { type: 'text/csv' });
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = "study_progress.csv";
            link.click();
        }
    </script>
    <footer>
        <a href="{{ url_for('main.dashboard') }}">Back to Dashboard</a>
    </footer>
</body>
</html>
'''
question_papers_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Question Paper Repository</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <h1>📄 Question Paper Repository</h1>
    </header>

    <section>
        <p>Download previous years' question papers to enhance your preparation.</p>

        <form action="{{ url_for('main.question_papers') }}" method="POST">
            <label for="subject">Select Subject:</label>
            <select id="subject" name="subject" required>
                <option value="math">Mathematics</option>
                <option value="physics">Physics</option>
                <option value="chemistry">Chemistry</option>
                <option value="computer_science">Computer Science</option>
                <option value="engineering">Engineering</option>
            </select>

            <button type="submit">Get Papers</button>
        </form>

        {% if question_papers %}
        <h2>Available Question Papers</h2>
        <ul>
            {% for paper in question_papers %}
            <li><a href="{{ paper.link }}" target="_blank">{{ paper.name }}</a></li>
            {% endfor %}
        </ul>
        {% endif %}
    </section>

    <footer>
        <a href="{{ url_for('main.dashboard') }}">Back to Dashboard</a>
    </footer>
</body>
</html>
'''
internships_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Internship Opportunities</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <h1>🧪 Internship Opportunities</h1>
    </header>

    <section>
        <p>Find the best internship opportunities to boost your career.</p>

        <form action="{{ url_for('main.internships') }}" method="POST">
            <label for="field">Select Field:</label>
            <select id="field" name="field" required>
                <option value="software">Software Development</option>
                <option value="data_science">Data Science</option>
                <option value="cybersecurity">Cybersecurity</option>
                <option value="marketing">Marketing</option>
            </select>

            <button type="submit">Find Internships</button>
        </form>

        {% if internships %}
        <h2>Recommended Internships</h2>
        <ul>
            {% for internship in internships %}
            <li><a href="{{ internship.link }}" target="_blank">{{ internship.name }}</a></li>
            {% endfor %}
        </ul>
        {% endif %}
    </section>

    <footer>
        <a href="{{ url_for('main.dashboard') }}">Back to Dashboard</a>
    </footer>
</body>
</html>
'''
online_classes_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Online Classes</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <h1>📺 Online Classes</h1>
    </header>

    <section>
        <p>Explore the best online courses from various platforms.</p>

        <form action="{{ url_for('main.online_classes') }}" method="POST">
            <label for="category">Select Category:</label>
            <select id="category" name="category" required>
                <option value="programming">Programming</option>
                <option value="math">Mathematics</option>
                <option value="science">Science</option>
                <option value="business">Business</option>
            </select>

            <button type="submit">Find Classes</button>
        </form>

        {% if classes %}
        <h2>Recommended Online Classes</h2>
        <ul>
            {% for course in classes %}
            <li><a href="{{ course.link }}" target="_blank">{{ course.name }}</a></li>
            {% endfor %}
        </ul>
        {% endif %}
    </section>

    <footer>
        <a href="{{ url_for('main.dashboard') }}">Back to Dashboard</a>
    </footer>
</body>
</html>
'''
study_materials_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Study Materials</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <h1>📚 Best Study Materials</h1>
    </header>

    <section>
        <p>Find the best study materials, books, and resources to boost your learning.</p>

        <form action="{{ url_for('main.study_materials') }}" method="POST">
            <label for="subject">Select Subject:</label>
            <select id="subject" name="subject" required>
                <option value="math">Mathematics</option>
                <option value="science">Science</option>
                <option value="history">History</option>
                <option value="programming">Programming</option>
            </select>

            <button type="submit">Get Materials</button>
        </form>

        {% if materials %}
        <h2>Recommended Materials</h2>
        <ul>
            {% for material in materials %}
            <li><a href="{{ material.link }}" target="_blank">{{ material.name }}</a></li>
            {% endfor %}
        </ul>
        {% endif %}
    </section>

    <footer>
        <a href="{{ url_for('main.dashboard') }}">Back to Dashboard</a>
    </footer>
</body>
</html>
'''
reminders_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reminders</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <h1>⏰ Exam & Task Reminders</h1>
    </header>

    <section>
        <p>Set reminders for your upcoming exams, assignments, and study sessions.</p>

        <form action="{{ url_for('main.reminders') }}" method="POST">
            <label for="task">Task:</label>
            <input type="text" id="task" name="task" required>

            <label for="date">Date:</label>
            <input type="date" id="date" name="date" required>

            <label for="time">Time:</label>
            <input type="time" id="time" name="time" required>

            <button type="submit">Add Reminder</button>
        </form>

        {% if reminders %}
        <h2>Your Reminders</h2>
        <ul>
            {% for reminder in reminders %}
            <li>{{ reminder.task }} - {{ reminder.date }} at {{ reminder.time }}</li>
            {% endfor %}
        </ul>
        {% endif %}
         <button onclick="window.location.href='{{ url_for('main.all_reminders') }}'">Show All Reminders</button>
    </section>

    <footer>
        <a href="{{ url_for('main.dashboard') }}">Back to Dashboard</a>
    </footer>
</body>
</html>
'''
all_reminders_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>All Reminders</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <h1>📅 All Reminders</h1>
    </header>

    <section>
        {% if reminders %}
        <ul>
            {% for reminder in reminders %}
            <li>{{ reminder.task }} - {{ reminder.date }} at {{ reminder.time }}</li>
            {% endfor %}
        </ul>
        {% else %}
        <p>No reminders found.</p>
        {% endif %}
    </section>

    <footer>
        <a href="{{ url_for('main.reminders') }}">Back to Reminders</a>
    </footer>
</body>
</html>
'''
index_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Study Tracker - Home</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      background-color: #0f0f1b;
      color: #e0e0e0;
      font-family: 'Segoe UI', sans-serif;
      margin: 0;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px 40px;
      background-color: #111122;
      border-bottom: 1px solid #1f1f2e;
    }
    .logo {
      font-size: 1.8rem;
      color: #00ffff;
      text-shadow: 0 0 5px #00ffff;
    }
    nav a {
      color: #00ffff;
      margin-left: 20px;
      text-decoration: none;
      font-weight: bold;
    }
    .hero {
      text-align: center;
      padding: 100px 20px;
    }
    .hero h1 {
      font-size: 3rem;
      color: #00ffff;
      text-shadow: 0 0 10px #00ffff;
    }
    .hero p {
      font-size: 1.2rem;
      max-width: 600px;
      margin: 0 auto 30px;
    }
    .buttons a {
      display: inline-block;
      background: #00ffff;
      color: #0f0f1b;
      padding: 12px 25px;
      margin: 10px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: bold;
      box-shadow: 0 0 10px #00ffff;
    }
    footer {
      text-align: center;
      padding: 20px;
      background: #111122;
      color: #777;
    }
  </style>
</head>
<body>
  <header>
    <div class="logo">StudyTracker</div>
    <nav>
        <a href="{{ url_for('auth.login') }}">Login</a>
        <a href="{{ url_for('auth.signup') }}">Sign Up</a>
        <a href="{{ url_for('auth.guest_login') }}">Guest</a>

    </nav>
  </header>

  <section class="hero">
    <h1>Welcome to Your Personalized Study Tracker</h1>
    <p>Plan smart. Track consistently. Achieve more.</p>
    <div class="buttons">
      <a href="{{ url_for('auth.signup') }}">Get Started</a>
      <a href="{{ url_for('auth.guest_login') }}">Try as Guest</a>
    </div>
  </section>

  <footer>
    &copy; {{ 2025 }} Muhammed abnan - StudyTracker
  </footer>
</body>
</html>
'''
login_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Login - Study Tracker</title>
  <style>
    body {
      background: #0f0f1b;
      color: #fff;
      font-family: 'Segoe UI', sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      overflow: hidden;
    }
    form {
      background: #111122;
      padding: 40px;
      border-radius: 10px;
      box-shadow: 0 0 15px #00ffffaa;
      animation: fadeIn 1s ease-in-out;
      width: 300px;
    }
    h2 {
      color: #00ffff;
      margin-bottom: 20px;
      text-align: center;
    }
    input {
      display: block;
      width: 100%;
      padding: 10px;
      margin-bottom: 15px;
      border: none;
      border-radius: 5px;
      outline: none;
      transition: box-shadow 0.3s ease;
    }
    input:focus {
      box-shadow: 0 0 8px 2px #00ffffaa;
      background-color: #1a1a2e;
      color: #fff;
    }
    button {
      background: #00ffff;
      border: none;
      padding: 10px;
      width: 100%;
      border-radius: 5px;
      font-weight: bold;
      color: #000;
      cursor: pointer;
      transition: background 0.3s ease, transform 0.2s ease;
    }
    button:hover {
      background: #00dddd;
      transform: scale(1.03);
    }
    a {
      color: #00ffff;
      text-decoration: none;
      display: block;
      margin-top: 15px;
      text-align: center;
    }
    .error {
      color: #ff4d4d;
      margin-bottom: 15px;
      text-align: center;
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(-30px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  </style>
</head>
<body>
  <form action="{{ url_for('auth.login') }}" method="POST">
    <h2>Login</h2>
    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}
    <input type="email" name="email" placeholder="Enter your email" required>
    <input type="password" name="password" placeholder="Enter your password" required>
    <button type="submit">Login</button>
    <a href="{{ url_for('auth.signup') }}">Don't have an account? Sign up</a>
  </form>
</body>
</html>

'''
signup_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sign Up - Study Tracker</title>
  <style>
    body {
      background: #0f0f1b;
      color: #fff;
      font-family: 'Segoe UI', sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
    }
    form {
      background: #111122;
      padding: 40px;
      border-radius: 10px;
      box-shadow: 0 0 10px #00ffff;
    }
    h2 {
      color: #00ffff;
      margin-bottom: 20px;
    }
    input {
      display: block;
      width: 100%;
      padding: 10px;
      margin-bottom: 15px;
      border: none;
      border-radius: 5px;
    }
    button {
      background: #00ffff;
      border: none;
      padding: 10px;
      width: 100%;
      border-radius: 5px;
      font-weight: bold;
      color: #000;
    }
    a {
      color: #00ffff;
      text-decoration: none;
      display: block;
      margin-top: 10px;
      text-align: center;
    }
  </style>
</head>
<body>
  <form method="POST">
    <h2>Sign Up</h2>
    <input type="text" name="name" placeholder="name" required/>
    <input type="email" name="email" placeholder="Email" required/>
    <input type="password" name="password" placeholder="Password" required/>
    <button type="submit">Sign Up</button>
    <a href="{{ url_for('auth.login') }}">Already have an account? Login</a>
  </form>
</body>
</html>
'''
performance_input_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Performance Input - Study Tracker</title>
  <style>
    body {
      background-color: #0a0a0a;
      font-family: 'Segoe UI', sans-serif;
      color: #fff;
      margin: 0;
      padding: 0;
    }

    header {
      background-color: #111;
      text-align: center;
      padding: 2rem 1rem;
      border-bottom: 2px solid #0ff;
      box-shadow: 0 2px 10px #0ff55;
    }

    header h1 {
      font-size: 2rem;
      color: #0ff;
      margin: 0;
    }

    section {
      max-width: 500px;
      margin: 2rem auto;
      padding: 2rem;
      background-color: #121212;
      border-radius: 12px;
      box-shadow: 0 0 20px #0ff33;
    }

    .form-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    label {
      font-weight: bold;
      margin-top: 1rem;
      color: #0ff;
    }

    input[type="text"],
    input[type="number"],
    input[type="date"] {
      padding: 10px;
      border-radius: 6px;
      border: 1px solid #444;
      background-color: #1a1a1a;
      color: #fff;
      transition: border 0.3s ease, box-shadow 0.3s ease;
    }

    input:focus {
      outline: none;
      border: 1px solid #0ff;
      box-shadow: 0 0 8px #0ff;
    }

    button {
      padding: 12px;
      margin-top: 1rem;
      background-color: #0ff;
      color: #000;
      font-weight: bold;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      box-shadow: 0 0 10px #0ff, 0 0 20px #0ff inset;
      transition: all 0.3s ease-in-out;
    }

    button:hover {
      background-color: #0cc;
      box-shadow: 0 0 15px #0ff, 0 0 30px #0ff inset;
    }

    .card {
      background-color: #1e1e1e;
      border: 1px solid #0ff;
      padding: 1rem;
      border-radius: 12px;
      margin-top: 1rem;
      box-shadow: 0 0 15px #0ff44;
    }

    .motivation-card h3 {
      margin-top: 0;
      color: #0ff;
    }

    .btn {
      display: inline-block;
      padding: 10px 20px;
      margin-top: 2rem;
      background-color: #0ff;
      color: #000;
      font-weight: bold;
      border-radius: 8px;
      text-decoration: none;
      transition: all 0.3s ease;
      box-shadow: 0 0 8px #0ff, 0 0 16px #0ff inset;
    }

    .btn:hover {
      background-color: #0cc;
      box-shadow: 0 0 12px #0ff, 0 0 24px #0ff inset;
    }

    .fade-in {
      opacity: 0;
      transform: translateY(20px);
      animation: fadeInUp 0.8s ease-out forwards;
    }

    @keyframes fadeInUp {
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    footer {
      text-align: center;
      padding: 1rem;
      background: #111;
      color: #aaa;
      border-top: 2px solid #0ff;
      box-shadow: 0 -2px 10px #0ff55;
      margin-top: 2rem;
    }

    footer a {
      color: #0ff;
      text-decoration: none;
    }

    footer a:hover {
      text-decoration: underline;
    }
    /* Reset and Base Styling */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  
  body {
    font-family: 'Poppins', sans-serif;
    background: #0f0f0f;
    color: #fff;
    scroll-behavior: smooth;
    line-height: 1.6;
    transition: background 0.4s, color 0.4s;
  }
  
  body.light-theme {
    background: #f4f4f4;
    color: #111;
  }
  
  a {
    color: inherit;
    text-decoration: none;
  }
  
  ul {
    list-style: none;
  }
  
  .container {
    width: 90%;
    max-width: 1200px;
    margin: auto;
  }
  
  /* Header and Navbar */
  header {
    background: #111;
    padding: 20px 0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  }
  
  .navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .navbar ul {
    display: flex;
    gap: 20px;
  }
  
  .navbar a {
    padding: 10px 15px;
    transition: background 0.3s;
  }
  
  .navbar a:hover {
    background: #1e1e1e;
    border-radius: 5px;
  }
  
  /* Hero Section */
  .hero {
    padding: 100px 0;
    text-align: center;
  }
  
  .hero h1 {
    font-size: 3rem;
    margin-bottom: 20px;
  }
  
  .hero p {
    font-size: 1.2rem;
    color: #aaa;
  }
  
  .btn {
    display: inline-block;
    padding: 10px 20px;
    margin-top: 20px;
    border-radius: 5px;
    background: #0ff;
    color: #000;
    font-weight: bold;
    transition: background 0.3s, box-shadow 0.3s;
    box-shadow: 0 0 10px #0ff;
  }
  
  .btn:hover {
    background: #0cc;
    box-shadow: 0 0 20px #0cc;
  }
  
  /* Section Styling */
  .section {
    padding: 60px 0;
  }
  
  .section h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 40px;
    color: #0ff;
  }
  
  .card {
    background: #1a1a1a;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    transition: transform 0.3s, box-shadow 0.3s;
  }
  
  .card:hover {
    transform: translateY(-5px);
    box-shadow: 0 0 15px #0ff;
  }
  
  .footer {
    background: #111;
    padding: 20px 0;
    text-align: center;
    font-size: 0.9rem;
    color: #aaa;
  }
  
  /* Form Styling */
  .form-container {
    display: grid;
    grid-template-columns: 1fr;
    gap: 20px;
    padding: 40px 20px;
    background: #1a1a1a;
    border-radius: 10px;
    width: 90%;
    max-width: 600px;
    margin: 50px auto;
    box-shadow: 0 8px 16px rgba(0, 255, 255, 0.1);
    animation: fadeInUp 1s ease-out;
  }
  
  .form-container h2 {
    margin-bottom: 30px;
    color: #0ff;
    font-size: 2rem;
    text-align: center;
  }
  
  .form-container input,
  .form-container textarea,
  .form-container select,
  .form-container button {
    font-family: inherit;
    font-size: 1rem;
    width: 100%;
    max-width: 500px;
    padding: 12px 15px;
    border: none;
    outline: none;
    border-radius: 8px;
    background: #111;
    color: #fff;
    transition: 0.3s ease, box-shadow 0.4s;
  }
  
  .form-container input::placeholder,
  .form-container textarea::placeholder {
    color: #888;
  }
  
  .form-container input:focus,
  .form-container textarea:focus,
  .form-container select:focus {
    background: #1f1f1f;
    box-shadow: 0 0 8px #0ff;
  }
  
  .form-container button {
    background: #0ff;
    color: #000;
    font-weight: bold;
    cursor: pointer;
    transition: background 0.3s, box-shadow 0.3s;
    box-shadow: 0 0 10px #0ff;
  }
  
  .form-container button:hover {
    background: #0cc;
    box-shadow: 0 0 20px #0cc;
  }
  
  /* Theme Toggle */
  .theme-toggle {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #0ff;
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    cursor: pointer;
    box-shadow: 0 0 10px #0ff;
    transition: background 0.3s;
    z-index: 1000;
  }
  
  .theme-toggle:hover {
    background: #0cc;
    box-shadow: 0 0 20px #0cc;
  }
  
  /* Animations */
  @keyframes fadeInUp {
    0% {
      opacity: 0;
      transform: translateY(30px);
    }
    100% {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .fade-in {
    animation: fadeInUp 1s ease-out forwards;
    opacity: 0;
  }
  /* Base Styles */
body {
    background-color: #0f0f0f;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
    margin: 0;
    padding: 0;
    line-height: 1.6;
}

/* Header */
header {
    background: linear-gradient(90deg, #0ff1ce, #6a5acd);
    color: #fff;
    padding: 1rem;
    text-align: center;
    border-bottom: 2px solid #00ffff;
    box-shadow: 0 0 10px #00ffff;
}

h1 {
    margin: 0;
    font-size: 2rem;
    text-shadow: 0 0 8px #00ffff;
}

/* Section Styling */
section {
    padding: 2rem;
    max-width: 800px;
    margin: auto;
    background: rgba(20, 20, 20, 0.9);
    border-radius: 10px;
    box-shadow: 0 0 12px rgba(0, 255, 255, 0.3);
}

/* Form Styling */
form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

input, select {
    padding: 0.6rem;
    border: 2px solid #00ffff;
    border-radius: 6px;
    background-color: #1e1e1e;
    color: #fff;
    transition: all 0.3s ease;
}

input:focus, select:focus {
    outline: none;
    box-shadow: 0 0 10px #00ffff;
    border-color: #00ffff;
}

button {
    padding: 0.7rem;
    background-color: #00ffff;
    border: none;
    border-radius: 6px;
    color: #000;
    font-weight: bold;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.3s;
}

button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 12px #00ffff, 0 0 20px #00ffff inset;
}

/* Cards */
.study-plan-card,
.motivation-card {
    margin-top: 1.5rem;
    padding: 1.2rem;
    background: #121212;
    border-left: 4px solid #00ffff;
    border-radius: 8px;
    box-shadow: 0 0 12px rgba(0, 255, 255, 0.3);
}

/* Lists */
ul {
    list-style: none;
    padding: 0;
}

li {
    margin: 0.5rem 0;
    padding: 0.5rem;
    background: #1a1a1a;
    border-left: 4px solid #00ffff;
    border-radius: 5px;
    transition: background 0.3s ease;
}

li a {
    color: #00ffff;
    text-decoration: none;
    font-weight: bold;
}

li:hover {
    background: #222;
}

/* Footer */
footer {
    text-align: center;
    margin-top: 2rem;
    padding: 1rem;
    border-top: 1px solid #00ffff;
    font-size: 0.9rem;
}

footer a {
    color: #00ffff;
    text-decoration: none;
    transition: color 0.3s ease;
}

footer a:hover {
    color: #0ff1ce;
}

/* Chart Container (Progress) */
canvas {
    max-width: 100%;
    height: 400px !important;
}

/* Smooth Entrances */
section, header, footer {
    animation: fadeInUp 0.6s ease both;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(15px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}


  </style>
</head>
<body>

  <header>
    <h1>📈 Performance Input</h1>
  </header>

  <section>
    <form method="POST" class="form-container fade-in">
      <label for="subject">Subject</label>
      <input type="text" name="subject" id="subject" placeholder="e.g., Mathematics" required>

      <label for="hours">Study Hours per Day</label>
      <input type="number" name="hours" id="hours" min="1" max="12" placeholder="e.g., 4" required>

      <label for="start_date">Start Date</label>
      <input type="date" name="start_date" id="start_date" required>

      <label for="end_date">End Date</label>
      <input type="date" name="end_date" id="end_date">

      {% if suggestion %}
      <div class="card motivation-card">
        <h3>💡 AI Suggestion</h3>
        <p>{{ suggestion }}</p>
        <input type="hidden" name="confirm" value="1">
        <button type="submit">✅ Confirm & Save</button>
      </div>
      {% else %}
      <button type="submit">⚡ Preview Suggestion</button>
      {% endif %}
    </form>

    <div style="text-align:center;">
      <a href="{{ url_for('main.dashboard') }}" class="btn">⬅ Back to Dashboard</a>
    </div>
  </section>

  <footer>
    &copy; <a href="{{ url_for('main.dashboard') }}">Dashboard</a>
  </footer>

</body>
</html>
'''
dashboard_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Dashboard - Study Tracker</title>
  <style>
    body {
      background:linear-gradient(1deg, #0ce3e8, #0f0f1b);
      color: #e0e0e0;
      font-family: 'Segoe UI', sans-serif;
      margin: 0;
      padding: 20px;
    }

    h1 {
      color: #00ffff;
      text-align: center;
      margin-bottom: 30px;
      text-shadow: 0 0 10px #00ffff;
    }

    nav {
      background: #111122;
      padding: 15px;
      margin-bottom: 30px;
      border-radius: 8px;
      text-align: center;
      box-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
    }

    nav a {
      color: #00ffff;
      margin: 0 15px;
      text-decoration: none;
      font-weight: bold;
      transition: color 0.3s ease;
    }

    nav a:hover {
      color: #0ff1ce;
    }

    section {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 50px;
      text-align: center;
    }

    .card {
      background: #1c1c2e;
      padding: 100px 134px;
      border-radius: 10px;
      box-shadow: 0 0 8px #00ffff;
      text-decoration: none;
      font-size: 18px;
      font-weight: bold;
      color: #e0e0e0;
      transition: transform 0.2s, box-shadow 0.2s;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .card:hover {
      transform: scale(1.05);
      box-shadow: 0 0 12px #00ffff, 0 0 20px #00ffff inset;
    }
  </style>
</head>
<body>
  <nav>
    <a href="{{ url_for('main.dashboard') }}">🏠 Home</a>
    <a href="{{ url_for('auth.logout') }}">🚪 Logout</a>
  </nav>

  <h1>Hello, {{ user.name }} 👋</h1>

  <section>
    <a href="{{ url_for('main.study_plan') }}" class="card">📘 Study Plan</a>
    <a href="{{ url_for('main.reminders') }}" class="card">⏰ Reminders</a>
    <a href="{{ url_for('main.study_materials') }}" class="card">📚 Materials</a>
    <a href="{{ url_for('main.online_classes') }}" class="card">📺 Online Classes</a>
    <a href="{{ url_for('main.internships') }}" class="card">🧪 Internships</a>
    <a href="{{ url_for('main.question_papers') }}" class="card">📄 Papers</a>
    <a href="{{ url_for('main.progress_tracking') }}" class="card">📊 Progress</a>
    <a href="{{ url_for('main.motivational_tips') }}" class="card">💡 Motivation</a>
    <a href="{{ url_for('main.performance_input') }}" class="card">📊 Perfomance_Input</a>
  </section>
</body>
</html>
'''
def correct_spelling(text):
    blob = TextBlob(text)
    return str(blob.correct())

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
main_bp = Blueprint('main', __name__)

@app.route('/submit_text', methods=['POST'])
def submit_text():
    raw_text = request.form['user_text']
    corrected_text = correct_spelling(raw_text)

    # Store or display the corrected text
    return render_template('result.html', corrected=corrected_text)

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
        else:
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
        user = User(name=name, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))

    return render_template_string(signup_template)


@auth_bp.route('/guest')
def guest_login():
    session['user_id'] = None
    session['is_guest'] = True
    session['guest_name'] = 'Guest'
    return redirect(url_for('main.dashboard'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@main_bp.route('/')
def index():
    return render_template_string(index_template)

@main_bp.route('/dashboard')
def dashboard():
    if session.get('is_guest'):
        return render_template_string(dashboard_template, user={'name': 'Guest'}, study_plan=None)
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    study_plan = StudyPlan.query.filter_by(user_id=user_id).all()
    return render_template_string(dashboard_template, user=user, study_plan=study_plan)
from textblob import TextBlob

def correct_spelling(text):
    return str(TextBlob(text).correct())

from flask import request, render_template_string
from textblob import TextBlob # or wherever your template is

@main_bp.route('/study_plan', methods=['GET', 'POST'])
def study_plan():
    recommendation = None
    if request.method == 'POST':
        subject = request.form.get('subject')
        hours = request.form.get('hours')

        if subject and hours:
            corrected_subject = str(TextBlob(subject).correct())
            try:
                hours = int(hours)
                ai_plan = get_study_recommendation(hours)
                recommendation = (
                    f"For <strong>{corrected_subject}</strong>, we recommend: <em>{ai_plan}</em>"
                )
            except ValueError:
                recommendation = "Please enter a valid number for study hours."

    return render_template_string(study_plan_template, recommendation=recommendation)

@main_bp.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if request.method == 'POST':
        task = request.form['task']
        date = request.form['date']
        time = request.form['time']

        # Create and save the reminder
        new_reminder = Reminder(task=task, date=date, time=time)
        db.session.add(new_reminder)
        db.session.commit()

        return redirect(url_for('main.reminders'))  # Reload page after saving

    # Retrieve all reminders from the database
    reminder_list = Reminder.query.all()
    return render_template_string(reminders_template, reminders=reminder_list)

    #return render_template_string(reminders_template, reminders=None)

@main_bp.route('/all_reminders')
def all_reminders():
    reminders = Reminder.query.all()  # Fetch all reminders from the database
    return render_template_string(all_reminders_template, reminders=reminders)


# Study Materials Route
@main_bp.route('/study-materials', methods=['GET', 'POST'])
def study_materials():
    materials_db = {
        "math": [
            {"name": "Khan Academy - Math", "link": "https://www.khanacademy.org/math"},
            {"name": "MIT OpenCourseWare - Calculus", "link": "https://ocw.mit.edu/courses/mathematics/"},
        ],
        "science": [
            {"name": "NASA Science", "link": "https://science.nasa.gov/"},
            {"name": "Khan Academy - Science", "link": "https://www.khanacademy.org/science"},
        ],
        "history": [
            {"name": "History.com", "link": "https://www.history.com/"},
            {"name": "BBC History", "link": "https://www.bbc.co.uk/history"},
        ],
        "programming": [
            {"name": "W3Schools - Programming", "link": "https://www.w3schools.com/"},
            {"name": "GeeksforGeeks - Coding", "link": "https://www.geeksforgeeks.org/"},
        ],
    }

    if request.method == 'POST':
        subject = request.form['subject']
        materials = materials_db.get(subject, [])

        return render_template_string(study_materials_template, materials=materials)

    return render_template_string(study_materials_template, materials=None)


@main_bp.route('/online-classes', methods=['GET', 'POST'])
def online_classes():
    courses_db = {
        "programming": [
            {"name": "Harvard CS50 - Introduction to Computer Science", "link": "https://cs50.harvard.edu/"},
            {"name": "Python for Beginners - Udemy", "link": "https://www.udemy.com/course/python-for-beginners/"},
        ],
        "math": [
            {"name": "Khan Academy - Math Courses", "link": "https://www.khanacademy.org/math"},
            {"name": "MIT OpenCourseWare - Math", "link": "https://ocw.mit.edu/courses/mathematics/"},
        ],
        "science": [
            {"name": "Coursera - Science of Well-Being", "link": "https://www.coursera.org/learn/the-science-of-well-being"},
            {"name": "Khan Academy - Science", "link": "https://www.khanacademy.org/science"},
        ],
        "business": [
            {"name": "Harvard Business School - Online Courses", "link": "https://online.hbs.edu/courses/"},
            {"name": "Financial Markets - Yale (Coursera)", "link": "https://www.coursera.org/learn/financial-markets-global"},
        ],
    }

    if request.method == 'POST':
        category = request.form['category']
        classes = courses_db.get(category, [])

        return render_template_string(online_classes_template, classes=classes)

    return render_template_string(online_classes_template, classes=None)

# Internships Route
@main_bp.route('/internships', methods=['GET', 'POST'])
def internships():
    internships_db = {
        "software": [
            {"name": "Google Software Engineering Internship", "link": "https://careers.google.com/internships/"},
            {"name": "Microsoft Internship Program", "link": "https://careers.microsoft.com/students/us/en"},
        ],
        "data_science": [
            {"name": "IBM Data Science Internship", "link": "https://www.ibm.com/employment/"},
            {"name": "Meta Data Science Internship", "link": "https://www.metacareers.com/students"},
        ],
        "cybersecurity": [
            {"name": "Cisco Cybersecurity Internship", "link": "https://www.cisco.com/c/en/us/about/careers.html"},
            {"name": "NSA Cybersecurity Internships", "link": "https://www.intelligencecareers.gov/nsa/students-and-internships"},
        ],
        "marketing": [
            {"name": "Google Digital Marketing Internship", "link": "https://careers.google.com/students/"},
            {"name": "HubSpot Marketing Internship", "link": "https://www.hubspot.com/careers"},
        ],
    }

    if request.method == 'POST':
        field = request.form['field']
        internships = internships_db.get(field, [])

        return render_template_string(internships_template, internships=internships)

    return render_template_string(internships_template, internships=None)


# Question Papers Route
@main_bp.route('/question-papers', methods=['GET', 'POST'])
def question_papers():
    papers_db = {
        "math": [
            {"name": "Mathematics - 2023", "link": "https://example.com/math-2023.pdf"},
            {"name": "Mathematics - 2022", "link": "https://example.com/math-2022.pdf"},
        ],
        "physics": [
            {"name": "Physics - 2023", "link": "https://example.com/physics-2023.pdf"},
            {"name": "Physics - 2022", "link": "https://example.com/physics-2022.pdf"},
        ],
        "chemistry": [
            {"name": "Chemistry - 2023", "link": "https://example.com/chemistry-2023.pdf"},
            {"name": "Chemistry - 2022", "link": "https://example.com/chemistry-2022.pdf"},
        ],
        "computer_science": [
            {"name": "CS - 2023", "link": "https://example.com/cs-2023.pdf"},
            {"name": "CS - 2022", "link": "https://example.com/cs-2022.pdf"},
        ],
        "engineering": [
            {"name": "Engineering - 2023", "link": "https://example.com/engineering-2023.pdf"},
            {"name": "Engineering - 2022", "link": "https://example.com/engineering-2022.pdf"},
        ],
    }

    if request.method == 'POST':
        subject = request.form['subject']
        question_papers = papers_db.get(subject, [])

        return render_template_string(question_papers_template, question_papers=question_papers)

    return render_template_string(question_papers_template, question_papers=None)


# Progress Tracking Route
from datetime import datetime

# Dummy database for tracking study hours
study_progress_db = []

@main_bp.route('/progress-tracking', methods=['GET', 'POST'])
def progress_tracking():
    global study_progress_db

    if request.method == 'POST':
        subject = request.form['subject']
        hours_studied = int(request.form['hours_studied'])
        study_progress_db.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "hours": hours_studied
        })

    # Prepare progress data for chart visualization
    progress_data = {
        "dates": [entry["date"] for entry in study_progress_db],
        "hours": [entry["hours"] for entry in study_progress_db]
    }

    return render_template_string(progress_tracking_template, progress_data=progress_data)


# Motivational Tips Route
import random

motivational_tips_list = [
    "Believe in yourself and all that you are. Know that there is something inside you greater than any obstacle.",
    "Your only limit is your mind. Keep pushing forward!",
    "Success is not final, failure is not fatal: it is the courage to continue that counts.",
    "Don't watch the clock; do what it does—keep going.",
    "The secret to getting ahead is getting started.",
    "Every expert was once a beginner. Keep learning, keep growing!",
    "Small progress is still progress. Never give up!"
]

@main_bp.route('/motivational-tips', methods=['GET', 'POST'])
def motivational_tips():
    tip = None
    if request.method == 'POST':
        tip = random.choice(motivational_tips_list)
    
    return render_template_string(motivational_tips_template, tip=tip)


def generate_study_suggestion(subject, hours):
    if hours < 1:
        return f"Try to dedicate at least 1 hour daily to {subject} for consistency."
    elif hours < 2:
        return f"{subject} is important. Consider increasing your study time gradually."
    elif hours >= 4:
        return f"You're investing a lot in {subject}. Make sure to include breaks to avoid burnout!"
    else:
        return f"A solid {hours} hours daily for {subject} sounds like a good balance."

@main_bp.route('/performance-input', methods=['GET', 'POST'])
def performance_input():
    if request.method == 'POST':
        subject = request.form.get('subject')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        try:
            hours = int(request.form.get('hours'))
        except (ValueError, TypeError):
            flash("Please enter a valid number of hours.", "danger")
            return render_template_string(performance_input_template, suggestion=None)

        if not subject or not start_date:
            flash("Please fill in all required fields.", "danger")
            return render_template_string(performance_input_template, suggestion=None)

        if request.form.get('confirm') == '1':
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None

            if session.get('is_guest'):
                flash("Guest users cannot save plans.", "warning")
                return redirect(url_for('main.dashboard'))

            new_plan = StudyPlan(
                user_id=session['user_id'],  # Make sure this is set in session
                subject=subject,
                hours_per_day=hours,
                start_date=start_date_obj,
                end_date=end_date_obj
            )
            db.session.add(new_plan)
            db.session.commit()
            flash("Study plan saved successfully!", "success")
            return redirect(url_for('main.dashboard'))
        else:
            suggestion = generate_study_suggestion(subject, hours)
            return render_template_string(performance_input_template,
                                   subject=subject,
                                   hours=hours,
                                   suggestion=suggestion,
                                   start_date=start_date,
                                   end_date=end_date)

    return render_template_string(performance_input_template, suggestion=None)


# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)

# Run
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
