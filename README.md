# Job Radar

An AI agent that scores job postings against your resume and drafts tailored outreach - built on a LangGraph pipeline with a FastAPI backend and a React dashboard.

Paste in a job description. The pipeline extracts the real requirements, scores your fit against them with an honest gap analysis, if the fit clears a threshold - drafts a short outreach message using only the skills that genuinely match. Every job lands on a dashboard, sortable by fit score.

## How it works

The core is a `StateGraph` with four stages:

```
extract → score → [conditional: fit >= 50?] → draft → end
                         |
                         └── below threshold → end (no draft written)
```

- **`extract`** - pulls structured requirements (must-have skills, nice-to-haves, seniority, responsibilities) out of the raw posting text, via Gemini with a Pydantic schema for structured output.
- **`score`** - classifies each required skill as `matched` / `partial` / `missing`, and tags each as `technical` or `soft`. The fit score is computed in plain Python from the technical classifications only - soft skills (communication, problem-solving) are shown but never counted, because an LLM can always rationalize a soft skill as "partially implied," which made early scores unreliable.
- **conditional edge** - routes to `draft` only if the score clears a threshold, skipping the cost of drafting outreach for jobs that aren't a real fit.
- **`draft`** - writes a short outreach message, constrained to reference only the skills the previous step marked as matched. It's structurally unable to claim a skill the candidate doesn't have, because unmatched skills never reach the prompt.

## Stack

- **Pipeline**: LangGraph, LangChain, Gemini API (`gemini-3.5-flash`)
- **Backend**: FastAPI, SQLite
- **Frontend**: React (Vite)

## Project structure

```
extract.py    # requirements extraction node
score.py      # fit scoring node (technical/soft split, weighted score)
draft.py      # outreach drafting node
graph.py      # wires the nodes into a LangGraph StateGraph
db.py         # SQLite storage
main.py       # FastAPI app (POST /jobs, GET /jobs)
profile.json  # candidate skills/experience profile the scorer compares against
frontend/     # React dashboard (Vite)
```

## Running locally

**Backend:**

```bash
pip install -r requirements.txt
# create a .env file with: GOOGLE_API_KEY=your_key_here
uvicorn main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Open the Vite dev URL, paste a job posting, and it'll appear on the dashboard once scored.
