# TLC LLM Playground

> **🚀 RETURNING TO THIS PROJECT? START HERE:**
> Open Claude Code and say:
> **"I'm back working on tlc_llm_playground. Read CLAUDE.md and plan.md for full context, then tell me: where were we and what's our current spotlight?"**
>
> Then come back and read the rest of this README.

---

**Welcome back, Darrin.** This is your re-entry guide.

## What This Is

A learning playground for working with local LLMs (via LM Studio) with request queue management. But more importantly: this is where you're learning to be an AI-augmented developer.

**Three Goals** (in order of importance):
1. **Learn to work with AI assistants effectively** (meta-skill for career)
2. **Understand every loop and thread deeply** (not just "it works")
3. **Build a working queue system for multi-user LLM access** (the actual app)

## Getting Back Into Flow

### Quick Re-Entry (5 minutes)
1. **Read `CLAUDE.md`** - Your collaboration contract with Claude
2. **Check `plan.md`** - Where are we in the MVP roadmap?
3. **Read `loops.md`** - Remind yourself of the interaction patterns
4. **Open a Claude Code session** and say: "I'm back! Where were we?"

### Cold Start (haven't touched this in weeks)
1. Read this whole README
2. Read CLAUDE.md thoroughly
3. Review plan.md to see completed vs pending phases
4. Run the app (see below) to remember what it does
5. Check git log to see what changed since you were last here

## How to Run This Thing

> **Note**: These instructions are for Windows PowerShell. If you're on macOS/Linux, use `source venv/bin/activate` instead of the activation command below.
>
> **Requirements**: Python 3.9+ (currently using 3.13.9)

### First Time Setup
```powershell
# 1. Make sure you're in the project directory
cd C:\AppDev\tlc_llm_playground

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1
# If you get an execution policy error, run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. Install dependencies (if you haven't already)
pip install -r requirements.txt

# 4. Copy environment template and customize if needed (when .env.example exists)
# copy .env.example .env
# Edit .env if your LM Studio URL is different
```

### Running the Streamlit App
```powershell
# Make sure venv is activated first (you'll see (venv) in your prompt)
streamlit run original_streamlit.py
```

Opens in browser at http://localhost:8501

### Running the Queue Server (when it's finished)
```powershell
uvicorn queue_server:app --reload
```

API docs at http://localhost:8000/docs

## Your Working Style (Remind Yourself)

**You have ADHD.** You generate a million ideas a minute. This is a strength (curiosity, enthusiasm) and a risk (rabbit holes).

**Claude's job**: Keep you focused on the end goal. Gentle nudging back to the plan when needed.

**Your job**:
- Call out rabbit holes when you feel them forming
- Stream-of-consciousness responses help Claude calibrate
- Ask for the "warm glow" if responses are too laser-focused or too broad

**When you catch yourself sounding knowledgeable about something you don't fully understand**: CALL IT OUT. Your ability to sound smart can make LLMs overestimate your knowledge.

## Project Structure

```
tlc_llm_playground/
├── README.md              ← You are here
├── CLAUDE.md              ← Claude's instruction manual (read this with Claude)
├── plan.md                ← MVP roadmap, track progress here
├── loops.md               ← Interaction patterns and workflows
├── config.py              ← ALL settings in one place
├── .env.example           ← Template for local config
├── .env                   ← Your actual config (not in git)
├── requirements.txt       ← Python dependencies
├── original_streamlit.py  ← Current Streamlit frontend
├── queue_server.py        ← FastAPI queue server (WIP)
└── venv/                  ← Virtual environment
```

## Key Files to Know

- **CLAUDE.md**: How to work with Claude on this project
- **plan.md**: Where you are in the build, what's next
- **loops.md**: Interaction patterns and workflows
- **config.py**: All settings - modify here, not scattered across files

## What You're Learning

**Technical Skills**:
- Python async programming (FastAPI, background tasks)
- Streamlit for rapid UI development
- OpenAI-compatible API integration
- Queue-based request management
- Project organization and configuration management

**Meta-Skills**:
- How to structure problems for AI assistance
- When to use AI vs. do it yourself
- How to review/understand/modify AI-generated code
- Collaboration patterns with AI assistants
- Building career-critical skills for the AI-augmented future

## Getting Help

**From Claude**:
1. Open Claude Code
2. Start with: "I'm working on tlc_llm_playground. Read CLAUDE.md and plan.md to get context."
3. Ask your question or describe what you want to build

**From Documentation**:
- Streamlit: https://docs.streamlit.io/
- FastAPI: https://fastapi.tiangolo.com/
- LM Studio: https://lmstudio.ai/

## Remember

This project is your vehicle for learning AI-augmented development. The app is the "what", understanding every detail is the "how", but **learning to work effectively with AI is the "why"**.

The subscription stays active because you're building the future. Keep going.

---

*Last updated: 2025-10-28*
*When you make significant progress, update this file.*
