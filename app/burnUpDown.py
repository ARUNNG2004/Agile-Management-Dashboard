from flask import Flask, render_template
import matplotlib.pyplot as plt
import os
import datetime

app = Flask(__name__)

if not os.path.exists("static"):
    os.makedirs("static")

sprint_start_date = datetime.date.today()  # Start from today's date
days = [sprint_start_date + datetime.timedelta(days=i) for i in range(10)]  # 10-day sprint
formatted_dates = [day.strftime("%b %d") for day in days]  # Format: "Feb 9", "Feb 10", etc.

def generate_burnup_chart():
    """Generate and save a burnup chart with exact dates on x-axis and legend outside."""
    completed_work = [2, 5, 8, 12, 15, 19, 22, 27, 30, 35]  # Work completed per day
    total_scope = [35] * len(days)  # Fixed total scope

    plt.figure(figsize=(8, 8))
    plt.plot(formatted_dates, completed_work, marker='o', linestyle='-', color='g', label="Completed Story Points")
    plt.plot(formatted_dates, total_scope, linestyle='--', color='r', label="Total Scope")

    plt.xlabel("Sprint Timeline")
    plt.ylabel("Story Points Completed")
    plt.title("Sprint Burnup Chart")
    plt.xticks(rotation=45, fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(True)

    # Move the legend outside the graph
    plt.legend(loc="upper left", bbox_to_anchor=(1, 1))  

    burnup_path = os.path.join(app.root_path, "static", "burnup_chart.png")

    plt.savefig(burnup_path, bbox_inches="tight")  # Prevent label cutoff
    plt.close()
    
    return burnup_path

def generate_burndown_chart():
    """Generate and save a burndown chart with exact dates on x-axis and legend outside."""
    remaining_work = [35, 30, 27, 24, 20, 18, 14, 10, 5, 0]  # Remaining work

    plt.figure(figsize=(8, 8))
    plt.plot(formatted_dates, remaining_work, marker='o', linestyle='-', color='b', label="Remaining Story Points")

    plt.xlabel("Sprint Timeline")
    plt.ylabel("Story Points Remaining")
    plt.title("Sprint Burndown Chart")
    plt.xticks(rotation=45, fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(True)

    # Move the legend outside the graph
    plt.legend(loc="upper left", bbox_to_anchor=(1, 1))  
    
    burndown_path = os.path.join(app.root_path, "static", "burndown_chart.png")

    plt.savefig(burndown_path, bbox_inches="tight")
    plt.close()

    return burndown_path

@app.route("/")
def index():
    burnup_chart = generate_burnup_chart()
    burndown_chart = generate_burndown_chart()
    return render_template("index.html", burnup_chart=burnup_chart, burndown_chart=burndown_chart)

if __name__ == "__main__":
    app.run(debug=True)
