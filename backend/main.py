import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph import graph
from db import init_db, save_job, list_jobs

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


class JobRequest(BaseModel):
    job_description: str


def serialize(result: dict) -> dict:         # Convert Pydantic object into python dictionary
    outreach = result.get("outreach")
    return {
        "requirements": result["requirements"].model_dump(),
        "analysis": result["analysis"].model_dump(),
        "fit_score": result["fit_score"],
        "status": result["status"],
        "outreach": outreach.model_dump() if outreach else None,
    }


@app.post("/jobs")
def create_job(payload: JobRequest):
    result = graph.invoke({"job_description": payload.job_description})
    job_id = save_job(result)
    return {"id": job_id, **serialize(result)}


# Get jobs from DB → convert JSON strings back to dictionaries → clean up the old fields → return them.
@app.get("/jobs")
def get_jobs():
    rows = list_jobs()
    for r in rows:
        r["requirements"] = json.loads(r["requirements_json"])
        r["analysis"] = json.loads(r["analysis_json"])
        r["outreach"] = json.loads(r["outreach_json"]) if r["outreach_json"] else None
        del r["requirements_json"], r["analysis_json"], r["outreach_json"]
    return rows