import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from models import (
    Client, ClientType, MenuItem, OrderItem,
    Order, OrderStatus, Table, TableStatus,
    Hall, Waiter, Reservation
)
from queue_service import PriorityQueue
from order_service import OrderService


# ══════════════════════════════════════════════════════════════
# TestPriorityQueue — 7 тестів
# ══════════════════════════════════════════════════════════════
class TestPriorityQueue(unittest.TestCase):

    def setUp(self):
        self.queue   = PriorityQueue()
        self.vip     = Client(1, "Олена",  ClientType.VIP)
        self.loyal   = Client(2, "Іван",   ClientType.LOYAL)
        self.regular = Client(3, "Петро",  ClientType.REGULAR)

    def test_enqueue_increases_size(self):
        """Додавання клієнта збільшує розмір черги."""
        self.queue.enqueue(self.regular)
        self.assertEqual(len(self.queue), 1)

    def test_vip_served_before_regular(self):
        """VIP-клієнт обслуговується раніше за звичайного."""
        self.queue.enqueue(self.regular)
        self.queue.enqueue(self.vip)
        served = self.queue.dequeue()
        self.assertEqual(served.client_type, ClientType.VIP)

    def test_vip_served_before_loyal(self):
        """VIP-клієнт обслуговується раніше за постійного."""
        self.queue.enqueue(self.loyal)
        self.queue.enqueue(self.vip)
        served = self.queue.dequeue()
        self.assertEqual(served.client_type, ClientType.VIP)

    def test_loyal_served_before_regular(self):
        """Постійний клієнт обслуговується раніше за звичайного."""
        self.queue.enqueue(self.regular)
        self.queue.enqueue(self.loyal)
        served = self.queue.dequeue()
        self.assertEqual(served.client_type, ClientType.LOYAL)

    def test_dequeue_empty_raises(self):
        """Виклик dequeue() на порожній черзі генерує IndexError."""
        with self.assertRaises(IndexError):
            self.queue.dequeue()

    def test_is_empty_true_and_false(self):
        """is_empty() повертає True для порожньої черги і False після додавання."""
        self.assertTrue(self.queue.is_empty())
        self.queue.enqueue(self.regular)
        self.assertFalse(self.queue.is_empty())

    def test_peek_all_does_not_remove(self):
        """peek_all() не видаляє елементи з черги."""
        self.queue.enqueue(self.regular)
        self.queue.enqueue(self.loyal)
        result = self.queue.peek_all()
        self.assertEqual(len(result), 2)
        self.assertEqual(len(self.queue), 2)  # розмір не змінився


