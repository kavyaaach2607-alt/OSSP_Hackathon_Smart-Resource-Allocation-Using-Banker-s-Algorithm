const $ = (id) => document.getElementById(id);
const RES = "ABCDEFGH";
let state = null;
let logCount = 0;

async function api(path, body) {
  const res = await fetch(path, body ? {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
  } : undefined);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

/* ---------------- tabs ---------------- */
function showTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  $("tab-main").classList.toggle("hidden", name !== "main");
  $("tab-tools").classList.toggle("hidden", name !== "tools");
}
document.querySelectorAll(".tab").forEach((t) => (t.onclick = () => showTab(t.dataset.tab)));

/* ---------------- rendering ---------------- */
function render(s, highlight = null) {
  state = s;
  const totals = s.available.map((a, j) => a + s.allocation.reduce((sum, row) => sum + row[j], 0));
  const cols = (cls = "") => Array.from({ length: s.m }, (_, j) => `<th class="${j === 0 ? cls : ""}">${RES[j]}</th>`).join("");

  // available pills
  $("available").innerHTML = s.available.map((v, j) => `<span class="pill"><small>${RES[j]}</small>${v}</span>`).join("");

  // state table
  let html = `<thead><tr><th rowspan="2" style="text-align:left">Proc</th>
      <th class="grp sepl" colspan="${s.m}">Allocation</th><th class="grp sepl" colspan="${s.m}">Max</th>
      <th class="grp sepl" colspan="${s.m}">Need</th></tr>
      <tr>${cols("sepl")}${cols("sepl")}${cols("sepl")}</tr></thead><tbody>`;
  const cells = (row, cls = "") => row.map((v, j) => `<td class="${(j === 0 ? "sepl " : "") + cls}">${v}</td>`).join("");
  s.max.forEach((_, i) => {
    html += `<tr class="${i === highlight ? "highlight" : ""}"><td class="proc">P${i}</td>
      ${cells(s.allocation[i])}${cells(s.max[i])}${cells(s.need[i], "need")}</tr>`;
  });
  $("stateTable").innerHTML = html + "</tbody>";

  // status card
  $("statusCard").className = "card status " + (s.safe ? "safe" : "unsafe");
  $("statusIcon").textContent = s.safe ? "✓" : "!";
  $("statusTitle").textContent = s.safe ? "System is SAFE" : "System is UNSAFE";
  $("statusSub").textContent = s.safe
    ? `All ${s.n} processes can finish in the order below — deadlock is avoided.`
    : "No order lets every process finish — deadlock is possible.";

  // sequence
  $("sequence").innerHTML = s.safe
    ? s.sequence.map((p, k) => `<span class="chip" style="animation-delay:${k * 80}ms">P${p}</span>`).join('<span class="arrow">→</span>')
    : '<span class="nosafe">No safe sequence exists</span>';

  // request form (rebuild only when the shape changed)
  const sel = $("procSelect");
  if (sel.options.length !== s.n) {
    sel.innerHTML = s.max.map((_, i) => `<option value="${i}">P${i}</option>`).join("");
  }
  if ($("reqInputs").children.length !== s.m) {
    $("reqInputs").innerHTML = Array.from({ length: s.m }, (_, j) =>
      `<div>${RES[j]}<input type="number" min="0" value="0" class="reqInput"></div>`).join("");
  }

  // usage bars (tools tab)
  $("bars").innerHTML = s.available.map((a, j) => {
    const used = totals[j] - a, pct = totals[j] ? Math.round((used / totals[j]) * 100) : 0;
    return `<div class="bar-row"><div class="bar-label"><span>Resource ${RES[j]}</span>
      <span>${used} / ${totals[j]} in use (${pct}%)</span></div>
      <div class="bar"><div class="${pct >= 85 ? "hot" : ""}" style="width:${pct}%"></div></div></div>`;
  }).join("");

  // readiness table (tools tab)
  let r = `<thead><tr><th style="text-align:left">Proc</th><th>Need</th><th>Available</th><th>Can run now?</th></tr></thead><tbody>`;
  s.need.forEach((n, i) => {
    const ok = n.every((v, j) => v <= s.available[j]);
    r += `<tr><td class="proc">P${i}</td><td>[${n.join(", ")}]</td><td>[${s.available.join(", ")}]</td>
      <td><span class="tag ${ok ? "yes" : "no"}">${ok ? "Yes" : "Waiting"}</span></td></tr>`;
  });
  $("readyTable").innerHTML = r + "</tbody>";

  $("steps").innerHTML = "";
}

