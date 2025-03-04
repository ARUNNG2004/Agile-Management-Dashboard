from flask import Flask, render_template, request, redirect, url_for
import os
import datetime
import matplotlib.pyplot as plt
import sqlite3

app = Flask(__name__, template_folder="templates", static_folder="static")

if not os.path.exists("app/static"):
    os.makedirs("app/static")

sprint_start_date = datetime.date.today()
days = [sprint_start_date + datetime.timedelta(days=i) for i in range(10)]
formatted_dates = [day.strftime("%b %d") for day in days]

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sprint_progress (
        day INTEGER PRIMARY KEY,
        completed_work INTEGER,
        remaining_work INTEGER
    )
    ''')

    conn.commit()
    conn.close()

def fetch_sprint_data():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT completed_work, remaining_work FROM sprint_progress ORDER BY day ASC")
    data = cursor.fetchall()

    conn.close()

    completed_work = [row[0] for row in data]
    remaining_work = [row[1] for row in data]

    return completed_work, remaining_work

def generate_burnup_chart():
    completed_work, _ = fetch_sprint_data()
    total_scope = [35] * len(days)

    plt.figure(figsize=(8, 8))
    plt.plot(formatted_dates, completed_work, marker='o', linestyle='-', color='g', label="Completed Story Points")
    plt.plot(formatted_dates, total_scope, linestyle='--', color='r', label="Total Scope")

    plt.xlabel("Sprint Timeline")
    plt.ylabel("Story Points Completed")
    plt.title("Sprint Burnup Chart")
    plt.xticks(rotation=45, fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(True)
    plt.legend(loc="upper left", bbox_to_anchor=(1, 1))

    burnup_path = os.path.join("app/static", "burnup_chart.png")
    plt.savefig(burnup_path, bbox_inches="tight")
    plt.close()

    return burnup_path

def generate_burndown_chart():
    _, remaining_work = fetch_sprint_data()

    plt.figure(figsize=(8, 8))
    plt.plot(formatted_dates, remaining_work, marker='o', linestyle='-', color='b', label="Remaining Story Points")

    plt.xlabel("Sprint Timeline")
    plt.ylabel("Story Points Remaining")
    plt.title("Sprint Burndown Chart")
    plt.xticks(rotation=45, fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(True)
    plt.legend(loc="upper left", bbox_to_anchor=(1, 1))

    burndown_path = os.path.join("app/static", "burndown_chart.png")
    plt.savefig(burndown_path, bbox_inches="tight")
    plt.close()

    return burndown_path

@app.route("/update", methods=["POST"])
def update_data():
    day = int(request.form["day"])
    completed_work = int(request.form["completed_work"])
    remaining_work = int(request.form["remaining_work"])

    conn = sqlite3.connect("users.db")
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

@app.route("/")
def index():
    burnup_chart = "static/burnup_chart.png"
    burndown_chart = "static/burndown_chart.png"
    return render_template("index.html", burnup_chart=burnup_chart, burndown_chart=burndown_chart)

if __name__ == "__main__":
    init_db()
    generate_burnup_chart()
    generate_burndown_chart()
    app.run(debug=True)
