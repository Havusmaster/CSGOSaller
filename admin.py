# admin.py
"""
Админские обёртки — проверка прав и удобные функции для webapp и бота.
"""

from config import ADMIN_IDS
import database

def is_admin(telegram_id):
    try:
        return int(telegram_id) in ADMIN_IDS
    except Exception:
        return False

# Веб-обёртки для добавления/управления товарами / аукционами
def admin_add_product(form):
    name = form.get("name") or "Без имени"
    description = form.get("description", "")
    price = float(form.get("price", 0))
    type_ = form.get("type", "agent")
    float_value = None
    if type_ == "weapon":
        try:
            float_value = float(form.get("float_value", 0.0))
        except:
            float_value = None
    link = form.get("link")
    return database.add_product(name, description, price, type_, float_value, link)

def admin_delete_product(product_id):
    return database.delete_product(product_id)

def admin_mark_sold(product_id):
    return database.mark_product_sold(product_id)

def admin_create_auction(form):
    import time
    title = form.get("title") or "Лот"
    description = form.get("description", "")
    start_price = float(form.get("start_price", 0))
    step = float(form.get("step", 1))
    duration_minutes = int(form.get("duration_minutes", 60))
    end_timestamp = int(time.time()) + duration_minutes * 60
    return database.create_auction(title, description, start_price, step, end_timestamp)

def admin_get_products():
    return database.get_products(only_available=False)

def admin_get_auctions():
    return database.get_auctions(only_active=False)

def admin_place_bid(auction_id, bidder_identifier, amount):
    return database.place_bid(auction_id, bidder_identifier, float(amount))

def admin_get_bids(auction_id):
    return database.get_bids_for_auction(auction_id)

def admin_get_highest(auction_id):
    return database.get_highest_bid(auction_id)
