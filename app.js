const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
let CAT = [], filterCat = "all", query = "";

async function load() {
  const c = await (await fetch("catalog.json", { cache: "no-store" })).json();
  CAT = c.datasets;
  $("#hcount").textContent = CAT.length;
  const cats = ["all", ...new Set(CAT.map(d => d.category))];
  $("#filters").innerHTML = cats.map(c =>
    `<button data-cat="${esc(c)}" class="${c === "all" ? "on" : ""}">${c === "all" ? "All" : esc(c)}</button>`).join("");
  document.querySelectorAll("#filters button").forEach(b => b.onclick = () => {
    filterCat = b.dataset.cat;
    document.querySelectorAll("#filters button").forEach(x => x.classList.toggle("on", x === b));
    render();
  });
  $("#search").addEventListener("input", e => { query = e.target.value.toLowerCase(); render(); });
  render();
}

function match(d) {
  if (filterCat !== "all" && d.category !== filterCat) return false;
  if (!query) return true;
  return (d.name + " " + d.description + " " + d.category).toLowerCase().includes(query);
}

function render() {
  const list = CAT.filter(match);
  $("#grid").innerHTML = list.length ? list.map(d => `
    <div class="card" data-slug="${esc(d.slug)}">
      <div class="row"><span class="cat">${esc(d.category)}</span>
        <span class="badge ${esc(d.tier)}">${esc(d.tier)}</span></div>
      <h3>${esc(d.name)}</h3>
      <p class="desc">${esc(d.description)}</p>
      <div class="meta">
        <span>${d.rows.toLocaleString()} rows</span><span>${esc(d.format)}</span>
        <span class="status ${esc(d.status)}">${d.status === "available" ? "● download a sample" : "● importing"}</span>
      </div>
    </div>`).join("") : `<p class="muted">No datasets match that search.</p>`;
  document.querySelectorAll(".card").forEach(c => c.onclick = () => openDetail(c.dataset.slug));
}

function openDetail(slug) {
  const d = CAT.find(x => x.slug === slug);
  if (!d) return;
  const schema = `<table class="schema">${d.schema.map(f =>
    `<tr><td><code>${esc(f.field)}</code></td><td class="muted">${esc(f.type)}</td></tr>`).join("")}</table>`;
  const samples = d.samples.map(s => esc(JSON.stringify(s, null, 2))).join("\n\n");
  const dl = d.status === "available" && d.sample_download
    ? `<a class="dlbtn" href="${esc(d.sample_download)}" download>⬇ Download sample (.jsonl)</a>
       <span class="lic">${esc(d.license)}</span>`
    : `<a class="notify" href="mailto:build@opendiabetic.com?subject=Notify me: ${esc(d.name)}">🔔 Notify me when it lands</a>
       <span class="lic">Full set importing · ${esc(d.license)}</span>`;
  $("#detailBody").innerHTML = `
    <span class="badge ${esc(d.tier)}">${esc(d.tier)}</span> <h2>${esc(d.name)}</h2>
    <p class="sub">${esc(d.category)} — ${esc(d.description)}</p>
    <div class="kv">
      <div class="k"><b>${d.rows.toLocaleString()}</b><span>rows</span></div>
      <div class="k"><b>${esc(d.format)}</b><span>format</span></div>
      <div class="k"><b>${esc(d.size)}</b><span>size</span></div>
      <div class="k"><b class="${d.status === "available" ? "green" : ""}">${d.status}</b><span>status</span></div>
    </div>
    <h4>Schema</h4>${schema}
    <h4>Real sample rows (verify before you download)</h4>
    <pre class="sample">${samples}</pre>
    <h4>SHA-256</h4><p class="hash">${esc(d.sha256)}</p>
    <div class="dlbar">${dl}</div>`;
  $("#detail").classList.remove("hide");
  document.body.style.overflow = "hidden";
}
function closeDetail() { $("#detail").classList.add("hide"); document.body.style.overflow = ""; }
$("#closeDetail").onclick = closeDetail;
$("#detail").addEventListener("click", e => { if (e.target.id === "detail") closeDetail(); });
document.addEventListener("keydown", e => { if (e.key === "Escape") closeDetail(); });

load();
