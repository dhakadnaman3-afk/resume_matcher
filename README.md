# Resume vs JD Matcher

An AI-powered tool that compares a resume with a job description, finds matched and missing skills, calculates a match percentage, and gives advice on what to improve.

Built with **LangGraph, LangChain, Groq, and FastAPI**.

## Features

- Extracts skills from both the resume and the job description using an LLM
- Compares them using set operations to find matched and missing skills
- Calculates a match percentage
- Generates personalised advice on what to learn or add to the resume
- Simple web interface plus a REST API (with auto-generated Swagger docs)

## How it works

The app uses a 3-step LangGraph pipeline:

1. **Extract Agent**: pulls skills out of the resume and the job description
2. **Compare Agent**: finds matched and missing skills and computes the match percentage
3. **Advice Agent**: suggests what to improve based on the missing skills

## Tech Stack

- Python
- FastAPI + Uvicorn
- LangChain + LangGraph
- Groq LLM (via `langchain-groq`)
- pypdf and python-docx for reading resume files

## Project Structure

```
resume_matcher/
├── app/
│   ├── main.py      # FastAPI app, /match endpoint, web UI
│   ├── graph.py     # LangGraph workflow
│   ├── agents.py    # Extract, Compare, Advice agents
│   └── extras.py    # Additional routes (file handling)
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. Clone the repository

```bash
git clone https://github.com/<your-username>/resume_matcher.git
cd resume_matcher
```

2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your Groq API key

```
GROQ_API_KEY=your_key_here
```

You can get a free key from https://console.groq.com

## Run

```bash
uvicorn app.main:app --reload
```

Then open:

- Web app: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs

## API Usage

**POST** `/match`

Request:

```json
{
  "resume_text": "Python developer with experience in FastAPI, SQL, Git...",
  "jd_text": "Required: Python, SQL, FastAPI, Docker, AWS..."
}
```

Response:

```json
{
  "matched_skills": ["Python", "SQL", "FastAPI"],
  "missing_skills": ["Docker", "AWS"],
  "match_percentage": 60,
  "advice": "Learn Docker and AWS basics and add a project using them..."
}
```

## Future Improvements

- Fuzzy skill matching using string similarity
- Support for more resume formats
- Deployment on Render

## Author

**Naman Dhakad**
GitHub: [@<your-username>](https://github.com/<your-username>)