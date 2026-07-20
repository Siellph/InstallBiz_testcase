const tbody = document.getElementById("files-tbody");
const paginationEl = document.getElementById("pagination");
const selectedCountEl = document.getElementById("selected-count");
const sortHeader = document.getElementById("sort-header");
const calculateBtn = document.getElementById("calculate-btn");
const resultsBlock = document.getElementById("results");
const totalStatsTable = document.getElementById("total-stats-table");
const perFileStatsEl = document.getElementById("per-file-stats");

const PER_PAGE = 20;

let currentPage = 1;
let sortDir = "desc";
let totalFiles = 0;
let currentPageNames = [];
const selected = new Set();

async function loadPage(page) {
    currentPage = page;
    const resp = await fetch(
        `/api/files?page=${page}&per_page=${PER_PAGE}&sort=${sortDir}`
    );
    const data = await resp.json();

    totalFiles = data.total;
    currentPageNames = data.files.map((f) => f.name);

    renderTable(data.files);
    renderPagination();
    updateSelectedCount();
}

function renderTable(files) {
    tbody.innerHTML = "";
    for (const f of files) {
        const tr = document.createElement("tr");

        const tdCheck = document.createElement("td");
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.checked = selected.has(f.name);
        cb.addEventListener("change", () => {
            if (cb.checked) selected.add(f.name);
            else selected.delete(f.name);
            updateSelectedCount();
        });
        tdCheck.appendChild(cb);

        const tdName = document.createElement("td");
        tdName.textContent = f.name;

        const tdTime = document.createElement("td");
        tdTime.textContent = f.downloaded_at;

        tr.append(tdCheck, tdName, tdTime);
        tbody.appendChild(tr);
    }
}

function renderPagination() {
    paginationEl.innerHTML = "";
    const totalPages = Math.max(1, Math.ceil(totalFiles / PER_PAGE));

    for (let p = 1; p <= totalPages; p++) {
        const btn = document.createElement("button");
        btn.textContent = p;
        btn.className = p === currentPage ? "page-btn active" : "page-btn";
        btn.addEventListener("click", () => loadPage(p));
        paginationEl.appendChild(btn);
    }
}

function updateSelectedCount() {
    selectedCountEl.textContent = `Выбрано: ${selected.size}`;
}

sortHeader.addEventListener("click", () => {
    sortDir = sortDir === "desc" ? "asc" : "desc";
    loadPage(1);
});

document.getElementById("select-page-btn").addEventListener("click", () => {
    currentPageNames.forEach((n) => selected.add(n));
    loadPage(currentPage);
});

document.getElementById("select-all-btn").addEventListener("click", async () => {
    const resp = await fetch("/api/files/all-names");
    const data = await resp.json();
    data.names.forEach((n) => selected.add(n));
    loadPage(currentPage);
});

document.getElementById("clear-selection-btn").addEventListener("click", () => {
    selected.clear();
    loadPage(currentPage);
});

calculateBtn.addEventListener("click", async () => {
    if (selected.size === 0) return;

    const resp = await fetch("/api/files/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ files: Array.from(selected) }),
    });
    const data = await resp.json();
    renderResults(data);
});

function renderResults(data) {
    resultsBlock.hidden = false;

    totalStatsTable.innerHTML = "";
    const headerRow = document.createElement("tr");
    const bodyRow = document.createElement("tr");

    for (let d = 0; d <= 9; d++) {
        const th = document.createElement("th");
        th.textContent = d;
        headerRow.appendChild(th);

        const td = document.createElement("td");
        td.textContent = data.total[String(d)];
        bodyRow.appendChild(td);
    }
    totalStatsTable.append(headerRow, bodyRow);

    perFileStatsEl.innerHTML = "";
    for (const [name, stats] of Object.entries(data.per_file)) {
        const wrapper = document.createElement("div");
        wrapper.className = "per-file-block";

        const title = document.createElement("h3");
        title.textContent = name;
        wrapper.appendChild(title);

        const table = document.createElement("table");
        table.className = "stats-table";
        const hRow = document.createElement("tr");
        const bRow = document.createElement("tr");

        for (let d = 0; d <= 9; d++) {
            const th = document.createElement("th");
            th.textContent = d;
            hRow.appendChild(th);

            const td = document.createElement("td");
            td.textContent = stats[String(d)];
            bRow.appendChild(td);
        }

        table.append(hRow, bRow);
        wrapper.appendChild(table);
        perFileStatsEl.appendChild(wrapper);
    }
}

loadPage(1);
