import os
import random
from flask import Flask, render_template, request, redirect, session
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "secret123"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= LOGIN =================

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

        try:
            supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            session["user"] = email
            return redirect("/dashboard")
        except:
            return "Login failed"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user = supabase.table("users").select("*").eq("email", session["user"]).execute().data[0]
    activities = supabase.table("activities").select("*").execute().data

    return render_template("dashboard.html",
                           user=user,
                           activities=activities)


# ================= ACTIVITY COMPLETE =================

@app.route("/complete/<id>")
def complete(id):
    if "user" not in session:
        return redirect("/login")

    activity = supabase.table("activities").select("*").eq("id", id).execute().data[0]
    user = supabase.table("users").select("*").eq("email", session["user"]).execute().data[0]

    new_xp = user["xp"] + activity["xp"]
    new_coins = user["coins"] + activity["coins"]

    supabase.table("users").update({
        "xp": new_xp,
        "coins": new_coins
    }).eq("email", session["user"]).execute()

    return redirect("/dashboard")


# ================= ADD ACTIVITY =================

@app.route("/addactivity", methods=["POST"])
def addactivity():
    name = request.form["name"]
    xp = int(request.form["xp"])
    coins = int(request.form["coins"])

    supabase.table("activities").insert({
        "name": name,
        "xp": xp,
        "coins": coins
    }).execute()

    return redirect("/dashboard")


# ================= GACHA SYSTEM =================

GACHA_COST = 100

gacha_table = [
    ("Common", 60, [
        ("5 dk mola", 0),
        ("10 coin", 10),
        ("Motivasyon mesajı", 0)
    ]),
    ("Rare", 30, [
        ("1 video", 0),
        ("50 coin", 50),
        ("25 XP", 0)
    ]),
    ("Epic", 9, [
        ("1 bölüm anime/dizi", 0),
        ("45 dk oyun", 0),
        ("XP Boost", 0),
        ("100 coin", 100)
    ]),
    ("Legendary", 1, [
        ("2 saat guilt-free oyun", 0),
        ("500 coin", 500),
        ("XP Potion", 0)
    ])
]


def roll():
    r = random.randint(1,100)
    total = 0

    for rarity, chance, rewards in gacha_table:
        total += chance
        if r <= total:
            return rarity, random.choice(rewards)

    return "Common", ("Nothing",0)


@app.route("/gacha")
def gacha():
    if "user" not in session:
        return redirect("/login")

    user = supabase.table("users").select("*").eq("email", session["user"]).execute().data[0]

    if user["coins"] < GACHA_COST:
        return "Not enough coins"

    rarity, reward = roll()
    reward_name, coin_reward = reward

    supabase.table("users").update({
        "coins": user["coins"] - GACHA_COST + coin_reward
    }).eq("email", session["user"]).execute()

    return render_template("gacha.html",
                           rarity=rarity,
                           reward=reward_name)


# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
