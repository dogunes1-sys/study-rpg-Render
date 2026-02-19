import os, json, random, datetime
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "secretkey"

DATA_FILE = "user.json"
LOG_FILE = "gacha_log.json"

# ---------- DATA ----------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "coin":0,
            "xp":0,
            "level":1,
            "daily_coin":0,
            "last_day":str(datetime.date.today()),
            "streak":0,
            "last_task_day":""
        }
    return json.load(open(DATA_FILE))

def save_data(data):
    json.dump(data, open(DATA_FILE,"w"))

def load_log():
    if not os.path.exists(LOG_FILE):
        return []
    return json.load(open(LOG_FILE))

def save_log(log):
    json.dump(log, open(LOG_FILE,"w"))

# ---------- LEVEL ----------

def check_level(data):
    need = data["level"] * 100
    if data["xp"] >= need:
        data["xp"] -= need
        data["level"] += 1

def rank_name(level):
    ranks=[(1,"Bronze"),(5,"Silver"),(10,"Gold"),(20,"Platinum"),(35,"Diamond"),(50,"Mythic")]
    r="Bronze"
    for lvl,name in ranks:
        if level>=lvl:
            r=name
    return r

# ---------- DAILY RESET ----------

def reset_daily(data):
    today=str(datetime.date.today())
    if data["last_day"]!=today:
        data["daily_coin"]=0
        data["last_day"]=today

# ---------- STREAK ----------

def streak_bonus(data):

    bonuses={
        3:("coin",50),
        7:("coin",200),
        14:("epic",None),
        30:("legendary",None)
    }

    if data["streak"] in bonuses:

        typ,val=bonuses[data["streak"]]

        if typ=="coin":
            data["coin"]+=val
            return f"🔥 STREAK BONUS → {val} coin"

        if typ=="epic":
            rarity,reward=roll(force="Epic")
            return f"🔥 STREAK EPIC → {reward}"

        if typ=="legendary":
            rarity,reward=roll(force="Legendary")
            return f"🔥 STREAK LEGENDARY → {reward}"

    return None


def update_streak(data):

    today=datetime.date.today()
    last=data["last_task_day"]

    if last=="":
        data["streak"]=1
        data["last_task_day"]=str(today)
        return None

    last_date=datetime.date.fromisoformat(last)
    diff=(today-last_date).days

    if diff==1:
        data["streak"]+=1
    elif diff>1:
        data["streak"]=1

    data["last_task_day"]=str(today)

    return streak_bonus(data)

# ---------- GACHA ----------

rewards={
"Common":["5 dk mola","10 coin","15 coin"],
"Rare":["1 video","50 coin","30 dk oyun"],
"Epic":["1 bölüm anime","100 coin","XP x2 buff"],
"Legendary":["2 saat guilt-free oyun","500 coin","XP x3 potion"]
}

def roll(force=None):

    if force:
        rarity=force
    else:
        r=random.random()
        if r<0.60: rarity="Common"
        elif r<0.90: rarity="Rare"
        elif r<0.99: rarity="Epic"
        else: rarity="Legendary"

    return rarity,random.choice(rewards[rarity])

# ---------- ROUTES ----------

@app.route("/")
def home():
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():

    data=load_data()
    reset_daily(data)
    check_level(data)
    save_data(data)

    leaderboard=[
        {"name":"Shadow","coin":4200},
        {"name":"Zenith","coin":3900},
        {"name":"Nova","coin":3100},
        {"name":"You","coin":data["coin"]}
    ]
    leaderboard=sorted(leaderboard,key=lambda x:x["coin"],reverse=True)

    return render_template(
        "dashboard.html",
        data=data,
        rank=rank_name(data["level"]),
        board=leaderboard,
        gacha=session.pop("gacha_result",None),
        streak_msg=session.pop("streak_msg",None)
    )

# ---------- TASK ----------

@app.route("/task",methods=["POST"])
def task():

    coin=int(request.form["coin"])
    xp=int(request.form["xp"])

    data=load_data()
    reset_daily(data)

    if data["daily_coin"]>=1000:
        return redirect("/dashboard")

    data["coin"]+=coin
    data["xp"]+=xp
    data["daily_coin"]+=coin

    msg=update_streak(data)

    check_level(data)
    save_data(data)

    if msg:
        session["streak_msg"]=msg

    return redirect("/dashboard")

# ---------- GACHA ----------

@app.route("/gacha")
def gacha():

    data=load_data()

    if data["coin"]<150:
        session["gacha_result"]=("NO COIN","150 coin gerekli")
        return redirect("/dashboard")

    data["coin"]-=150

    rarity,reward=roll()

    if "coin" in reward:
        for w in reward.split():
            if w.isdigit():
                data["coin"]+=int(w)

    save_data(data)

    log=load_log()
    log.append({"date":str(datetime.datetime.now()),"rarity":rarity,"reward":reward})
    save_log(log)

    session["gacha_result"]=(rarity,reward)
    return redirect("/dashboard")

# ---------- RUN ----------

if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000)