# ══════════════════════════════════════════════════════════════
# TestOrderService — 8 тестів
# ══════════════════════════════════════════════════════════════
class TestOrderService(unittest.TestCase):

    def setUp(self):
        self.service = OrderService()
        self.regular = Client(1, "Марія",   ClientType.REGULAR)
        self.loyal   = Client(2, "Дмитро",  ClientType.LOYAL)
        self.vip     = Client(3, "Катерина", ClientType.VIP)
        self.item    = MenuItem(1, "Піца", 100.0, "Піца")

    def test_create_order_returns_order(self):
        """create_order повертає об'єкт Order."""
        order = self.service.create_order(self.regular)
        self.assertIsInstance(order, Order)

    def test_create_order_links_client(self):
        """Замовлення прив'язане до переданого клієнта."""
        order = self.service.create_order(self.loyal)
        self.assertEqual(order.client, self.loyal)

    def test_no_discount_for_regular(self):
        """Звичайний клієнт не отримує знижки."""
        order = self.service.create_order(self.regular)
        self.service.add_item(order, OrderItem(self.item, 1))
        self.assertAlmostEqual(self.service.calculate_total(order), 100.0)

    def test_loyal_discount_10_percent(self):
        """Постійний клієнт отримує знижку 10%."""
        order = self.service.create_order(self.loyal)
        self.service.add_item(order, OrderItem(self.item, 1))
        self.assertAlmostEqual(self.service.calculate_total(order), 90.0)

    def test_vip_discount_15_percent(self):
        """VIP-клієнт отримує знижку 15%."""
        order = self.service.create_order(self.vip)
        self.service.add_item(order, OrderItem(self.item, 1))
        self.assertAlmostEqual(self.service.calculate_total(order), 85.0)

    def test_status_advance_to_in_progress(self):
        """Перший виклик advance_status переводить статус у IN_PROGRESS."""
        order = self.service.create_order(self.regular)
        self.service.advance_status(order.order_id)
        self.assertEqual(order.status, OrderStatus.IN_PROGRESS)

    def test_status_full_cycle(self):
        """Повний цикл статусів: PENDING → IN_PROGRESS → READY → COMPLETED."""
        order = self.service.create_order(self.regular)
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.service.advance_status(order.order_id)
        self.assertEqual(order.status, OrderStatus.IN_PROGRESS)
        self.service.advance_status(order.order_id)
        self.assertEqual(order.status, OrderStatus.READY)
        self.service.advance_status(order.order_id)
        self.assertEqual(order.status, OrderStatus.COMPLETED)

    def test_unavailable_item_raises_value_error(self):
        """Додавання недоступної страви генерує ValueError."""
        bad = MenuItem(99, "Суп", 50.0, "Супи", available=False)
        order = self.service.create_order(self.regular)
        with self.assertRaises(ValueError):
            self.service.add_item(order, OrderItem(bad))


# ══════════════════════════════════════════════════════════════
# TestModels — 7 тестів
# ══════════════════════════════════════════════════════════════
class TestModels(unittest.TestCase):

    def test_client_priority_values(self):
        """Пріоритети клієнтів: REGULAR=10, LOYAL=20, VIP=30."""
        self.assertEqual(Client(1, "A", ClientType.REGULAR).base_priority, 10)
        self.assertEqual(Client(2, "B", ClientType.LOYAL).base_priority,   20)
        self.assertEqual(Client(3, "C", ClientType.VIP).base_priority,     30)

    def test_order_item_subtotal(self):
        """subtotal = ціна × кількість."""
        item = MenuItem(1, "Борщ", 85.0, "Супи")
        oi   = OrderItem(item, 3)
        self.assertAlmostEqual(oi.subtotal, 255.0)

    def test_order_total_sum(self):
        """total замовлення дорівнює сумі subtotal всіх позицій."""
        client = Client(1, "Тест", ClientType.REGULAR)
        order  = Order(order_id=1, client=client)
        order.add_item(OrderItem(MenuItem(1, "Піца",  100.0, "Піца"), 2))
        order.add_item(OrderItem(MenuItem(2, "Кава",   50.0, "Напої"), 1))
        self.assertAlmostEqual(order.total, 250.0)

    def test_order_initial_status(self):
        """Нове замовлення має статус PENDING."""
        client = Client(1, "Тест", ClientType.REGULAR)
        order  = Order(order_id=1, client=client)
        self.assertEqual(order.status, OrderStatus.PENDING)

    def test_order_next_status_stops_at_completed(self):
        """Статус не виходить за межі COMPLETED при додаткових викликах."""
        client = Client(1, "Тест", ClientType.REGULAR)
        order  = Order(order_id=1, client=client)
        for _ in range(10):
            order.next_status()
        self.assertEqual(order.status, OrderStatus.COMPLETED)

    def test_table_initial_status_free(self):
        """Новий столик має статус FREE."""
        table = Table(table_id=1, hall_id=1, seats=4)
        self.assertEqual(table.status, TableStatus.FREE)

    def test_waiter_default_active_tables(self):
        """Новий офіціант має 0 активних столиків."""
        waiter = Waiter(waiter_id=1, name="Олена", level="senior")
        self.assertEqual(waiter.active_tables, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
