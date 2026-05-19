from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import List


class ClientType(Enum):
    REGULAR = "regular"
    LOYAL   = "loyal"
    VIP     = "vip"


class OrderStatus(Enum):
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    READY       = "ready"
    COMPLETED   = "completed"


class TableStatus(Enum):
    FREE     = "free"
    RESERVED = "reserved"
    OCCUPIED = "occupied"


@dataclass
class MenuItem:
    item_id:   int
    name:      str
    price:     float
    category:  str
    available: bool = True


@dataclass
class OrderItem:
    menu_item: MenuItem
    quantity:  int = 1

    @property
    def subtotal(self) -> float:
        return self.menu_item.price * self.quantity


@dataclass
class Client:
    client_id:    int
    name:         str
    client_type:  ClientType = ClientType.REGULAR
    bonus_points: int = 0
    arrived_at:   datetime = field(default_factory=datetime.now)

    @property
    def base_priority(self) -> int:
        return {
            ClientType.REGULAR: 10,
            ClientType.LOYAL:   20,
            ClientType.VIP:     30,
        }[self.client_type]


@dataclass
class Order:
    order_id:   int
    client:     Client
    items:      List[OrderItem] = field(default_factory=list)
    status:     OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)

    def add_item(self, item: OrderItem) -> None:
        self.items.append(item)

    @property
    def total(self) -> float:
        return sum(i.subtotal for i in self.items)

    def next_status(self) -> None:
        transitions = {
            OrderStatus.PENDING:     OrderStatus.IN_PROGRESS,
            OrderStatus.IN_PROGRESS: OrderStatus.READY,
            OrderStatus.READY:       OrderStatus.COMPLETED,
        }
        if self.status in transitions:
            self.status = transitions[self.status]


@dataclass
class Table:
    table_id: int
    hall_id:  int
    seats:    int
    status:   TableStatus = TableStatus.FREE


@dataclass
class Hall:
    hall_id: int
    name:    str
    tables:  List[Table] = field(default_factory=list)


@dataclass
class Waiter:
    waiter_id:     int
    name:          str
    level:         str = "junior"  # junior | senior
    active_tables: int = 0


@dataclass
class Reservation:
    reservation_id: int
    client_name:    str
    table:          Table
    waiter:         Waiter
    hall:           Hall
    guests:         int  = 2
    note:           str  = ""
    seated:         bool = False
    closed:         bool = False
    created_at:     datetime = field(default_factory=datetime.now)
