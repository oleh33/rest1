import heapq
from datetime import datetime
from models import Client


class PriorityQueue:
    def __init__(self):
        self._heap: list = []
        self._counter: int = 0

    def enqueue(self, client: Client) -> None:
        heapq.heappush(self._heap, (-client.base_priority, self._counter, client))
        self._counter += 1

    def dequeue(self) -> Client:
        if self._heap:
            return heapq.heappop(self._heap)[2]
        raise IndexError("Черга порожня")

    def peek_all(self) -> list:
        sorted_heap = sorted(self._heap, key=lambda x: (x[0], x[1]))
        return [item[2] for item in sorted_heap]

    def aging(self) -> None:
        updated = []
        for priority, counter, client in self._heap:
            wait = (datetime.now() - client.arrived_at).seconds // 60
            bonus = max(0, (wait - 5) // 2)
            updated.append((priority - bonus, counter, client))
        heapq.heapify(updated)
        self._heap = updated

    def __len__(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return len(self._heap) == 0
