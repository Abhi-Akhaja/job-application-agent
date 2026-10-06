const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchJobs() {
    const res = await fetch(`${BASE_URL}/jobs`);
    if (!res.ok) throw new Error("Failed to load jobs");
    return res.json();
}

export async function createJob(jobDescription) {
    const res = await fetch(`${BASE_URL}/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_description: jobDescription }),
    });
    if (!res.ok) throw new Error("Failed to score job");
    return res.json();
}