function addLog(text, ok) {
  const log = $("log");
  const empty = log.querySelector(".empty");
  if (empty) empty.remove();
  const li = document.createElement("li");
  li.className = ok ? "ok" : "bad";
  li.innerHTML = `<div class="time">${new Date().toLocaleTimeString()}</div>${text}`;
  log.prepend(li);
  $("logCount").textContent = ++logCount;
}

/* ---------------- actions ---------------- */
$("sendBtn").onclick = async () => {
  const pid = Number($("procSelect").value);
  const req = [...document.querySelectorAll(".reqInput")].map((i) => Number(i.value) || 0);
  const box = $("result");
  try {
    const r = await api("/api/request", { process: pid, request: req });
    box.textContent = r.message;
    box.className = "result " + (r.granted ? "ok" : "bad");
    addLog(`P${pid} [${req.join(" ")}] → ${r.message}`, r.granted);
    render(r.state, pid);
  } catch (e) {
    box.textContent = e.message;
    box.className = "result bad";
    addLog(`P${pid} [${req.join(" ")}] → ${e.message}`, false);
  }
};

async function sampleText() {
  const s = await api("/api/sample");
  const row = (r) => "[" + r.join(", ") + "]";
  return `{\n "available": ${row(s.available)},\n "max": [\n  ${s.max.map(row).join(",\n  ")}\n ],\n "allocation": [\n  ${s.allocation.map(row).join(",\n  ")}\n ]\n}`;
}

$("resetBtn").onclick = async () => {
  $("procSelect").innerHTML = ""; $("reqInputs").innerHTML = "";
  render(await api("/api/reset", {}));
  $("result").className = "result hidden";
  addLog("State reset to sample data", true);
  $("customJson").value = await sampleText();
};

$("stepBtn").onclick = () => {
  const list = $("steps");
  list.innerHTML = "";
  if (!state.safe) { list.innerHTML = "<li class='show'>Stuck: no process can finish with the current Work.</li>"; return; }
  state.steps.forEach((st, k) => {
    const li = document.createElement("li");
    li.innerHTML = `P${st.process}: Need [${st.need}] ≤ Work [${st.work_before}] → finishes, Work = [${st.work_after}]`;
    list.appendChild(li);
    setTimeout(() => li.classList.add("show"), 600 * k);
  });
};

document.querySelectorAll(".demo").forEach((b) => {
  b.onclick = () => {
    const p = Number(b.dataset.p), vals = b.dataset.r.split(",").map(Number);
    if (p >= state.n || vals.length !== state.m) { alert("This demo fits the sample data. Press 'Reset sample' first."); return; }
    $("procSelect").value = p;
    document.querySelectorAll(".reqInput").forEach((inp, j) => (inp.value = vals[j]));
    $("result").className = "result hidden";
    showTab("main");
  };
});

$("loadBtn").onclick = async () => {
  const msg = $("loadMsg");
  try {
    const s = await api("/api/load", JSON.parse($("customJson").value));
    $("procSelect").innerHTML = ""; $("reqInputs").innerHTML = "";
    render(s);
    msg.style.color = "var(--ok)"; msg.textContent = "Loaded.";
    addLog("Custom data loaded", true);
  } catch (e) {
    msg.style.color = "var(--bad)"; msg.textContent = e.message;
    addLog("Load rejected: " + e.message, false);
  }
};

(async () => {
  render(await api("/api/state"));
  $("customJson").value = await sampleText();
})();