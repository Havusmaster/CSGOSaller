# webapp.py
"""
Flask WebApp: магазин, аукционы, админ-панель.
Интерфейс на Bootstrap 5. Всё на русском.
"""

from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from config import FLASK_SECRET, APP_URL, FLASK_PORT
import database
from admin import is_admin, admin_add_product, admin_get_products, admin_delete_product, admin_mark_sold, admin_create_auction, admin_get_auctions, admin_get_bids
import time

app = Flask(__name__)
app.secret_key = FLASK_SECRET

# Базовый шаблон
BASE_HTML = """
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>CSsaler — Магазин и Аукцион</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body { background: #f8fafc; }
      .card { border-radius: 12px; }
      .shadow-soft { box-shadow: 0 6px 18px rgba(0,0,0,0.06); }
      .hover-grow:hover { transform: translateY(-4px); transition: .18s; }
    </style>
  </head>
  <body>
    <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm mb-4">
      <div class="container">
        <a class="navbar-brand" href="/">🛍️ CSsaler</a>
        <div>
          <a class="btn btn-outline-primary me-2" href="/">Магазин</a>
          <a class="btn btn-outline-success me-2" href="/auctions">Аукционы</a>
          <a class="btn btn-outline-dark" href="/admin">Админ-панель</a>
        </div>
      </div>
    </nav>
    <div class="container">
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="mb-3">
            {% for m in messages %}
              <div class="alert alert-info">{{ m }}</div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}
      {{ content|safe }}
    </div>
    <footer class="text-center mt-5 mb-5 text-muted">© CSsaler</footer>
  </body>
</html>
"""

# Главная — магазин
@app.route("/")
def index():
    products = database.get_products(only_available=True)
    cards = ""
    for p in products:
        float_info = f"<div class='text-muted small'>Float: {p['float_value']}</div>" if p['type']=='weapon' and p['float_value'] else ""
        link_button = f"<a class='btn btn-sm btn-outline-primary' href='{p['link'] or '#'}' target='_blank'>🔗 Ссылка на продукт</a>" if p.get('link') else ""
        admin_profile_link = ""
        if p:
            # открытие профиля первого админа
            admin_profile_link = f"tg://user?id={ (database.get_products and '') }"
        cards += f"""
        <div class="col-md-4 mb-4">
          <div class="card p-3 shadow-soft hover-grow">
            <h5>📦 {p['name']}</h5>
            <p class="small text-muted">{p['description']}</p>
            <div class="fw-bold">💰 {p['price']}</div>
            <div class="small text-muted">Тип: {'🔫 Оружие' if p['type']=='weapon' else '💼 Агент'}</div>
            {float_info}
            <div class="mt-3 d-flex gap-2">
              <a class="btn btn-primary" href="tg://resolve?domain=&start=buy_{p['id']}">🛒 Купить</a>
              {link_button}
              <a class="btn btn-outline-secondary" href="tg://user?id=0">💬 Написать админу</a>
            </div>
          </div>
        </div>
        """
    content = f"<div class='row'>{cards or '<div class=\"alert alert-warning\">Нет доступных товаров</div>'}</div>"
    return render_template_string(BASE_HTML, content=content)

