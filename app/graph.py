from typing import TypedDict
from langgraph.graph import StateGraph, END
from app.agents import extract_skills, compare_skills, generate_advice

# Step 1: State define karo — ye ek "shared box" hai jisme har node apna result daalega
class MatcherState(TypedDict):
    resume_text: str
    jd_text: str
    resume_skills: list
    jd_skills: list
    matched_skills: list
    missing_skills: list
    match_percentage: float
    advice: str


# Step 2: Har node ek function hai jo state leta hai, state update karke return karta hai
def extract_node(state: MatcherState) -> MatcherState:
    state["resume_skills"] = extract_skills(state["resume_text"])
    state["jd_skills"] = extract_skills(state["jd_text"])
    return state

def compare_node(state: MatcherState) -> MatcherState:
    result = compare_skills(state["resume_skills"], state["jd_skills"])
    state["matched_skills"] = result["matched_skills"]
    state["missing_skills"] = result["missing_skills"]
    state["match_percentage"] = result["match_percentage"]
    return state

def advice_node(state: MatcherState) -> MatcherState:
    state["advice"] = generate_advice(state["missing_skills"])
    return state


# Step 3: Graph banao — nodes add karo, edges (connections) define karo
graph = StateGraph(MatcherState)

graph.add_node("extract", extract_node)
graph.add_node("compare", compare_node)
graph.add_node("advice", advice_node)

graph.set_entry_point("extract")
graph.add_edge("extract", "compare")
graph.add_edge("compare", "advice")
graph.add_edge("advice", END)

app_graph = graph.compile()