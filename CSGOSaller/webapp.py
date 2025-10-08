# webapp.py
"""
Flask WebApp: магазин и аукцион.
Язык и тема подтягиваются по ?tg_id=<телеграм_id> (если передан).
Если tg_id нет — используются DEFAULT (узбек, dark).
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from config import t, DEFAULT_LANG, DEFAULT_THEME, FLASK_SECRET, APP_URL
import database
from admin import is_admin, admin_add_product, admin_create_auction
import time, os

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = FLASK_SECRET

# Главная страница — магазин
@app.route("/")
def index():
    tg_id = request.args.get("tg_id", type=int)
    if tg_id:
        prefs = database.get_user_pref(tg_id)
        lang = prefs.get("lang", DEFAULT_LANG)
        theme = prefs.get("theme", DEFAULT_THEME)
    else:
        lang = DEFAULT_LANG
        theme = DEFAULT_THEME

    products = database.get_products(only_available=True)
    return render_template("index.html", lang=lang, theme=theme, t=t, products=products, app_url=APP_URL)

# Аукционы страница
@app.route("/auctions")
def auctions():
    tg_id = request.args.get("tg_id", type=int)
    if tg_id:
        prefs = database.get_user_pref(tg_id)
        lang = prefs.get("lang", DEFAULT_LANG)
        theme = prefs.get("theme", DEFAULT_THEME)
    else:
        lang = DEFAULT_LANG
        theme = DEFAULT_THEME

    auctions = database.get_auctions(only_active=True)
    return render_template("auctions.html", lang=lang, theme=theme, t=t, auctions=auctions)

# Простая health
@app.route("/health")
def health():
    return "OK", 200

# Admin routes (как раньше)
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if request.method == "POST":
        tid = request.form.get("telegram_id")
        if tid and is_admin(tid):
            # записываем в сессию простую cookie / query - но для простоты работаем через flash
            flash("✅ Авторизация успешна")
            return redirect(url_for("admin_dashboard", tg_id=tid))
        else:
            flash("⛔ Доступ запрещён")
            return redirect(url_for("admin_panel"))
    # язык и тема по умолчанию
    lang = DEFAULT_LANG
    theme = DEFAULT_THEME
    return render_template("admin_login.html", lang=lang, theme=theme, t=t)

@app.route("/admin/dashboard")
def admin_dashboard():
    tg_id = request.args.get("tg_id", type=int)
    # проверка через query param
    if not tg_id or not is_admin(tg_id):
        flash("Требуется авторизация админа")
        return redirect(url_for("admin_panel"))
    products = database.get_products(only_available=False)
    auctions = database.get_auctions(only_active=False)
    return render_template("admin_dashboard.html", lang=DEFAULT_LANG, theme=DEFAULT_THEME, t=t, products=products, auctions=auctions)

@app.route("/admin/add_product", methods=["POST"])
def admin_add_product_route():
    tg_id = request.args.get("tg_id", type=int)
    if not tg_id or not is_admin(tg_id):
        flash("Доступ запрещён")
        return redirect(url_for("admin_panel"))
    admin_add_product(request.form)
    flash("✅ Товар добавлен")
    return redirect(url_for("admin_dashboard", tg_id=tg_id))

@app.route("/admin/create_auction", methods=["POST"])
def admin_create_auction_route():
    tg_id = request.args.get("tg_id", type=int)
    if not tg_id or not is_admin(tg_id):
        flash("Доступ запрещён")
        return redirect(url_for("admin_panel"))
    admin_create_auction(request.form)
    flash("🏁 Аукцион создан")
    return redirect(url_for("admin_dashboard", tg_id=tg_id))

# Статические файлы (CSS)
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), "static"), filename)

# запуск (если запускать напрямую)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