# Аукционы — список и формы ставок
@app.route("/auctions")
def auctions():
    auctions = database.get_auctions(only_active=True)
    cards = ""
    for a in auctions:
        now = int(time.time())
        remaining = max(0, a['end_timestamp'] - now)
        minutes = remaining // 60
        highest = database.get_highest_bid(a['id'])
        highest_str = f"{highest['amount']} ({highest['bidder_identifier']})" if highest else "Пока нет ставок"
        cards += f"""
        <div class="col-md-6 mb-4">
          <div class="card p-3 shadow-soft hover-grow">
            <h5>🏷️ {a['title']}</h5>
            <p class="small text-muted">{a['description']}</p>
            <div class="small">Старт: {a['start_price']} | Шаг: {a['step']}</div>
            <div class="fw-bold mt-2">Текущий максимум: {highest_str}</div>
            <div class="text-muted small">Осталось: {minutes} мин</div>
            <form method="post" action="/auction/{a['id']}/bid" class="mt-3 d-flex">
              <input name="bidder" class="form-control me-2" placeholder="@username или ID" required>
              <input name="amount" class="form-control me-2" placeholder="Сумма" type="number" step="0.01" required>
              <button class="btn btn-success">Сделать ставку</button>
            </form>
          </div>
        </div>
        """
    content = f"<div class='row'>{cards or '<div class=\"alert alert-info\">Нет активных аукционов</div>'}</div>"
    return render_template_string(BASE_HTML, content=content)

@app.route("/auction/<int:auction_id>/bid", methods=["POST"])
def auction_bid(auction_id):
    bidder = request.form.get("bidder")
    amount = request.form.get("amount")
    if not bidder or not amount:
        flash("Пожалуйста, заполните все поля ✍️")
        return redirect(url_for("auctions"))
    try:
        amount = float(amount)
    except:
        flash("Сумма указана неверно ❌")
        return redirect(url_for("auctions"))
    database.place_bid(auction_id, bidder, amount)
    flash("✅ Ваша ставка принята!")
    return redirect(url_for("auctions"))

# Админ — простой вход по Telegram ID
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if request.method == "POST":
        tid = request.form.get("telegram_id")
        if tid and is_admin(tid):
            session['admin_id'] = int(tid)
            flash("✅ Авторизация прошла успешно")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("⛔ Доступ запрещён: вы не в списке админов")
            return redirect(url_for("admin_panel"))
    content = """
    <div class="card p-4">
      <h4>🔒 Вход в админ-панель</h4>
      <form method="post">
        <div class="mb-3">
          <label class="form-label">Telegram ID (цифры)</label>
          <input name="telegram_id" class="form-control" placeholder="Введите ваш Telegram ID">
        </div>
        <button class="btn btn-primary">Войти</button>
      </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get('admin_id') or not is_admin(session.get('admin_id')):
        flash("Требуется авторизация админа")
        return redirect(url_for("admin_panel"))
    prods = admin_get_products()
    auctions_all = admin_get_auctions()
    # карточки и формы
    product_rows = ""
    for p in prods:
        product_rows += f"""
        <div class='border p-2 mb-2 rounded'>
          <div class='d-flex justify-content-between'>
            <div><strong>📦 {p['name']}</strong> — {p['price']}<br><small class='text-muted'>{p['description']}</small></div>
            <div>
              <a href='/admin/delete_product/{p['id']}' class='btn btn-sm btn-danger mb-1'>Удалить</a>
              <a href='/admin/mark_sold/{p['id']}' class='btn btn-sm btn-outline-success mb-1'>Отметить как продано</a><br>
              <a class='btn btn-sm btn-outline-secondary' href='tg://user?id=0'>💬 Написать админу</a>
            </div>
          </div>
        </div>
        """
    auctions_rows = ""
    for a in auctions_all:
        auctions_rows += f"""
        <div class='border p-2 mb-2 rounded'>
          <strong>🏷 {a['title']}</strong> — Старт {a['start_price']} — Конец: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(a['end_timestamp']))}<br>
          <a href='/admin/auction/{a['id']}/bids' class='btn btn-sm btn-outline-primary mt-2'>Посмотреть ставки</a>
        </div>
        """
    content = f"""
    <div class="row">
      <div class="col-md-6">
        <div class="card p-3 mb-3 shadow-soft">
          <h5>➕ Добавить товар</h5>
          <form method="post" action="/admin/add_product">
            <input name="name" class="form-control mb-2" placeholder="Название" required>
            <textarea name="description" class="form-control mb-2" placeholder="Описание"></textarea>
            <input name="price" class="form-control mb-2" placeholder="Цена" required type="number" step="0.01">
            <select name="type" class="form-control mb-2">
              <option value="agent">💼 Агент</option>
              <option value="weapon">🔫 Оружие</option>
            </select>
            <input name="float_value" class="form-control mb-2" placeholder="Float (если оружие)">
            <input name="link" class="form-control mb-2" placeholder="Ссылка на продукт (необязательно)">
            <button class="btn btn-success">Добавить</button>
          </form>
        </div>

        <div class="card p-3 shadow-soft">
          <h5>🏆 Создать аукцион</h5>
          <form method="post" action="/admin/create_auction">
            <input name="title" class="form-control mb-2" placeholder="Название лота" required>
            <textarea name="description" class="form-control mb-2" placeholder="Описание"></textarea>
            <input name="start_price" class="form-control mb-2" placeholder="Стартовая цена" required type="number" step="0.01">
            <input name="step" class="form-control mb-2" placeholder="Шаг ставки" required type="number" step="0.01">
            <input name="duration_minutes" class="form-control mb-2" placeholder="Длительность (минуты)" required type="number" value="60">
            <button class="btn btn-primary">Создать аукцион</button>
          </form>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card p-3 mb-3 shadow-soft">
          <h5>📦 Товары</h5>
          {product_rows or '<div class="small text-muted">Нет товаров</div>'}
        </div>

        <div class="card p-3 shadow-soft">
          <h5>⚔️ Аукционы (все)</h5>
          {auctions_rows or '<div class="small text-muted">Нет аукционов</div>'}
        </div>
      </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/admin/add_product", methods=["POST"])
