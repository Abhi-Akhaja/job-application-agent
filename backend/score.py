import json
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from extract import Requirements, extract


class SkillMatch(BaseModel):
    requirement: str = Field(description="the required skill, verbatim from the posting")
    category: str = Field(description="one of: technical, soft. 'technical' = a specific tool/language/framework/system. 'soft' = a trait, mindset, or general ability like communication, problem-solving, debugging, logical thinking")
    status: str = Field(description="one of: matched, partial, missing")
    evidence: str = Field(description="what in the candidate's profile supports this, or empty string if missing")

class FitAnalysis(BaseModel):
    skill_matches: list[SkillMatch]
    nice_to_have_matches: list[str] = Field(description="nice-to-have skills the candidate does have, if any")
    overall_reasoning: str = Field(description="2-3 sentences on the overall fit, referencing the real matches and real gaps")


WEIGHTS = {"matched": 1.0, "partial": 0.5, "missing": 0.0}


SCORE_PROMPT = """You are assessing how well a candidate fits a job posting's REQUIRED (must-have) skills.
 
For EACH item in must_have_skills below:
1. Tag it as "technical" (a specific tool, language, framework, or system) or "soft" (a trait or general ability like communication, problem-solving, logical thinking, culture fit)
2. Classify it against the candidate profile as:
   - "matched": the candidate has clear, direct evidence of this
   - "partial": related or adjacent experience, but not a direct match
   - "missing": no evidence in the profile
 
Do not be generous. If the profile doesn't support it, say "missing" — an honest gap analysis is the whole point.
Separately, note any nice_to_have_skills the candidate happens to have.
 
MUST-HAVE SKILLS:
{must_have}
 
NICE-TO-HAVE SKILLS:
{nice_to_have}
 
CANDIDATE PROFILE:
{profile}
"""

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)
scorer = llm.with_structured_output(FitAnalysis)


def score_fit(requirements: Requirements, profile: dict) -> tuple[FitAnalysis, int]:
    prompt = SCORE_PROMPT.format(
        must_have=json.dumps(requirements.must_have_skills, indent=2),
        nice_to_have=json.dumps(requirements.nice_to_have_skills, indent=2),
        profile=json.dumps(profile, indent=2),
    )
    analysis = scorer.invoke(prompt)
 
    technical = [m for m in analysis.skill_matches if m.category == "technical"]
    scoring_set = technical if technical else analysis.skill_matches  # fall back if a posting is all soft skills
 
    if not scoring_set:
        fit_score = 0
    else:
        total = sum(WEIGHTS[m.status] for m in scoring_set)
        fit_score = round(100 * total / len(scoring_set))
 
    return analysis, fit_score


if __name__ == "__main__":
    with open("profile.json") as f:
        profile = json.load(f)
 
    jd = open("sample_jd.txt").read()
    requirements = extract(jd)
 
    analysis, fit_score = score_fit(requirements, profile)
 
    print(f"FIT SCORE: {fit_score}  (technical requirements only)\n")
    for m in analysis.skill_matches:
        tag = "TECH" if m.category == "technical" else "soft"
        print(f"[{m.status.upper():8}] ({tag}) {m.requirement}")
        if m.evidence:
            print(f"           evidence: {m.evidence}")
    if analysis.nice_to_have_matches:
        print(f"\nNice-to-have matches: {analysis.nice_to_have_matches}")
    print(f"\nReasoning: {analysis.overall_reasoning}")
 