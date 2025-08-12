import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template as original_render_template, redirect, session, g

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret")

BASE_DATA_DIR = "businesses"

# --- עזרות קריאה/כתיבה JSON לכל עסק ---

def get_business_dir(business):
    return os.path.join(BASE_DATA_DIR, business, "data")

def load_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- התחברות ---

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            error = "יש למלא שם משתמש וסיסמה"
            return render_template("login.html", error=error)
        # טענת סיסמאות ועסקים מ-config.json
        config = load_json("config.json")
        for biz, info in config.get("businesses", {}).items():
            if username == info.get("username") and password == info.get("password"):
                session["username"] = username
                session["business"] = biz
                session["is_admin"] = False
                return redirect("/business_main")
        # בדיקה אם ה-host (מנהל מערכת)
        host_info = config.get("host", {})
        if username == host_info.get("username") and password == host_info.get("password"):
            session["username"] = username
            session["is_admin"] = True
            return redirect("/host_main")
        error = "שם משתמש או סיסמה שגויים"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# --- דפי מערכת ---

@app.before_request
def before_request():
    g.username = session.get("username")
    g.business = session.get("business")
    g.is_admin = session.get("is_admin", False)

def render_template(template_name_or_list, **context):
    context["session"] = {
        "username": g.username,
        "business": g.business,
        "is_admin": g.is_admin
    }
    return original_render_template(template_name_or_list, **context)

@app.route("/host_main")
def host_main():
    if not g.is_admin:
        return redirect("/login")
    config = load_json("config.json")
    return render_template("host_main.html", businesses=config.get("businesses", {}))

@app.route("/business_main")
def business_main():
    if g.is_admin or not g.business:
        return redirect("/login")
    return render_template("main_admin.html", business=g.business)

# --- המשך קוד ניהול עסקים, הזמנות, שגרות, וכו' בהתאם לעסק ---
# כאן ניתן להוסיף ראוטים לניהול העסק הספציפי, קריאה/כתיבה מהקבצים בספריית העסק

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)