from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from models import (
    Client, ClientType, MenuItem, OrderItem,
    Waiter, Hall, Table, TableStatus, Reservation
)
from queue_service import PriorityQueue
from order_service import OrderService
from datetime import datetime
import functools

app = Flask(__name__)
app.secret_key = "kryivka-secret-2025"

# ── Початкові дані ───────────────────────────────────────────────
queue_service = PriorityQueue()
order_service = OrderService()
_client_id      = 1
_reservation_id = 1

MENU = [
    MenuItem(1,  "Борщ з пампушками",    85.0,  "Супи"),
    MenuItem(2,  "Крем-суп з грибів",    95.0,  "Супи"),
    MenuItem(3,  "Стейк рибай",         320.0,  "М'ясо"),
    MenuItem(4,  "Курка по-київськи",   185.0,  "М'ясо"),
    MenuItem(5,  "Форель на грилі",     245.0,  "Риба"),
    MenuItem(6,  "Паста карбонара",     160.0,  "Паста"),
    MenuItem(7,  "Піца Маргарита",      145.0,  "Піца"),
    MenuItem(8,  "Цезар з куркою",      135.0,  "Салати"),
    MenuItem(9,  "Грецький салат",      110.0,  "Салати"),
    MenuItem(10, "Тірамісу",             95.0,  "Десерти"),
    MenuItem(11, "Чізкейк",              90.0,  "Десерти"),
    MenuItem(12, "Еспресо",              55.0,  "Напої"),
    MenuItem(13, "Свіжовичавлений сік",  75.0,  "Напої"),
    MenuItem(14, "Лимонад домашній",     70.0,  "Напої"),
    MenuItem(15, "Наливка Вишня",         65.0,  "Наливки"),
    MenuItem(16, "Наливка Журавлина",      65.0,  "Наливки"),
    MenuItem(17, "Наливка Зубрівка",       65.0,  "Наливки"),
    MenuItem(18, "Наливка Кава апельсин",  70.0,  "Наливки"),
    MenuItem(19, "Наливка Калганівка",     65.0,  "Наливки"),
    MenuItem(20, "Наливка Кедрівка",       65.0,  "Наливки"),
    MenuItem(21, "Наливка Кізил",          65.0,  "Наливки"),
    MenuItem(22, "Наливка М'ята",          65.0,  "Наливки"),
    MenuItem(23, "Наливка Малина",         65.0,  "Наливки"),
    MenuItem(24, "Медовуха",               70.0,  "Наливки"),
    MenuItem(25, "Наливка Подих Карпат",   75.0,  "Наливки"),
    MenuItem(26, "Наливка Райська кава",   70.0,  "Наливки"),
    MenuItem(27, "Наливка Райський плід",  70.0,  "Наливки"),
    MenuItem(28, "Наливка Смородина",      65.0,  "Наливки"),
    MenuItem(29, "Наливка Хріновуха",      65.0,  "Наливки"),
]

WAITERS = [
    Waiter(1, "Яницький Максим",      "senior"),
    Waiter(2, "Сачок Павло",          "junior"),
    Waiter(3, "Будов Денис",          "junior"),
    Waiter(4, "Мельникович Григорій", "senior"),
    Waiter(0, "Адміністратор",        "admin"),   # адмін
]

HALLS = [
    Hall(1, "Основний зал", [
        Table(1, 1, 4), Table(2, 1, 4), Table(3, 1, 2),
        Table(4, 1, 6), Table(5, 1, 2), Table(6, 1, 4),
    ]),
    Hall(2, "VIP-зал", [
        Table(7, 2, 8), Table(8, 2, 4), Table(9, 2, 6),
    ]),
    Hall(3, "Літня тераса", [
        Table(10, 3, 4), Table(11, 3, 4),
        Table(12, 3, 2), Table(13, 3, 6),
    ]),
]

RESERVATIONS: list = []


# ── Допоміжні ────────────────────────────────────────────────────
def find_table(table_id: int):
    for hall in HALLS:
        for t in hall.tables:
            if t.table_id == table_id:
                return t, hall
    return None, None

def find_waiter(waiter_id: int):
    return next((w for w in WAITERS if w.waiter_id == waiter_id), None)

def current_waiter():
    wid = session.get("waiter_id")
    if wid is None:
        return None
    return find_waiter(wid)

def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if current_waiter() is None:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return wrapper

