from abc import ABC, abstractmethod
from models import Order, Client, ClientType, OrderItem


class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, total: float) -> float:
        pass


class NoDiscount(DiscountStrategy):
    def apply(self, total: float) -> float:
        return total


class LoyalDiscount(DiscountStrategy):
    def apply(self, total: float) -> float:
        return total * 0.90


class VIPDiscount(DiscountStrategy):
    def apply(self, total: float) -> float:
        return total * 0.85


class OrderService:
    def __init__(self):
        self._orders: dict = {}
        self._next_id: int = 1
        self._strategies = {
            ClientType.REGULAR: NoDiscount(),
            ClientType.LOYAL:   LoyalDiscount(),
            ClientType.VIP:     VIPDiscount(),
        }

    def create_order(self, client: Client) -> Order:
        order = Order(order_id=self._next_id, client=client)
        self._orders[self._next_id] = order
        self._next_id += 1
        return order

    def add_item(self, order: Order, item: OrderItem) -> None:
        if not item.menu_item.available:
            raise ValueError(f"{item.menu_item.name} недоступна")
        order.add_item(item)

    def calculate_total(self, order: Order) -> float:
        strategy = self._strategies[order.client.client_type]
        return round(strategy.apply(order.total), 2)

    def advance_status(self, order_id: int) -> str:
        order = self._orders[order_id]
        order.next_status()
        return order.status.value

    def get_order(self, order_id: int):
        return self._orders.get(order_id)

    def get_all_orders(self) -> list:
        return list(self._orders.values())
