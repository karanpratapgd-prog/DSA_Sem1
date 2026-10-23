import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import InputError, SchedulerService  # noqa: E402


def names(state):
    return [t["name"] for t in state["queue"]]


def test_insert_orders_by_priority_then_arrival():
    s = SchedulerService()
    s.insert("low", 4)
    s.insert("a", 2)
    s.insert("b", 2)
    st = s.insert("urgent", 1)
    assert names(st) == ["urgent", "a", "b", "low"]


def test_extract_runs_next_and_logs_it():
    s = SchedulerService()
    s.insert("a", 2)
    s.insert("b", 1)
    st = s.extract()
    assert [t["name"] for t in st["ran"]] == ["b"]
    assert names(st) == ["a"]


def test_extract_empty_is_an_error():
    with pytest.raises(InputError):
        SchedulerService().extract()


@pytest.mark.parametrize("name", ["", "   ", None, 5, "x" * 41])
def test_bad_names_rejected(name):
    with pytest.raises(InputError):
        SchedulerService().insert(name, 3)


@pytest.mark.parametrize("prio", [0, 6, -1, "abc", None, True, 2.5])
def test_bad_priorities_rejected(prio):
    with pytest.raises(InputError):
        SchedulerService().insert("task", prio)


def test_numeric_string_priority_accepted_and_name_whitespace_cleaned():
    st = SchedulerService().insert("  my   task ", "2")
    assert st["queue"][0]["name"] == "my task"
    assert st["queue"][0]["priority"] == 2


def test_fifo_toggle_shows_why_tie_break_matters():
    s = SchedulerService()
    st = s.load("ties")
    assert names(st) == ["Task " + c for c in "ABCDEFG"]
    st = s.set_fifo(False)
    assert names(st) != ["Task " + c for c in "ABCDEFG"]
    st = s.set_fifo(True)
    assert names(st) == ["Task " + c for c in "ABCDEFG"]


def test_reset_keeps_fifo_setting_and_clears_tasks():
    s = SchedulerService()
    s.set_fifo(False)
    s.load("demo")
    st = s.reset()
    assert st["queue"] == [] and st["ran"] == []
    assert st["use_fifo"] is False


def test_queue_limit():
    s = SchedulerService()
    for i in range(200):
        s.insert("t%d" % i, 3)
    with pytest.raises(InputError):
        s.insert("one too many", 3)
