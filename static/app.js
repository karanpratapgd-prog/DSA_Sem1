"use strict";

const $ = (id) => document.getElementById(id);

async function api(path, body) {
  const opts = body === undefined
    ? {}
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const res = await fetch(path, opts);
  let data = {};
  try { data = await res.json(); } catch (e) { /* ignore */ }
  if (!res.ok) throw new Error(data.error || "Something went wrong (" + res.status + ").");
  return data;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function setStatus(message, isError) {
  const s = $("status");
  s.textContent = message;
  s.className = isError ? "status error" : "status";
}

function render(state) {
  $("fifo").checked = state.use_fifo;
  setStatus(state.message, false);

  // Queue in true selection order
  const q = $("queue");
  q.replaceChildren();
  state.queue.forEach((t, i) => {
    const li = el("li", "p" + t.priority + (i === 0 ? " next" : ""));
    li.appendChild(el("span", "rank", String(i + 1)));
    li.appendChild(el("span", "name", t.name));
    li.appendChild(el("span", "meta", "priority " + t.priority + " | arrived #" + t.arrival));
    if (i === 0) li.appendChild(el("span", "tag", "Next"));
    const prev = state.queue[i - 1];
    if (prev && prev.priority === t.priority) {
      li.appendChild(el("span", "tag tie", state.use_fifo ? "tie: earlier arrival first" : "tie"));
    }
    q.appendChild(li);
  });
  $("queue-empty").hidden = state.queue.length > 0;
  $("queue-count").textContent = state.queue.length + (state.queue.length === 1 ? " task waiting" : " tasks waiting");

  // Heap array
  const h = $("heap");
  h.replaceChildren();
  state.heap.forEach((t, i) => {
    const c = el("div", "cell p" + t.priority);
    c.appendChild(el("span", "idx", "[" + i + "]"));
    c.appendChild(el("span", "nm", t.name));
    c.appendChild(el("span", "idx", "p" + t.priority + ", #" + t.arrival));
    h.appendChild(c);
  });
  $("heap-empty").hidden = state.heap.length > 0;

  // Run log
  const r = $("ran");
  r.replaceChildren();
  state.ran.forEach((t, i) => {
    const li = el("li");
    li.appendChild(el("span", "rank", String(i + 1)));
    li.appendChild(el("span", "name", t.name));
    li.appendChild(el("span", "chip p" + t.priority, "priority " + t.priority));
    li.appendChild(el("span", "meta", "arrived #" + t.arrival));
    r.appendChild(li);
  });
  $("ran-empty").hidden = state.ran.length > 0;
}

async function act(path, body) {
  try {
    render(await api(path, body));
    return true;
  } catch (err) {
    setStatus(err.message, true);
    return false;
  }
}

$("add-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const name = $("name").value;
  const priority = parseInt($("priority").value, 10);
  if (await act("/api/insert", { name: name, priority: priority })) {
    $("name").value = "";
  }
  $("name").focus();
});
$("run-next").addEventListener("click", () => act("/api/extract", {}));
$("reset").addEventListener("click", () => act("/api/reset", {}));
$("load-demo").addEventListener("click", () => act("/api/load", { kind: "demo" }));
$("load-ties").addEventListener("click", () => act("/api/load", { kind: "ties" }));
$("fifo").addEventListener("change", (ev) => act("/api/fifo", { use_fifo: ev.target.checked }));

api("/api/state").then(render).catch((err) => setStatus(err.message, true));
