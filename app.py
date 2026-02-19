import json
import os
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_EMAIL = "admin@mail.com"
ADMIN_PASSWORD = "1234"

DATA_FILE = "data.json"


# -------- DATA SYSTEM --------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"xp": 0, "coin": 0}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


# -------- ROUTES --------
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
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
        user=session["user"]
    )


# -------- ACTION BUTTONS --------
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


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
