from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from extract import Requirements
from score import FitAnalysis


class OutreachDraft(BaseModel):
    subject: str
    message: str = Field(description="120-150 words, confident, specific, no generic filler")


DRAFT_PROMPT = """Write a short, tailored outreach message from a job candidate to a hiring manager for the role below.

Rules:
- Only reference skills or projects from MATCHED SKILLS below. Never mention a skill that isn't listed, and never mention gaps or missing requirements.
- Open with something specific to the role or company, not "I am excited to apply."
- Reference 1-2 concrete matched projects with real detail, not just a skill name.
- 120-150 words. Confident, direct, no filler.
- End with a clear, low-pressure call to action.

ROLE: {title} at {company}
MATCHED SKILLS: {matched}
CANDIDATE DIFFERENTIATOR: {differentiator}
CANDIDATE PROJECTS: {projects}
"""

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.4)
drafter = llm.with_structured_output(OutreachDraft)


def draft_outreach(requirements: Requirements, analysis: FitAnalysis, profile: dict) -> OutreachDraft:
    matched = [m.requirement for m in analysis.skill_matches if m.status == "matched"]
    prompt = DRAFT_PROMPT.format(
        title=requirements.title,
        company=requirements.company,
        matched=matched,
        differentiator=profile.get("differentiator", ""),
        projects=profile.get("projects", []),
    )
    return drafter.invoke(prompt)