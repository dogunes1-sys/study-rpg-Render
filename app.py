import os
import random
import datetime
from flask import Flask, render_template, request, redirect, session
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------- DATA STORAGE ----------
users = {}

# ---------- TASKS ----------
TASKS = {
    "branch": {"name": "Branş Deneme", "coin": 35, "xp": 10},
    "topic": {"name": "Konu Bitirme", "coin": 150, "xp": 45},
    "ayt": {"name": "AYT Deneme", "coin": 200, "xp": 55},
    "tyt": {"name": "TYT Deneme", "coin": 200, "xp": 55},
    "analysis": {"name": "Deneme Analizi", "coin": 50, "xp": 25},
    "mistakes": {"name": "Yanlışlara Bakma", "coin": 100, "xp": 30},
}

# ---------- GACHA ----------
GACHA_COST = 150

LOOT_TABLE = [
    ("Common", 60, ["5 dk mola", "10 coin", "Motivasyon videosu"]),
    ("Rare", 30, ["1 video", "25 coin", "Mini ödül molası"]),
    ("Epic", 9, ["1 bölüm anime", "45 dk oyun", "XP x2 boost", "100 coin"]),
    ("Legendary", 1, ["2 saat guilt-free oyun", "500 coin", "XP x3 potion"])
]

# ---------- LOGIN ----------
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]

        if email not in users:
            users[email] = {
                "coin": 0,
                "xp": 0,
                "level": 1,
                "streak": 0,
                "last_task": None,
                "loot_log": []
            }

        session["user"] = email
        return redirect("/dashboard")

    return render_template("login.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user = users[session["user"]]
    return render_template("dashboard.html", user=user, tasks=TASKS)

# ---------- TASK ----------
@app.route("/task/<task>")
def task(task):
    if "user" not in session:
        return redirect("/login")

    if task not in TASKS:
        return redirect("/dashboard")

    u = users[session["user"]]
    t = TASKS[task]

    today = str(datetime.date.today())

    # streak check
    if u["last_task"] == today:
        pass
    else:
        yesterday = str(datetime.date.today() - datetime.timedelta(days=1))
        if u["last_task"] == yesterday:
            u["streak"] += 1
        else:
            u["streak"] = 1

    u["last_task"] = today

    # reward
    u["coin"] += t["coin"]
    u["xp"] += t["xp"]

    # level up
    if u["xp"] >= u["level"] * 100:
        u["xp"] = 0
        u["level"] += 1

    return redirect("/dashboard")

# ---------- GACHA ----------
@app.route("/gacha")
def gacha():
    if "user" not in session:
        return redirect("/login")

    u = users[session["user"]]

    if u["coin"] < GACHA_COST:
        return redirect("/dashboard")

    u["coin"] -= GACHA_COST

    roll = random.randint(1,100)
    total = 0

    for rarity, chance, rewards in LOOT_TABLE:
        total += chance
        if roll <= total:
            reward = random.choice(rewards)
            u["loot_log"].append(f"{rarity} → {reward}")
            break

    return render_template("gacha.html", rarity=rarity, reward=reward)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
