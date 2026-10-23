"""
FIFO Tie-Breaking Priority Scheduler
====================================

A priority-based task scheduler whose tie-breaking rule is
First-Come, First-Served (FIFO).

Selection rule
--------------
1. The task with the HIGHEST priority is selected first.
   (Convention: a SMALLER number means a HIGHER priority, 1 = most urgent.)
2. If two tasks have the SAME priority, the one that ARRIVED FIRST wins.

How FIFO is guaranteed
----------------------
Every task receives a strictly increasing arrival sequence number when it is
inserted. The scheduler orders tasks by the composite key

        (priority, arrival_seq)

Because arrival_seq is unique, no two tasks ever compare as equal, so the
order of selection is fully deterministic.

Data structure
--------------
A hand-written binary min-heap stored in a Python list (array representation):
    parent(i) = (i - 1) // 2
    left(i)   = 2 * i + 1
    right(i)  = 2 * i + 2
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Task:
    """A unit of work waiting to be scheduled."""

    name: str
    priority: int                 # 1 = highest priority
    arrival_seq: int = -1         # assigned by the scheduler on insert
    burst_time: int = 1           # simulated run time (used by the visualizer)

    def key(self, use_fifo: bool = True) -> Tuple[int, ...]:
        """Comparison key. With FIFO on, ties are broken by arrival order."""
        if use_fifo:
            return (self.priority, self.arrival_seq)
        return (self.priority,)

    def __repr__(self) -> str:
        return f"{self.name}(p={self.priority}, #{self.arrival_seq})"


class FIFOPriorityScheduler:
    """Binary-heap priority scheduler with FIFO tie-breaking."""

    def __init__(self, use_fifo: bool = True) -> None:
        self._heap: List[Task] = []
        self._counter: int = 0          # next arrival sequence number
        self.use_fifo = use_fifo        # False = plain heap, ties undefined

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _less(self, a: Task, b: Task) -> bool:
        return a.key(self.use_fifo) < b.key(self.use_fifo)

    def _swap(self, i: int, j: int) -> None:
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]

    def _sift_up(self, i: int) -> None:
        while i > 0:
            parent = (i - 1) // 2
            if self._less(self._heap[i], self._heap[parent]):
                self._swap(i, parent)
                i = parent
            else:
                break

    def _sift_down(self, i: int) -> None:
        n = len(self._heap)
        while True:
            left, right = 2 * i + 1, 2 * i + 2
            smallest = i
            if left < n and self._less(self._heap[left], self._heap[smallest]):
                smallest = left
            if right < n and self._less(self._heap[right], self._heap[smallest]):
                smallest = right
            if smallest == i:
                break
            self._swap(i, smallest)
            i = smallest

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def insert(self, name: str, priority: int, burst_time: int = 1) -> Task:
        """Add a task. O(log n). Stamps it with the next arrival number."""
        task = Task(name, priority, self._counter, burst_time)
        self._counter += 1
        self._heap.append(task)
        self._sift_up(len(self._heap) - 1)
        return task

    def set_fifo(self, use_fifo: bool) -> None:
        """Switch the tie-break rule and rebuild the heap from the waiting tasks.

        Tasks keep their original arrival numbers and are re-inserted in
        arrival order, so the new rule is applied consistently.
        """
        tasks = sorted(self._heap, key=lambda t: t.arrival_seq)
        self.use_fifo = use_fifo
        self._heap = []
        for t in tasks:
            self._heap.append(t)
            self._sift_up(len(self._heap) - 1)

    def peek(self) -> Optional[Task]:
        """Return the next task without removing it. O(1)."""
        return self._heap[0] if self._heap else None

    def extract_next(self) -> Optional[Task]:
        """Remove and return the next task to run. O(log n)."""
        if not self._heap:
            return None
        top = self._heap[0]
        last = self._heap.pop()
        if self._heap:
            self._heap[0] = last
            self._sift_down(0)
        return top

    def __len__(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return not self._heap

    def snapshot(self) -> List[Task]:
        """Tasks in the order they WOULD be selected (non-destructive)."""
        return sorted(self._heap, key=lambda t: t.key(self.use_fifo))

    def heap_array(self) -> List[Task]:
        """The raw heap array (for showing the internal structure)."""
        return list(self._heap)
