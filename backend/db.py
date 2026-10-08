import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Neon gives this connection string from its dashboard
DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                company TEXT,
                title TEXT,
                location TEXT,
                fit_score INTEGER,
                status TEXT,
                job_description TEXT,
                requirements_json TEXT,
                analysis_json TEXT,
                outreach_json TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
    conn.commit()
    conn.close()


def save_job(result: dict) -> int:
    conn = get_conn()
    req = result["requirements"]
    outreach = result.get("outreach")
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO jobs
               (company, title, location, fit_score, status, job_description,
                requirements_json, analysis_json, outreach_json)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (
                req.company,
                req.title,
                req.location,
                result["fit_score"],
                result["status"],
                result["job_description"],
                req.model_dump_json(),
                result["analysis"].model_dump_json(),
                outreach.model_dump_json() if outreach else None,
            ),
        )
        job_id = cur.fetchone()["id"]
    conn.commit()
    conn.close()
    return job_id


def list_jobs() -> list[dict]:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM jobs ORDER BY fit_score DESC")
        rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


'''  
With SQLite

import sqlite3
import os

# Locally this defaults to a file in the project folder. If plan to Host, set DB_PATH to a path inside a mounted volume (e.g. /data/jobs.db) so the database survives redeploys instead of living on the container's throwaway disk.
DB_PATH = os.getenv("DB_PATH", "jobs.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            title TEXT,
            location TEXT,
            fit_score INTEGER,
            status TEXT,
            job_description TEXT,
            requirements_json TEXT,
            analysis_json TEXT,
            outreach_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_job(result: dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    req = result["requirements"]
    outreach = result.get("outreach")  
    cur = conn.execute(
        """INSERT INTO jobs
           (company, title, location, fit_score, status, job_description,
            requirements_json, analysis_json, outreach_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            req.company,
            req.title,
            req.location,
            result["fit_score"],
            result["status"],
            result["job_description"],
            req.model_dump_json(),
            result["analysis"].model_dump_json(),
            outreach.model_dump_json() if outreach else None,
        ),
    )
    conn.commit()
    job_id = cur.lastrowid
    conn.close()
    return job_id


def list_jobs() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row      # Access by row["company"]
    rows = conn.execute("SELECT * FROM jobs ORDER BY fit_score DESC").fetchall()      # [Row(job 1),Row(job 2),Row(job 3)]
    conn.close()
    return [dict(r) for r in rows]

'''

'''
rows = [
    Row(id=2, company="Google", title="Backend Developer", fit_score=95),
    Row(id=3, company="XYZ", title="Full Stack Developer", fit_score=82),
]
'''

# import json

# rows = [
#     {
#         "id": 3,
#         "company": "Google",
#         "requirements_json": '{"company": "Google", "title": "Python Developer"}',
#         "analysis_json": '{"score": 92, "reason": "Good Python experience"}',
#         "outreach_json": '{"message": "Hello Google"}'
#     },
    
#     {
#         "id": 1,
#         "company": "Microsoft",
#         "requirements_json": '{"company": "Microsoft", "title": "Backend Developer"}',
#         "analysis_json": '{"score": 85, "reason": "Good backend experience"}',
#         "outreach_json": '{"message": "Hello Microsoft"}'
#     },
    
#     {
#         "id": 2,
#         "company": "TCS",
#         "requirements_json": '{"company": "TCS", "title": "Python Developer"}',
#         "analysis_json": '{"score": 72, "reason": "Some relevant experience"}',
#         "outreach_json": None
#     }
# ]

# for r in rows:
#     r["requirements"] = json.loads(r["requirements_json"])
#     r["analysis"] = json.loads(r["analysis_json"])
#     r["outreach"] = json.loads(r["outreach_json"]) if r["outreach_json"] else None
#     del r["requirements_json"], r["analysis_json"], r["outreach_json"]
# print(rows)

# Result of print(r)
# {'id': 3, 'company': 'Google', 'requirements': {'company': 'Google', 'title': 'Python Developer'}, 'analysis': {'score': 92, 'reason': 'Good Python experience'}, 'outreach': {'message': 'Hello Google'}}
# {'id': 1, 'company': 'Microsoft', 'requirements': {'company': 'Microsoft', 'title': 'Backend Developer'}, 'analysis': {'score': 85, 'reason': 'Good backend experience'}, 'outreach': {'message': 'Hello Microsoft'}}
# {'id': 2, 'company': 'TCS', 'requirements': {'company': 'TCS', 'title': 'Python Developer'}, 'analysis': {'score': 72, 'reason': 'Some relevant experience'}, 'outreach': None}


