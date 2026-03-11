const form = document.getElementById("scoreForm");
const statusText = document.getElementById("statusText");
const btnScore = document.getElementById("btnScore");

const resultCard = document.getElementById("resultCard");
const fitScoreEl = document.getElementById("fitScore");
const scoreBreakdownEl = document.getElementById("scoreBreakdown");

const missingMustEl = document.getElementById("missingMust");
const missingNiceEl = document.getElementById("missingNice");
const learnSuggestionsEl = document.getElementById("learnSuggestions");
const cvImprovementsEl = document.getElementById("cvImprovements");

const btnDownloadDocx = document.getElementById("btnDownloadDocx");
const btnShowRaw = document.getElementById("btnShowRaw");
const rawJsonEl = document.getElementById("rawJson");

let lastResult = null;

function setStatus(text) {
    statusText.textContent = text;
}

function setList(ul, items, mapper = (x) => String(x)) {
    ul.innerHTML = "";
    (items || []).forEach(item => {
        const li = document.createElement("li");
        li.textContent = mapper(item);
        ul.appendChild(li);
    });
}

async function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

async function uploadCV(file) {
    const fd = new FormData();
    fd.append("file", file);

    const res = await fetch("/v1/cv/upload", { method: "POST", body: fd });
    if (!res.ok) throw new Error("Upload failed");
    return res.json(); // {cv_file_id}
}

async function createJob(cv_file_id, jd_text) {
    const res = await fetch("/v1/jobs/create-score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cv_file_id, jd_text, options: { output_formats: ["json", "docx"] } })
    });
    if (!res.ok) {
        const t = await res.text();
        throw new Error("Create job failed: " + t);
    }
    return res.json(); // {job_id}
}

async function getJob(job_id) {
    const res = await fetch(`/v1/jobs/${job_id}`);
    if (!res.ok) throw new Error("Job status failed");
    return res.json();
}

async function getResult(job_id) {
    const res = await fetch(`/v1/jobs/${job_id}/result`);
    if (!res.ok) throw new Error("Result not ready");
    return res.json(); // {job_id, result}
}

function renderResult(result) {
    lastResult = result;
    resultCard.classList.remove("d-none");

    const scores = result.scores || {};
    fitScoreEl.textContent = scores.fit_score ?? "-";
    scoreBreakdownEl.textContent = JSON.stringify(scores, null, 2);

    const gap = result.skill_gap || {};
    setList(missingMustEl, gap.missing_must_have || []);
    setList(missingNiceEl, gap.missing_nice_to_have || []);
    setList(
        learnSuggestionsEl,
        gap.learn_suggestions || [],
        (x) => `${x.skill}: ${x.reason} (${x.resources_level}, ~${x.time_estimate_weeks || "?"} weeks)`
    );

    setList(
        cvImprovementsEl,
        result.cv_improvements || [],
        (x) => `${x.issue} → ${x.fix}`
    );

    rawJsonEl.textContent = JSON.stringify(result, null, 2);

    btnDownloadDocx.classList.remove("d-none");
    btnDownloadDocx.href = `/v1/jobs/${result.job_id}/report/download`;
}

btnShowRaw.addEventListener("click", () => {
    rawJsonEl.classList.toggle("d-none");
});

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const file = document.getElementById("cvFile").files[0];
    const jdText = document.getElementById("jdText").value;

    if (!file || !jdText) return;

    btnScore.disabled = true;
    resultCard.classList.add("d-none");
    setStatus("Uploading CV...");

    try {
        const up = await uploadCV(file);
        setStatus("Creating job...");
        const job = await createJob(up.cv_file_id, jdText);

        setStatus("Running job...");
        for (let i = 0; i < 90; i++) {
            const st = await getJob(job.job_id);
            setStatus(`Status: ${st.status} (${st.progress}%)`);
            if (st.status === "failed") throw new Error(st.error_message || "Job failed");
            if (st.status === "succeeded") break;
            await sleep(1000);
        }

        setStatus("Fetching result...");
        const out = await getResult(job.job_id);
        renderResult(out.result);
        setStatus("Done.");
    } catch (err) {
        console.error(err);
        setStatus("Error: " + err.message);
    } finally {
        btnScore.disabled = false;
    }
});