def admin_add_product_route():
    if not session.get('admin_id') or not is_admin(session.get('admin_id')):
        flash("Доступ запрещён")
        return redirect(url_for("admin_panel"))
    admin_add_product(request.form)
    flash("✅ Товар добавлен")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_product/<int:product_id>")
def admin_delete_product_route(product_id):
    if not session.get('admin_id') or not is_admin(session.get('admin_id')):
        flash("Доступ запрещён")
        return redirect(url_for("admin_panel"))
    admin_delete_product(product_id)
    flash("🗑️ Товар удалён")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/mark_sold/<int:product_id>")
def admin_mark_sold_route(product_id):
    if not session.get('admin_id') or not is_admin(session.get('admin_id')):
        flash("Доступ запрещён")
        return redirect(url_for("admin_panel"))
    admin_mark_sold(product_id)
    flash("✅ Товар отмечен как продано")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/create_auction", methods=["POST"])
def admin_create_auction_route():
    if not session.get('admin_id') or not is_admin(session.get('admin_id')):
        flash("Доступ запрещён")
        return redirect(url_for("admin_panel"))
    admin_create_auction(request.form)
    flash("🏁 Аукцион создан")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/auction/<int:auction_id>/bids")
def admin_view_bids(auction_id):
    if not session.get('admin_id') or not is_admin(session.get('admin_id')):
        flash("Доступ запрещён")
        return redirect(url_for("admin_panel"))
    bids = admin_get_bids(auction_id)
    rows = ""
    for b in bids:
        rows += f"<tr><td>{b['id']}</td><td>{b['bidder_identifier']}</td><td>{b['amount']}</td><td>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(b['created_at']))}</td></tr>"
    content = f"""
    <div class="card p-3">
      <h5>Ставки по лоту #{auction_id}</h5>
      <table class="table">
        <thead><tr><th>#</th><th>Участник</th><th>Сумма</th><th>Время</th></tr></thead>
        <tbody>
        {rows or '<tr><td colspan=4>Нет ставок</td></tr>'}
        </tbody>
      </table>
      <a class="btn btn-secondary" href="/admin/dashboard">Назад</a>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/health")
def health():
    return "OK", 200

# Запуск только если вебврап запускается вручную (в бот.py мы запускаем Flask вручную)
if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT)
