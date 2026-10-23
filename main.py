"""
Demo of the FIFO tie-breaking priority scheduler.

Run:  python main.py
"""

from scheduler import FIFOPriorityScheduler

LINE = "-" * 66


def show_queue(sched: FIFOPriorityScheduler, title: str) -> None:
    print(f"\n{title}")
    print(LINE)
    if sched.is_empty():
        print("  (queue is empty)")
    for rank, t in enumerate(sched.snapshot(), start=1):
        print(f"  {rank}. {t.name:<18} priority={t.priority}  arrival=#{t.arrival_seq}")
    print(LINE)


def main() -> None:
    sched = FIFOPriorityScheduler(use_fifo=True)

    print("=" * 66)
    print(" FIFO TIE-BREAKING PRIORITY SCHEDULER  (1 = highest priority)")
    print("=" * 66)

    # ---- Step 1: insert six tasks (note the ties on priority 2 and 3) ----
    initial = [
        ("Backup Files",      3),
        ("Antivirus Scan",    2),
        ("Disk Cleanup",      4),
        ("Email Sync",        2),   # ties with Antivirus Scan -> arrived later
        ("Software Update",   3),   # ties with Backup Files   -> arrived later
        ("Print Document",    2),   # third task with priority 2
    ]
    print("\nSTEP 1: Insert six tasks")
    for name, prio in initial:
        t = sched.insert(name, prio)
        print(f"  inserted {t.name:<18} priority={t.priority}  arrival=#{t.arrival_seq}")
    show_queue(sched, "Queue order after inserting 6 tasks")

    # ---- Step 2: select and remove the next task ----
    print("\nSTEP 2: Select and remove the next task")
    print(f"  peek  -> {sched.peek()}")
    first = sched.extract_next()
    print(f"  extract_next -> {first}   (priority tie among 3 tasks: oldest wins)")
    show_queue(sched, "Queue after removing one task")

    # ---- Step 3: a new high-priority task arrives ----
    print("\nSTEP 3: A new HIGH-priority task arrives")
    urgent = sched.insert("Security Alert", 1)
    print(f"  inserted {urgent.name} priority={urgent.priority} arrival=#{urgent.arrival_seq}")
    print(f"  peek  -> {sched.peek()}   (jumps ahead of everything else)")
    show_queue(sched, "Queue after the high-priority arrival")

    # ---- Step 4: another task ties with an existing priority ----
    print("\nSTEP 4: Another priority-2 task arrives (tie-break test)")
    late = sched.insert("Cloud Upload", 2)
    print(f"  inserted {late.name} priority={late.priority} arrival=#{late.arrival_seq}")
    show_queue(sched, "Queue: Cloud Upload must sit BEHIND older priority-2 tasks")

    # ---- Step 5: drain the queue ----
    print("\nSTEP 5: Run all remaining tasks in order")
    order = 1
    print(f"  {order}. {first.name}  (already run in step 2)")
    while not sched.is_empty():
        order += 1
        t = sched.extract_next()
        print(f"  {order}. {t.name:<18} priority={t.priority}  arrival=#{t.arrival_seq}")

    # ---- Comparison: what if there were NO FIFO rule? ----
    print("\n" + "=" * 66)
    print(" COMPARISON: 7 equal-priority tasks, heap with and without FIFO")
    print("=" * 66)
    same_priority = [(f"Task {c}", 2) for c in "ABCDEFG"]   # arrive A,B,...,G
    print("  Arrival order:", " ".join(n[-1] for n, _ in same_priority))
    for label, use_fifo in (("Without FIFO", False), ("With FIFO   ", True)):
        s = FIFOPriorityScheduler(use_fifo=use_fifo)
        for name, prio in same_priority:
            s.insert(name, prio)
        out = []
        while not s.is_empty():
            out.append(s.extract_next().name[-1])
        print(f"  {label} run order:", " ".join(out))
    print("\n  A plain heap does not preserve arrival order among equal priorities.")
    print("  Adding the arrival number to the key restores first-come, first-served.")


if __name__ == "__main__":
    main()
