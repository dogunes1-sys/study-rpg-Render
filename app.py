import json
import os
import random
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_EMAIL = "admin@mail.com"
ADMIN_PASSWORD = "1234"

DATA_FILE = "data.json"

# ---------- DATA ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"xp": 0, "coin": 500}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

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
    return render_template(
        "dashboard.html",
        xp=data["xp"],
        coin=data["coin"],
        result=session.pop("gacha_result", None)
    )


# ---------- ACTIONS ----------
@app.route("/add_xp/<amount>")
def add_xp(amount):
    data = load_data()
    data["xp"] += int(amount)
    save_data(data)
    return redirect("/dashboard")


@app.route("/add_coin/<amount>")
def add_coin(amount):
    data = load_data()
    data["coin"] += int(amount)
    save_data(data)
    return redirect("/dashboard")


# ---------- GACHA ROUTE ----------
@app.route("/gacha")
def gacha():

    data = load_data()

    if data["coin"] < 100:
        session["gacha_result"] = ("NOCOIN", "Coin yetmez (100 gerekli)")
        return redirect("/dashboard")

    data["coin"] -= 100

    rarity, reward = roll_gacha()

    if "coin" in reward:
        amount = int(reward.split()[0])
        data["coin"] += amount

    save_data(data)

    session["gacha_result"] = (rarity, reward)
    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
