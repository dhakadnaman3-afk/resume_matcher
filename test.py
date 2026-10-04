from app.graph import app_graph

result = app_graph.invoke({
    "resume_text": "I have experience in Python, FastAPI, and SQL. Also worked with Docker.",
    "jd_text": "Looking for a candidate skilled in Python, FastAPI, PostgreSQL, and Kubernetes."
})

print(result)