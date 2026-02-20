import os
from flask import Flask, render_template, request, redirect, session
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "secret123"

# Basit user database (RAM)
users = {}

# Görevler
tasks = {
    "branch": {"name": "Branş Deneme", "coin": 35, "xp": 10},
    "sb": {"name": "Soru Bankası Bitirme", "coin": 150, "xp": 45},
    "ayt": {"name": "AYT Deneme", "coin": 200, "xp": 55},
    "tyt": {"name": "TYT Deneme", "coin": 200, "xp": 55},
    "analysis": {"name": "Deneme Analizi", "coin": 50, "xp": 25},
    "mistake": {"name": "Yanlışlara Bakma", "coin": 100, "xp": 30}
}

@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        session["user"] = email
        return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    email = session["user"]

    if email not in users:
        users[email] = {"coin":0,"xp":0}

    return render_template("dashboard.html", user=users[email], tasks=tasks, email=email)

@app.route("/task/<key>")
def do_task(key):
    if "user" not in session:
        return redirect("/login")

    email = session["user"]

    if key in tasks:
        users[email]["coin"] += tasks[key]["coin"]
        users[email]["xp"] += tasks[key]["xp"]

    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
