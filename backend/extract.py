import json
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI


class Requirements(BaseModel):
    company: str
    title: str
    location: str
    seniority: str = Field(description="intern / junior / mid / senior / unspecified")
    must_have_skills: list[str]
    nice_to_have_skills: list[str]
    responsibilities: list[str]

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)
extractor = llm.with_structured_output(Requirements)

PROMPT = """Extract the requirements from this job posting.
Only include what the posting actually says. If something is not stated, use "unspecified" or an empty list.

POSTING:
{jd}"""

def extract(jd : str) -> Requirements:
    return extractor.invoke(PROMPT.format(jd = jd))

if __name__ == "__main__":
    jd = open("sample_jd.txt").read()
    print(json.dumps(extract(jd).model_dump(), indent=2))