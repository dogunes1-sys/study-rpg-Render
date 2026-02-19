import json
import os
import random
from flask import Flask, render_template, redirect, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_EMAIL = "admin@mail.com"
ADMIN_PASSWORD = "1234"

DATA_FILE = "data.json"
LOG_FILE = "gacha_log.json"

# ---------- DATA ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"xp": 0, "coin": 500}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ---------- LOG ----------
def load_log():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f)

# ---------- GACHA ----------
def roll_gacha():

    roll = random.randint(1,100)

    if roll <= 60:
        return "COMMON", "☕ 5 dk mola"

    elif roll <= 90:
        return "RARE", "📺 1 video"

    elif roll <= 99:
        reward = random.choice([
            "🎮 45 dk oyun",
            "📺 1 bölüm anime/dizi",
            "⚡ XP Boost (1 gün x2)",
            "💰 100 coin"
        ])
        return "EPIC", reward

    else:
        reward = random.choice([
            "🔥 2 saat guilt-free oyun",
            "💎 500 coin",
            "🚀 XP Potion (3 görev x3)"
        ])
        return "LEGENDARY", reward


# ---------- ROUTES ----------
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/login", methods=["GET","POST"])
def login():
    from flask import request

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["user"] = email
            return redirect("/dashboard")
        else:
            return "Wrong credentials"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    data = load_data()
    log = load_log()[-10:][::-1]

    return render_template(
        "dashboard.html",
        xp=data["xp"],
        coin=data["coin"],
        log=log,
        result=session.pop("gacha_result", None)
    )


# ---------- TASK SYSTEM ----------
@app.route("/task/<name>")
def task(name):

    rewards = {
        "branch": (35,10),
        "konu": (150,45),
        "ayt": (200,55),
        "tyt": (200,55),
        "analysis": (50,25),
        "mistake": (100,30)
    }

    if name not in rewards:
        return redirect("/dashboard")

    coin, xp = rewards[name]

    data = load_data()
    data["coin"] += coin
    data["xp"] += xp
    save_data(data)

    return redirect("/dashboard")


# ---------- GACHA ----------
@app.route("/gacha")
def gacha():

    data = load_data()

    if data["coin"] < 100:
        session["gacha_result"] = ("NO COIN", "100 coin gerekli")
        return redirect("/dashboard")

    data["coin"] -= 100

    rarity, reward = roll_gacha()

    # coin ödülü varsa ekle
    if "coin" in reward:
        for word in reward.split():
            if word.isdigit():
                data["coin"] += int(word)

    save_data(data)

    # LOG SAVE
    log = load_log()
    log.append({"rarity":rarity,"reward":reward})
    save_log(log)

    session["gacha_result"] = (rarity, reward)
    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
