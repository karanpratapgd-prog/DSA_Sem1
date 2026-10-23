import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler import FIFOPriorityScheduler  # noqa: E402


def drain(s):
    out = []
    while not s.is_empty():
        out.append(s.extract_next())
    return out


def test_highest_priority_first():
    s = FIFOPriorityScheduler()
    s.insert("low", 5)
    s.insert("high", 1)
    s.insert("mid", 3)
    assert [t.name for t in drain(s)] == ["high", "mid", "low"]


def test_fifo_tie_break():
    s = FIFOPriorityScheduler()
    for name in ["a", "b", "c", "d"]:
        s.insert(name, 2)
    assert [t.name for t in drain(s)] == ["a", "b", "c", "d"]


def test_late_high_priority_jumps_queue():
    s = FIFOPriorityScheduler()
    for i in range(6):
        s.insert(f"t{i}", 3)
    s.extract_next()
    s.insert("urgent", 1)
    assert s.extract_next().name == "urgent"


def test_late_equal_priority_goes_behind():
    s = FIFOPriorityScheduler()
    s.insert("old", 2)
    s.insert("other", 3)
    s.insert("new", 2)
    assert [t.name for t in drain(s)] == ["old", "new", "other"]


def test_empty_queue():
    s = FIFOPriorityScheduler()
    assert s.extract_next() is None
    assert s.peek() is None
    assert len(s) == 0


def test_random_matches_sorted_reference():
    rng = random.Random(42)
    for _ in range(200):
        s = FIFOPriorityScheduler()
        reference = []
        for i in range(rng.randint(1, 40)):
            p = rng.randint(1, 5)
            t = s.insert(f"t{i}", p)
            reference.append((p, t.arrival_seq, t.name))
        expected = [name for _, _, name in sorted(reference)]
        assert [t.name for t in drain(s)] == expected