def table_full_info(t, hall):
    """Повертає dict зі всією інфою про столик."""
    reservation = next(
        (r for r in RESERVATIONS if r.table.table_id == t.table_id and not r.closed),
        None
    )
    order_data = None
    if reservation:
        for o in order_service.get_all_orders():
            if o.client.name == reservation.client_name and o.status.value != "completed":
                order_data = {
                    "order_id":    o.order_id,
                    "status":      o.status.value,
                    "items": [{
                        "name":     i.menu_item.name,
                        "qty":      i.quantity,
                        "price":    i.menu_item.price,
                        "subtotal": i.subtotal,
                    } for i in o.items],
                    "subtotal":    o.total,
                    "total":       order_service.calculate_total(o),
                    "discount":    round(o.total - order_service.calculate_total(o), 2),
                    "client_type": o.client.client_type.value,
                }
                break
    return {
        "table_id":       t.table_id,
        "seats":          t.seats,
        "status":         t.status.value,
        "hall_id":        hall.hall_id,
        "hall_name":      hall.name,
        "waiter_id":      reservation.waiter.waiter_id if reservation else None,
        "waiter_name":    reservation.waiter.name      if reservation else None,
        "waiter_level":   reservation.waiter.level     if reservation else None,
        "client_name":    reservation.client_name      if reservation else None,
        "guests":         reservation.guests            if reservation else None,
        "note":           reservation.note              if reservation else "",
        "reservation_id": reservation.reservation_id   if reservation else None,
        "seated":         reservation.seated            if reservation else False,
        "order":          order_data,
    }


# ── Сторінки ─────────────────────────────────────────────────────
@app.route("/login", methods=["GET"])
def login_page():
    if current_waiter():
        return redirect(url_for("index"))
    return render_template("login.html", waiters=[w for w in WAITERS if w.level != "admin"])

@app.route("/api/login", methods=["POST"])
def do_login():
    waiter_id = int(request.json.get("waiter_id", -1))
    waiter = find_waiter(waiter_id)
    if not waiter:
        return jsonify({"error": "Офіціанта не знайдено"}), 404
    session["waiter_id"] = waiter.waiter_id
    return jsonify({"waiter_id": waiter.waiter_id, "name": waiter.name, "level": waiter.level})

@app.route("/api/logout", methods=["POST"])
def do_logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/")
@login_required
def index():
    waiter = current_waiter()
    return render_template("index.html", menu=MENU, waiters=WAITERS, halls=HALLS, waiter=waiter)


# ── API: сесія ───────────────────────────────────────────────────
@app.route("/api/me", methods=["GET"])
def api_me():
    w = current_waiter()
    if not w:
        return jsonify({"error": "not logged in"}), 401
    return jsonify({"waiter_id": w.waiter_id, "name": w.name, "level": w.level})


# ── API: черга ───────────────────────────────────────────────────
@app.route("/api/client", methods=["POST"])
@login_required
def add_client():
    global _client_id
    data  = request.json
    ctype = ClientType[data.get("type", "REGULAR").upper()]
    client = Client(_client_id, data["name"], ctype)
    queue_service.enqueue(client)
    _client_id += 1
    return jsonify({"id": client.client_id, "name": client.name,
                    "type": client.client_type.value, "priority": client.base_priority,
                    "queue_size": len(queue_service)})

@app.route("/api/queue", methods=["GET"])
@login_required
def get_queue():
    items = queue_service.peek_all()
    return jsonify([{
        "id": c.client_id, "name": c.name, "type": c.client_type.value,
        "priority": c.base_priority,
        "wait_min": int((datetime.now() - c.arrived_at).seconds / 60),
    } for c in items])

# Офіціант САМ обирає клієнта з черги
@app.route("/api/serve/<int:client_id>", methods=["POST"])
@login_required
def serve_client(client_id):
    # Знайти і видалити конкретного клієнта з черги
    target = None
    new_heap = []
    for item in queue_service._heap:
        c = item[2]
        if c.client_id == client_id:
            target = c
        else:
            new_heap.append(item)
    if not target:
        return jsonify({"error": "Клієнта не знайдено в черзі"}), 404
    import heapq
    heapq.heapify(new_heap)
    queue_service._heap = new_heap
    order = order_service.create_order(target)
    return jsonify({"order_id": order.order_id, "client_name": target.name,
                    "client_type": target.client_type.value})


# ── API: зали / столики ──────────────────────────────────────────
@app.route("/api/halls", methods=["GET"])
@login_required
def get_halls():
    result = []
    for hall in HALLS:
        tables_data = [table_full_info(t, hall) for t in hall.tables]
        result.append({"hall_id": hall.hall_id, "name": hall.name, "tables": tables_data})
    return jsonify(result)

@app.route("/api/table/<int:table_id>", methods=["GET"])
@login_required
def get_table(table_id):
    t, hall = find_table(table_id)
    if not t:
        return jsonify({"error": "Столик не знайдено"}), 404
    return jsonify(table_full_info(t, hall))


# ── API: бронювання ──────────────────────────────────────────────
@app.route("/api/reservation", methods=["POST"])
@login_required
def make_reservation():
    global _reservation_id
    data   = request.json
    table, hall = find_table(data["table_id"])
    if not table:
        return jsonify({"error": "Столик не знайдено"}), 404
    if table.status != TableStatus.FREE:
        return jsonify({"error": "Столик вже зайнятий або заброньований"}), 400
    waiter = find_waiter(data.get("waiter_id") or session["waiter_id"])
    if not waiter:
        return jsonify({"error": "Офіціанта не знайдено"}), 404
    r = Reservation(
        reservation_id=_reservation_id,
        client_name=data["client_name"],
        table=table, waiter=waiter, hall=hall,
        guests=data.get("guests", 2),
        note=data.get("note", ""),
    )
    RESERVATIONS.append(r)
    table.status          = TableStatus.RESERVED
    waiter.active_tables += 1
    _reservation_id      += 1
    return jsonify({"reservation_id": r.reservation_id, "client": r.client_name,
                    "table_id": table.table_id, "hall": hall.name, "waiter": waiter.name})

