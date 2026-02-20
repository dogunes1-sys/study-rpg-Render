import os, random, datetime
from flask import Flask, render_template, request, redirect, session
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key="secret123"

SUPABASE_URL=os.getenv("SUPABASE_URL")
SUPABASE_KEY=os.getenv("SUPABASE_KEY")
supabase=create_client(SUPABASE_URL,SUPABASE_KEY)


# =========================
# TASKS
# =========================
tasks={
"ayt_fizik":{"name":"AYT Fizik Branş","coin":120,"xp":40},
"ayt_kimya":{"name":"AYT Kimya Branş","coin":120,"xp":40},
"ayt_biyoloji":{"name":"AYT Biyoloji Branş","coin":120,"xp":40},
"branch":{"name":"Genel Branş Deneme","coin":35,"xp":10},
"sb":{"name":"Soru Bankası Konu Bitirme","coin":400,"xp":45},
"analysis":{"name":"Deneme Analizi","coin":70,"xp":25},
"mistake":{"name":"Yanlışlara Bakma","coin":100,"xp":30}
}


# =========================
# LOOT TABLE
# =========================
loot_table=[
("Common",60,["5 dk mola","10 coin","motivasyon müziği"]),
("Rare",30,["1 video","30 coin","küçük oyun"]),
("Epic",9,["1 bölüm anime","100 coin","XP x2 boost"]),
("Legendary",1,["2 saat oyun guiltfree","500 coin","XP x3 potion"])
]


# =========================
# USER FETCH / CREATE
# =========================
def get_user(email):

    res=supabase.table("users").select("*").eq("email",email).execute()

    if not res.data:
        new_user={
            "email":email,
            "coin":0,
            "xp":0,
            "level":1,
            "streak":0,
            "last_task":None,
            "daily":None,
            "logs":[]
        }
        supabase.table("users").insert(new_user).execute()
        return new_user

    user=res.data[0]

    # eksik alan fix
    if user.get("logs") is None:
        user["logs"]=[]
    if "daily" not in user:
        user["daily"]=None

    return user


# =========================
# UPDATE USER
# =========================
def update_user(email,data):
    supabase.table("users").update(data).eq("email",email).execute()


# =========================
# LEVEL SYSTEM
# =========================
def level_up(user):
    need=user["level"]*100
    while user["xp"]>=need:
        user["xp"]-=need
        user["level"]+=1
        need=user["level"]*100


# =========================
# STREAK SYSTEM
# =========================
def streak_update(user):
    today=str(datetime.date.today())

    if user["last_task"]==today:
        return

    if user["last_task"]==str(datetime.date.today()-datetime.timedelta(days=1)):
        user["streak"]+=1
    else:
        user["streak"]=1

    user["last_task"]=today


# =========================
# DAILY REWARD
# =========================
def claim_daily(user,email):

    today=str(datetime.date.today())

    if user.get("daily")==today:
        return False

    reward=random.randint(50,150)
    user["coin"]+=reward
    user["daily"]=today

    logs=user["logs"] or []
    logs.append(f"🎁 Günlük ödül +{reward} coin")

    update_user(email,{
        "coin":user["coin"],
        "daily":today,
        "logs":logs
    })

    return True


# =========================
# GACHA RNG
# =========================
def roll_loot():
    r=random.randint(1,100)
    total=0
    for rarity,chance,rewards in loot_table:
        total+=chance
        if r<=total:
            return rarity,random.choice(rewards)


# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        session["user"]=request.form["email"]
        return redirect("/dashboard")
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    email=session["user"]
    user=get_user(email)

    return render_template("dashboard.html",user=user,tasks=tasks,email=email)


@app.route("/task/<key>")
def task(key):
    if "user" not in session:
        return redirect("/login")

    email=session["user"]
    user=get_user(email)

    if key in tasks:
        t=tasks[key]

        user["coin"]+=t["coin"]
        user["xp"]+=t["xp"]

        streak_update(user)
        level_up(user)

        logs=user["logs"] or []
        logs.append(f"✔ {t['name']} +{t['coin']} coin +{t['xp']} xp")

        update_user(email,{
            "coin":user["coin"],
            "xp":user["xp"],
            "level":user["level"],
            "streak":user["streak"],
            "last_task":user["last_task"],
            "logs":logs
        })

    return redirect("/dashboard")


@app.route("/gacha")
def gacha():
    if "user" not in session:
        return redirect("/login")

    email=session["user"]
    user=get_user(email)

    if user["coin"]<100:
        return redirect("/dashboard")

    user["coin"]-=100
    rarity,reward=roll_loot()

    if "coin" in reward:
        user["coin"]+=int(reward.split()[0])

    logs=user["logs"] or []
    logs.append(f"🎁 {rarity} → {reward}")

    update_user(email,{
        "coin":user["coin"],
        "logs":logs
    })

    return render_template("gacha.html",rarity=rarity,reward=reward)


@app.route("/daily")
def daily():
    if "user" not in session:
        return redirect("/login")

    email=session["user"]
    user=get_user(email)

    claim_daily(user,email)

    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000)
