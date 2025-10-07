# admin.py
"""
Логика админ-панели: функции управления товарами и аукционами,
которые используются в webapp и ботe.
"""

from database import (
    add_product, get_products, get_product, delete_product,
    mark_product_sold, create_auction, get_auctions, get_auction,
    place_bid, get_bids_for_auction, get_highest_bid
)
from config import ADMIN_IDS

# Проверка, является ли telegram_id админом
def is_admin(telegram_id):
    try:
        return int(telegram_id) in ADMIN_IDS
    except Exception:
        return False

# Обёртки для webapp
def admin_add_product(form):
    """
    form: dict с полями name, description, price, type, float_value(optional), link(optional)
    """
    name = form.get("name")
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
    return add_product(name, description, price, type_, float_value, link)

def admin_delete_product(product_id):
    return delete_product(product_id)

def admin_mark_sold(product_id):
    return mark_product_sold(product_id)

def admin_create_auction(form):
    """
    form: title, description, start_price, step, duration_minutes
    """
    import time
    title = form.get("title")
    description = form.get("description", "")
    start_price = float(form.get("start_price", 0))
    step = float(form.get("step", 1))
    duration_minutes = int(form.get("duration_minutes", 60))
    end_timestamp = int(time.time()) + duration_minutes * 60
    return create_auction(title, description, start_price, step, end_timestamp)

def admin_get_products():
    return get_products(only_available=False)

def admin_get_auctions():
    return get_auctions(only_active=False)

def admin_place_bid(auction_id, bidder_identifier, amount):
    return place_bid(auction_id, bidder_identifier, float(amount))

def admin_get_bids(auction_id):
    return get_bids_for_auction(auction_id)

def admin_get_highest(auction_id):
    return get_highest_bid(auction_id)
