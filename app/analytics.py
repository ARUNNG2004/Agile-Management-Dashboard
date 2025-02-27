from flask import Flask, render_template
import os
import datetime
import matplotlib.pyplot as plt

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")

if not os.path.exists("app/static"):
    os.makedirs("app/static")

sprint_start_date = datetime.date.today()
days = [sprint_start_date + datetime.timedelta(days=i) for i in range(10)]
formatted_dates = [day.strftime("%b %d") for day in days]

def generate_burnup_chart():
    completed_work = [2, 5, 8, 12, 15, 19, 22, 27, 30, 35]
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
    remaining_work = [35, 30, 27, 24, 20, 18, 14, 10, 5, 0]
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

@app.route("/")
def index():
    burnup_chart = "static/burnup_chart.png"
    burndown_chart = "static/burndown_chart.png"
    return render_template("index.html", burnup_chart=burnup_chart, burndown_chart=burndown_chart)

if __name__ == "__main__":
    generate_burnup_chart()  
    generate_burndown_chart()
    app.run(debug=True)
