[README.md](https://github.com/user-attachments/files/33864837/README.md)
# Priority-Based Task Scheduling in a Computer System

A data structures team project that compares **four approaches** to scheduling
tasks by priority, with working code, an animated visualizer, charts, tests, and a
written report.

| # | Approach | Core idea | Where it lives in this repo |
|---|----------|-----------|-----------------------------|
| 1 | [Unsorted list](#approach-1-unsorted-list) | Add at the end, scan to find the best task | Visualizer, tab 1 |
| 2 | [Sorted list](#approach-2-sorted-list) | Keep the best task at the front, insert in order | Visualizer, tab 2 |
| 3 | [Binary heap (priority queue)](#approach-3-binary-heap-priority-queue) | Best task always at the root of a tree | Visualizer, tab 3, and the heap web page |
| 4 | [FIFO tie-breaking](#approach-4-fifo-tie-breaking-first-come-first-served) | An arrival number settles equal priorities | Python project (`scheduler.py`, `app.py`, ...) |

---

## Contents

1. [The problem](#the-problem)
2. [The rule every approach follows](#the-rule-every-approach-follows)
3. [Quick start](#quick-start)
4. [Approach 1: Unsorted list](#approach-1-unsorted-list)
5. [Approach 2: Sorted list](#approach-2-sorted-list)
6. [Approach 3: Binary heap (priority queue)](#approach-3-binary-heap-priority-queue)
7. [Approach 4: FIFO tie-breaking (first-come, first-served)](#approach-4-fifo-tie-breaking-first-come-first-served)
8. [Worked example](#worked-example)
9. [Complexity comparison](#complexity-comparison)
10. [Project structure](#project-structure)
11. [Testing](#testing)
12. [Limitations and future work](#limitations-and-future-work)
13. [Uploading to GitHub](#uploading-to-github)
14. [References](#references)

---

## The problem

A computer runs many tasks, and some are more urgent than others. The scheduler must
always pick the most important waiting task, even while new tasks keep arriving.

The assignment asks us to:

- insert at least six tasks,
- show how the next task is selected and removed,
- show what happens when another high-priority task arrives,
- define how ties between equal priorities are resolved,
- implement the scheduling logic, and
- compare the time complexity of an unsorted list, a sorted list, and a binary heap.

Each approach below answers all six points.

## The rule every approach follows

All four approaches select tasks with the same two-step rule:

1. **The higher priority runs first.**
2. **If priorities are equal, the task that arrived first runs first** (first-come,
   first-served). Every task gets an *arrival number* when it is added, and the
   smaller arrival number wins.

Because arrival numbers are never repeated, there are never two tasks that tie
completely, so the run order is always the same for the same input.

> **Priority numbering differs between files.** The visualizer and the heap web page
> treat a **higher number as more urgent** (the visualizer uses 1 to 10, with 10 the
> most urgent). The Python project treats **1 as the most urgent** (priorities 1 to 5).
> The rule is identical; only the numbering is reversed.

---

## Quick start

### Open the animated visualizer (approaches 1 to 3)

No installation needed. Open `team/priority_task_scheduler_visualizer.html` in any
web browser (double-click it). Use the tabs to switch between the three data
structures, press **Run next task** to watch a task move from *Waiting* to *Running*
to *Completed*, and press **Add urgent task** to see a priority-10 task jump ahead.

### Open the heap scheduler web page (approach 3)

Open `team/heap_scheduler_web.html` in a browser. Add tasks with a name, priority and
burst duration, then press **Run All Tasks** to see them executed in priority order.

### Run the Python project (approach 4)

You need **Python 3.9 or newer**.

```bash
# the localhost web app (takes your input; uses only the standard library)
python app.py                # opens http://127.0.0.1:8000 in your browser
python app.py --port 9000    # use another port
python app.py --no-browser   # do not open the browser automatically

# the rest of the Python tools
pip install -r requirements.txt
python main.py               # step-by-step console demo
python visualize.py          # regenerates the charts in ./charts
python -m pytest -q tests    # runs the 25 tests
```

On Mac or Linux, use `python3` and `pip3` if `python` is not found. Stop the web app
with `Ctrl+C`. It listens on `127.0.0.1` only, so it can be reached from your own
computer and nowhere else.

---

## Approach 1: Unsorted list

**Idea.** Keep waiting tasks in a plain list in the order they arrive. To pick the
next task, scan the whole list and choose the best one.

```
Waiting list (arrival order):  T1(4)  T2(2)  T3(8)  T4(3)  T5(5)  T6(5)
Pick next: scan all six, choose T3 (highest priority)
```

**How it works.**

- **Insert:** append at the end.
- **Pick next:** look at every task and keep the best one. On a tie the earlier
  arrival wins.
- **Remove:** take the chosen task out of the list.

The visualizer does this with one comparison function and a scan:

```js
// higher priority first; on a tie, smaller arrival number first
function compare(a, b) { return b.priority - a.priority || a.seq - b.seq }

// unsorted list: scan every task and keep the best
tasks.reduce((best, t) => compare(t, best) < 0 ? t : best)
```

| Operation | Time | Why |
|-----------|------|-----|
| Insert | O(1) | append at the end |
| Pick next | O(n) | every task must be checked |
| Remove | O(n)* | locate the chosen task, then take it out |

\* On an array-backed list, locating and removing the chosen item can cost O(n).

**Good when** tasks are added often and picked rarely. **Weak when** picks are
frequent, because each pick scans everything.

**In this repo:** `team/priority_task_scheduler_visualizer.html`, tab *1. Unsorted List*.
The "Selection checks" counter on the page shows how many tasks were scanned.

---

## Approach 2: Sorted list

**Idea.** Keep the list ordered from highest to lowest priority at all times. The
next task is simply the first one.

```
Sorted list:  T3(8)  T5(5)  T6(5)  T1(4)  T4(3)  T2(2)
Pick next: take the first task, T3
```

**How it works.**

- **Insert:** find the correct position and shift later tasks to make room. Equal
  priorities are placed behind older ones, so first-come, first-served still holds.
- **Pick next:** read the first item.
- **Remove:** drop the first item.

```js
// sorted list: keep the tasks ordered best-first
tasks.slice().sort(compare)
```

| Operation | Time | Why |
|-----------|------|-----|
| Insert | O(n) | find the place and shift others |
| Pick next | O(1) | it is the first task |
| Remove | O(1)† | drop the first task |

† With the best task kept at the front of a linked list. Removing from the front of
an array needs a shift.

**Good when** picks are frequent and inserts are rare. **Weak when** many tasks
arrive, because every insert shifts the list.

**In this repo:** `team/priority_task_scheduler_visualizer.html`, tab *2. Sorted List*.

---

## Approach 3: Binary heap (priority queue)

**Idea.** Store the tasks in a binary tree where every parent is at least as good as
its children. The best task is therefore always at the root, and both inserting and
removing only walk one path down or up the tree.

```
                 T3 (8)                Stored in an array:
               /        \              [ T3, T5, T6, T2, T4, T1 ]
          T5 (5)        T6 (5)
         /      \       /
     T2 (2)   T4 (3)  T1 (4)
```

The tree is stored in a flat array using index arithmetic:

```
parent(i) = (i - 1) // 2
left(i)   = 2*i + 1
right(i)  = 2*i + 2
```

**How it works.**

- **Insert:** add the task at the end of the array, then *sift up*: swap it with its
  parent while it is better than the parent.
- **Pick next:** read the root (index 0).
- **Remove:** take the root, move the last task into its place, then *sift down*:
  swap it with the better child until the heap order is restored.

| Operation | Time | Why |
|-----------|------|-----|
| Insert | O(log n) | sift up along one path |
| Pick next | O(1) | read the root |
| Remove | O(log n) | sift down along one path |

A tree of n tasks is only about log₂ n levels tall, which is where O(log n) comes
from. For n inserts and n removals the total is O(n log n), against O(n²) for the
two list approaches.

**In this repo:**

- `team/priority_task_scheduler_visualizer.html`, tab *3. Binary Heap*, shows the
  idea with the same tasks and comparison rule as the other tabs.
- `team/heap_scheduler_web.html` is a small standalone page with a working heap
  (`HeapScheduler` class with `insert` and `extract`). Its comparison key is
  `[-priority, seq]`, so a higher priority wins and earlier arrivals win ties.
- `scheduler.py` is the Python version (see approach 4).

---

## Approach 4: FIFO tie-breaking (first-come, first-served)

**Idea.** A heap alone does not promise to keep equal-priority tasks in arrival
order. This approach fixes that by giving every task an **arrival number** and
comparing tasks by the pair **(priority, arrival number)**. Priority decides first;
the arrival number decides only when priorities are equal.

```python
@dataclass
class Task:
    name: str
    priority: int            # 1 = most urgent
    arrival_seq: int = -1    # stamped by the scheduler on insert
    burst_time: int = 1

    def key(self, use_fifo=True):
        if use_fifo:
            return (self.priority, self.arrival_seq)   # ties broken by arrival
        return (self.priority,)                        # ties left to the heap
```

Python compares tuples left to right, so `(2, 1) < (2, 3)` is true: same priority,
earlier arrival. Because arrival numbers are unique, no two tasks ever compare equal.

**Why it is needed.** Seven tasks, all priority 2, arrive in the order A to G:

| Rule | Run order |
|------|-----------|
| Arrival order | A B C D E F G |
| Heap on priority only | A G F E D C B |
| Heap with arrival number | A B C D E F G |

Without the arrival number, six of the seven tasks run out of arrival order. With
it, the order is exactly first-come, first-served. Switch the **FIFO tie-break**
option in the web app on and off to see this yourself.

**Cost.** Comparing two `(priority, arrival)` pairs takes constant time, so the
heap bounds do not change: insert O(log n), pick next O(1), remove O(log n), and
space O(n). Looking at the next task with `peek()` is O(1).

**The Python files.**

| File | Purpose |
|------|---------|
| `scheduler.py` | `Task` and `FIFOPriorityScheduler`: a hand-written binary min-heap with `insert`, `peek`, `extract_next`, `set_fifo`, `snapshot` |
| `main.py` | Console demo: six tasks, remove the next, urgent arrival, late tie, and the A to G experiment |
| `app.py` | Localhost web app and JSON API (Python standard library only) |
| `static/` | The web page the app serves (`index.html`, `style.css`, `app.js`) |
| `visualize.py` | Draws the three charts in `charts/` with matplotlib |
| `tests/` | 25 automated tests |

**The web app.** Run `python app.py`. You can add tasks (a name and a priority from
1 to 5), press **Run next task**, load sample data, and turn the FIFO tie-break on
or off. The page shows the queue in the exact order tasks will run, the internal
heap array, and the order in which tasks have already run. Invalid input, such as an
empty name or a priority of 99, gets a clear message.

---

## Worked example

The visualizer starts with six tasks (higher number = more urgent):

| Task | Name | Priority | Arrival |
|------|------|----------|---------|
| T1 | System update | 4 | 1 |
| T2 | Email sync | 2 | 2 |
| T3 | Security scan | 8 | 3 |
| T4 | File indexing | 3 | 4 |
| T5 | Memory cleanup | 5 | 5 |
| T6 | Database backup | 5 | 6 |

**Run order:** T3, T5, T6, T1, T4, T2.

- T3 runs first because 8 is the highest priority.
- T5 runs before T6. Both have priority 5, and T5 arrived first.

**Urgent task arrives.** Press *Add urgent task* to add `HP1` with priority 10. It
arrived last but runs first: HP1, T3, T5, T6, T1, T4, T2.

All three data structures give exactly this order, because they use the same rule.
Only the cost of getting there differs.

**Python demo (`python main.py`).** The console demo uses six different tasks,
where **1 is the most urgent**: Backup Files (3), Antivirus Scan (2), Disk Cleanup (4),
Email Sync (2), Software Update (3), Print Document (2). It runs Antivirus Scan,
adds a priority-1 Security Alert, then a late priority-2 Cloud Upload. The final
order is: Antivirus Scan, Security Alert, Email Sync, Print Document, Cloud Upload,
Backup Files, Software Update, Disk Cleanup. Cloud Upload waits behind the older
priority-2 tasks, and Security Alert jumps to the front of everything waiting.

---

## Complexity comparison

*n* is the number of tasks waiting.

| Approach | Insert | Pick next | Remove | n inserts + n removals | Space |
|----------|--------|-----------|--------|------------------------|-------|
| Unsorted list | O(1) | O(n) | O(n)* | O(n²) | O(n) |
| Sorted list | O(n) | O(1) | O(1)† | O(n²) | O(n) |
| Binary heap | O(log n) | O(1) | O(log n) | O(n log n) | O(n) |
| Heap with FIFO key | O(log n) | O(1) | O(log n) | O(n log n) | O(n) |

\* Locating and removing the chosen task. † With the best task kept at the front.

**Which to choose?** The lists each make one operation fast and the other slow. The
heap keeps both at O(log n) or better, which is why it is the practical choice for a
scheduler that handles many tasks. Adding the arrival number gives fair,
predictable ties at no extra asymptotic cost.

The "Selection checks" counter in the visualizer is an illustration of the work done,
not a precise count of machine instructions.

---

## Project structure

```
.
├── README.md                    this file
├── requirements.txt             matplotlib and pytest (the web app needs neither)
├── scheduler.py                 Task + FIFOPriorityScheduler (binary heap, FIFO key)
├── main.py                      console demo
├── app.py                       localhost web app and JSON API
├── static/
│   ├── index.html               web app page
│   ├── style.css                web app styles (light and dark)
│   └── app.js                   web app behaviour
├── visualize.py                 generates the charts
├── charts/                      PNG charts (slide size)
│   └── report/                  PNG charts (print size, used in the report)
├── tests/
│   ├── test_scheduler.py        tests for the heap and FIFO rule (6 tests)
│   └── test_app_service.py      tests for input checks and the web service (19 tests)
├── team/
│   ├── priority_task_scheduler_visualizer.html   animated visualizer, approaches 1 to 3
│   └── heap_scheduler_web.html                   standalone binary-heap scheduler page
└── report/
    ├── FIFO_Tie_Breaking_Scheduler_Report.docx   10-page report
    └── FIFO_Tie_Breaking_Scheduler_Report.pdf    PDF copy of the report
```

## Testing

```bash
pip install -r requirements.txt
python -m pytest -q tests
```

The 25 tests cover:

- the highest priority runs first,
- equal priorities run in arrival order,
- a late high-priority task jumps to the front,
- a late equal-priority task waits behind older ones,
- an empty queue returns nothing instead of failing,
- a randomized check: 200 random queues are drained and compared with Python's
  `sorted()` on `(priority, arrival)`, and the results must match exactly,
- input checks in the web service: empty or too-long names, priorities outside 1 to 5,
  and the queue size limit,
- switching the FIFO rule on and off, and clearing the queue.

## Limitations and future work

- **No preemption.** A running task is never interrupted, so a new urgent task waits
  until the current one finishes.
- **Starvation.** Low-priority tasks can wait a very long time if urgent tasks keep
  arriving. The usual fix is *aging*: slowly raise the priority of tasks that have
  waited.
- **Heap web page input check.** In `team/heap_scheduler_web.html`, leaving the
  priority box blank turns the value into `NaN`, which breaks the ordering. The page
  should reject blank input. The Python app already checks that a priority is a
  whole number from 1 to 5.
- **In-memory only.** The web app keeps its data in memory, so the queue is cleared
  when the server stops.

## References

Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). *Introduction to
algorithms* (4th ed.). MIT Press.

Knuth, D. E. (1998). *The art of computer programming: Vol. 3. Sorting and searching*
(2nd ed.). Addison-Wesley.

Sedgewick, R., & Wayne, K. (2011). *Algorithms* (4th ed.). Addison-Wesley.

Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). *Operating system concepts*
(10th ed.). Wiley.

Williams, J. W. J. (1964). Algorithm 232: Heapsort. *Communications of the ACM, 7*(6),
347–348. https://doi.org/10.1145/512274.512284
