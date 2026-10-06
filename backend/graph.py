import json
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, START, END

from extract import Requirements, extract
from score import FitAnalysis, score_fit
from draft import OutreachDraft, draft_outreach

with open("profile.json") as f:
    PROFILE = json.load(f)


class JobState(TypedDict):
    job_description: str
    requirements: Optional[Requirements]
    analysis: Optional[FitAnalysis]
    fit_score: Optional[int]
    status: Optional[str]
    outreach: Optional[OutreachDraft]

FIT_THRESHOLD = 50  # below this, don't bother drafting


def extract_node(state: JobState) -> dict:
    return {"requirements": extract(state["job_description"])}

def score_node(state: JobState) -> dict:
    analysis, fit_score = score_fit(state["requirements"], PROFILE)
    status = "low_fit" if fit_score < FIT_THRESHOLD else "scored"
    return {"analysis": analysis, "fit_score": fit_score, "status": status}

def route_after_score(state: JobState) -> str:
    return "draft" if state["fit_score"] >= FIT_THRESHOLD else "skip"

def draft_node(state: JobState) -> dict:
    outreach = draft_outreach(state["requirements"], state["analysis"], PROFILE)
    return {"outreach": outreach, "status": "drafted"}


builder = StateGraph(JobState)
builder.add_node("extract", extract_node)
builder.add_node("score", score_node)
builder.add_node("draft", draft_node)

builder.add_edge(START, "extract")
builder.add_edge("extract", "score")
builder.add_conditional_edges("score", route_after_score, {"draft": "draft", "skip": END})
builder.add_edge("score", "draft")
builder.add_edge("draft", END)

graph = builder.compile()


if __name__ == "__main__":
    jd = open("sample_jd.txt").read()
    result = graph.invoke({"job_description": jd})

    req = result["requirements"]
    print(f"{req.title} @ {req.company}")
    print(f"FIT SCORE: {result['fit_score']}  [{result['status']}]\n")
    for m in result["analysis"].skill_matches:
        print(f"[{m.status.upper():8}] ({m.category}) {m.requirement}")

    if result["status"] == "drafted":
        print(f"\n--- {result['outreach'].subject} ---")
        print(result["outreach"].message)
    else:
        print("\nFit too low — no outreach drafted.")