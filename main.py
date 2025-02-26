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
    """Generate and save a burnup chart."""
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

generate_burnup_chart()

@app.route("/")
def index():
    return render_template("index.html") 

if __name__ == "__main__":
    app.run(debug=True)