@app.route("/api/reservation/<int:rid>/seat", methods=["POST"])
@login_required
def seat_reservation(rid):
    r = next((x for x in RESERVATIONS if x.reservation_id == rid), None)
    if not r:
        return jsonify({"error": "Бронювання не знайдено"}), 404
    r.table.status = TableStatus.OCCUPIED
    r.seated = True
    return jsonify({"status": "seated", "table_id": r.table.table_id})

@app.route("/api/reservation/<int:rid>/close", methods=["POST"])
@login_required
def close_reservation(rid):
    r = next((x for x in RESERVATIONS if x.reservation_id == rid), None)
    if not r:
        return jsonify({"error": "Бронювання не знайдено"}), 404
    r.table.status = TableStatus.FREE
    r.waiter.active_tables = max(0, r.waiter.active_tables - 1)
    r.closed = True
    return jsonify({"status": "closed"})

@app.route("/api/reservations", methods=["GET"])
@login_required
def list_reservations():
    wid = session.get("waiter_id")
    w   = find_waiter(wid)
    # Адмін бачить всі, офіціант — тільки свої
    all_r = [r for r in RESERVATIONS if not r.closed]
    if w and w.level != "admin":
        all_r = [r for r in all_r if r.waiter.waiter_id == wid]
    return jsonify([{
        "reservation_id": r.reservation_id,
        "client":         r.client_name,
        "table_id":       r.table.table_id,
        "hall":           r.hall.name,
        "waiter":         r.waiter.name,
        "guests":         r.guests,
        "note":           r.note,
        "seated":         r.seated,
        "table_status":   r.table.status.value,
    } for r in all_r])


# ── API: замовлення ──────────────────────────────────────────────
@app.route("/api/order/<int:oid>/item", methods=["POST"])
@login_required
def add_item(oid):
    data  = request.json
    order = order_service.get_order(oid)
    if not order:
        return jsonify({"error": "Замовлення не знайдено"}), 404
    item = next((m for m in MENU if m.item_id == data["item_id"]), None)
    if not item:
        return jsonify({"error": "Страву не знайдено"}), 404
    try:
        order_service.add_item(order, OrderItem(item, data.get("qty", 1)))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({
        "total": order_service.calculate_total(order),
        "items": [{"name": i.menu_item.name, "qty": i.quantity,
                   "subtotal": i.subtotal} for i in order.items],
    })

@app.route("/api/order/<int:oid>/status", methods=["PATCH"])
@login_required
def update_status(oid):
    try:
        status = order_service.advance_status(oid)
        return jsonify({"status": status})
    except KeyError:
        return jsonify({"error": "Замовлення не знайдено"}), 404

@app.route("/api/orders", methods=["GET"])
@login_required
def list_orders():
    return jsonify([{
        "order_id":    o.order_id,
        "client":      o.client.name,
        "client_type": o.client.client_type.value,
        "status":      o.status.value,
        "total":       order_service.calculate_total(o),
        "items_count": len(o.items),
    } for o in order_service.get_all_orders()])


# ── API: чек ─────────────────────────────────────────────────────
@app.route("/api/receipt/<int:table_id>", methods=["GET"])
@login_required
def get_receipt(table_id):
    reservation = next(
        (r for r in RESERVATIONS if r.table.table_id == table_id and not r.closed), None)
    if not reservation:
        return jsonify({"error": "Немає активного бронювання для цього столика"}), 404
    orders_for_client = [o for o in order_service.get_all_orders()
                         if o.client.name == reservation.client_name]
    if not orders_for_client:
        return jsonify({"error": "Замовлень не знайдено"}), 404
    order = orders_for_client[-1]
    return jsonify({
        "receipt_num":  order.order_id,
        "table_id":     table_id,
        "hall":         reservation.hall.name,
        "client":       reservation.client_name,
        "client_type":  order.client.client_type.value,
        "guests":       reservation.guests,
        "waiter":       reservation.waiter.name,
        "note":         reservation.note,
        "created_at":   order.created_at.strftime("%d.%m.%Y %H:%M"),
        "items": [{"name": i.menu_item.name, "qty": i.quantity,
                   "price": i.menu_item.price, "subtotal": i.subtotal}
                  for i in order.items],
        "subtotal":  order.total,
        "discount":  round(order.total - order_service.calculate_total(order), 2),
        "total":     order_service.calculate_total(order),
        "status":    order.status.value,
    })


if __name__ == "__main__":
    app.run(debug=True)
