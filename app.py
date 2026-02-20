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
tasks = {
"branch":{"name":"Branş Deneme","coin":35,"xp":10},
"sb":{"name":"Soru Bankası Konu Bitirme","coin":400,"xp":45},
"ayt":{"name":"AYT Deneme","coin":500,"xp":55},
"tyt":{"name":"TYT Deneme","coin":500,"xp":55},
"analysis":{"name":"Deneme Analizi","coin":70,"xp":25},
"mistake":{"name":"Yanlışlara Bakma","coin":100,"xp":30},

"ayt_fizik":{"name":"AYT Fizik Branş","coin":60,"xp":20},
"ayt_kimya":{"name":"AYT Kimya Branş","coin":60,"xp":20},
"ayt_biyoloji":{"name":"AYT Biyoloji Branş","coin":60,"xp":20},

"tyt_fizik":{"name":"TYT Fizik Branş","coin":30,"xp":10},
"tyt_kimya":{"name":"TYT Kimya Branş","coin":30,"xp":10},
"tyt_biyoloji":{"name":"TYT Biyoloji Branş","coin":30,"xp":10},
"tyt_sosyal":{"name":"TYT Sosyal Branş","coin":45,"xp":15}
}

# =========================
# RANK + ACHIEVEMENT
# =========================
RANKS=[(1,"Beginner"),(6,"Apprentice"),(11,"Scholar"),(21,"Master"),(36,"Grandmaster")]

ACHIEVEMENTS=[
("rookie",10,"Rookie"),
("grinder",50,"Grinder"),
("machine",100,"Machine")
]

FAKE_LEADERBOARD=[
("ShadowMaster",2400),
("BrainBeast",2100),
("UltraMind",1800),
("FocusGod",1500)
]

# =========================
# LOOT
# =========================
loot_table=[
("Common",60,["5 dk mola","10 coin","motivasyon müziği"]),
("Rare",30,["1 video","30 coin","küçük oyun"]),
("Epic",9,["1 bölüm anime","100 coin","XP x2 boost"]),
("Legendary",1,["2 saat oyun guiltfree","500 coin","XP x3 potion"])
]

# =========================
# USER FETCH
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
        "logs":[],
        "tasks_done":0,
        "achievements":[]
        }
        supabase.table("users").insert(new_user).execute()
        return new_user

    user=res.data[0]

    # ---- NULL FIX ----
    if user.get("logs") is None:
        user["logs"]=[]
    if user.get("daily") is None:
        user["daily"]=None
    if user.get("tasks_done") is None:
        user["tasks_done"]=0
    if user.get("achievements") is None:
        user["achievements"]=[]

    return user

# =========================
# SAFE UPDATE
# =========================
def update_user(email,data):

    allowed={
    "coin","xp","level","streak",
    "last_task","logs","daily",
    "tasks_done","achievements"
    }

    clean={k:v for k,v in data.items() if k in allowed}

    supabase.table("users").update(clean).eq("email",email).execute()

# =========================
def level_up(user):
    need=user["level"]*100
    while user["xp"]>=need:
        user["xp"]-=need
        user["level"]+=1
        need=user["level"]*100

# =========================
def get_rank(level):
    rank="Beginner"
    for lvl,name in RANKS:
        if level>=lvl:
            rank=name
    return rank

# =========================
def streak_update(user):
    today=str(datetime.date.today())

    if user["last_task"]==today:
        return 0

    if user["last_task"]==str(datetime.date.today()-datetime.timedelta(days=1)):
        user["streak"]+=1
    else:
        user["streak"]=1

    user["last_task"]=today

    if user["streak"]==3: return 10
    if user["streak"]==7: return 30
    if user["streak"]==14: return 100

    return 0

# =========================
def claim_daily(user,email):
    today=str(datetime.date.today())
    if user.get("daily")==today:
        return False

    reward=random.randint(50,150)
    user["coin"]+=reward
    user["daily"]=today

    logs=user["logs"]
    logs.append(f"🎁 Günlük ödül +{reward}")

    update_user(email,{"coin":user["coin"],"daily":today,"logs":logs})
    return True

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

    rank=get_rank(user["level"])

    leaderboard=sorted(
        FAKE_LEADERBOARD+[("You",user["coin"])],
        key=lambda x:x[1],
        reverse=True
    )

    return render_template("dashboard.html",
        user=user,
        tasks=tasks,
        email=email,
        rank=rank,
        leaderboard=leaderboard
    )

# =========================
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
        user["tasks_done"]+=1

        bonus=streak_update(user)
        user["coin"]+=bonus

        level_up(user)

        logs=user["logs"]
        logs.append(f"✔ {t['name']} +{t['coin']}c +{t['xp']}xp")

        if bonus>0:
            logs.append(f"🔥 Streak bonus +{bonus}")

        # achievements
        for key_req,count,title in ACHIEVEMENTS:
            if user["tasks_done"]>=count and title not in user["achievements"]:
                user["achievements"].append(title)
                logs.append(f"🏆 {title} unlocked")

        update_user(email,{
        "coin":user["coin"],
        "xp":user["xp"],
        "level":user["level"],
        "streak":user["streak"],
        "last_task":user["last_task"],
        "logs":logs,
        "tasks_done":user["tasks_done"],
        "achievements":user["achievements"]
        })

    return redirect("/dashboard")

# =========================
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

    logs=user["logs"]
    logs.append(f"🎰 {rarity} → {reward}")

    update_user(email,{"coin":user["coin"],"logs":logs})

    return render_template("gacha.html",rarity=rarity,reward=reward)

# =========================
@app.route("/daily")
def daily():
    if "user" not in session:
        return redirect("/login")

    email=session["user"]
    user=get_user(email)
    claim_daily(user,email)
    return redirect("/dashboard")

# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000)
