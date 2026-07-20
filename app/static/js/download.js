const startBtn = document.getElementById("start-btn");
const progressBlock = document.getElementById("progress");
const startedAtEl = document.getElementById("started-at");
const statusMessageEl = document.getElementById("status-message");
const downloadedCountEl = document.getElementById("downloaded-count");
const totalCountEl = document.getElementById("total-count");
const progressBarInner = document.getElementById("progress-bar-inner");

let pollTimer = null;

async function pollStatus() {
    const resp = await fetch("/api/download/status");
    const state = await resp.json();

    startedAtEl.textContent = state.started_at_nsk || "—";
    statusMessageEl.textContent = state.message || "—";
    downloadedCountEl.textContent = state.downloaded;
    totalCountEl.textContent = state.total_seen;

    const pct = state.total_seen
        ? Math.round((state.downloaded / state.total_seen) * 100)
        : 0;
    progressBarInner.style.width = pct + "%";

    if (state.status === "running") {
        progressBlock.hidden = false;
        startBtn.disabled = true;
    }

    if (state.status === "done" || state.status === "error") {
        clearInterval(pollTimer);
        pollTimer = null;
        startBtn.disabled = false;
    }

    return state;
}

startBtn.addEventListener("click", async () => {
    startBtn.disabled = true;
    progressBlock.hidden = false;

    const resp = await fetch("/api/download/start", { method: "POST" });
    const data = await resp.json();

    if (!data.started) {
        statusMessageEl.textContent = "Скачивание уже выполняется";
    }

    if (!pollTimer) {
        pollTimer = setInterval(pollStatus, 1000);
    }
});

// На случай, если процесс уже был запущен ранее (например, обновили страницу)
pollStatus().then((state) => {
    if (state.status === "running" && !pollTimer) {
        pollTimer = setInterval(pollStatus, 1000);
    }
});
