from flask import Flask, redirect, request, url_for
import os
import datetime
import matplotlib.pyplot as plt
import sqlite3  

app = Flask(__name__, template_folder="templates", static_folder="static")

if not os.path.exists("static"):
    os.makedirs("static")

DB_PATH = os.path.abspath("users.db")

sprint_start_date = datetime.date.today()
days = [sprint_start_date + datetime.timedelta(days=i) for i in range(10)]
formatted_dates = [day.strftime("%b %d") for day in days]

def fetch_sprint_data():
    """Fetch sprint progress data from the existing database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch data in ascending order of days
    cursor.execute("SELECT day, completed_work, remaining_work FROM sprint_progress ORDER BY day ASC")
    data = cursor.fetchall()
    
    conn.close()
    
    # Debugging: Print fetched data to verify
    print("Fetched Data from DB:", data)  

    # Initialize lists with default 0 values
    completed_work = [0] * len(formatted_dates)
    remaining_work = [0] * len(formatted_dates)

    for row in data:
        day_index = row[0] - 1  
        if 0 <= day_index < len(formatted_dates):  
            completed_work[day_index] = row[1]
            remaining_work[day_index] = row[2]

    return completed_work, remaining_work

def generate_burnup_chart():
    """Generate and save the Sprint Burnup Chart."""
    completed_work, _ = fetch_sprint_data()
    total_scope = [35] * len(formatted_dates) 
    plt.figure(figsize=(8, 6))
    plt.plot(formatted_dates, completed_work, marker='o', linestyle='-', color='g', label="Completed Story Points")
    plt.plot(formatted_dates, total_scope, linestyle='--', color='r', label="Total Scope")

    plt.xlabel("Sprint Timeline")
    plt.ylabel("Story Points Completed")
    plt.title("Sprint Burnup Chart")
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True)
    plt.legend(loc="upper left")

    burnup_path = os.path.join("static", "burnup_chart.png")
    plt.savefig(burnup_path, bbox_inches="tight")
    plt.close()

    return burnup_path  

def generate_burndown_chart():
    """Generate and save the Sprint Burndown Chart."""
    _, remaining_work = fetch_sprint_data()

    plt.figure(figsize=(8, 6))
    plt.plot(formatted_dates, remaining_work, marker='o', linestyle='-', color='b', label="Remaining Story Points")

    plt.xlabel("Sprint Timeline")
    plt.ylabel("Story Points Remaining")
    plt.title("Sprint Burndown Chart")
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True)
    plt.legend(loc="upper left")

    burndown_path = os.path.join("static", "burndown_chart.png")
    plt.savefig(burndown_path, bbox_inches="tight")
    plt.close()

    return burndown_path

@app.route("/update", methods=["POST"])
def update_data():
    """Update the sprint progress data in the existing database."""
    day = int(request.form["day"])
    completed_work = int(request.form["completed_work"])
    remaining_work = int(request.form["remaining_work"])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sprint_progress WHERE day = ?", (day,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("UPDATE sprint_progress SET completed_work = ?, remaining_work = ? WHERE day = ?", 
                       (completed_work, remaining_work, day))
    else:
        cursor.execute("INSERT INTO sprint_progress (day, completed_work, remaining_work) VALUES (?, ?, ?)", 
                       (day, completed_work, remaining_work))

    conn.commit()
    conn.close()

    generate_burnup_chart()
    generate_burndown_chart()

    return redirect(url_for("index"))

@app.route("/debug")
def debug():
    conn = sqlite3.connect(DB_PATH)
    
