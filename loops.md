# Interaction Loops - TLC LLM Playground

This documents the various loops/workflows in this project. Understanding these patterns helps you get back into flow faster.

---

## 1. Darrin ↔ Claude Collaboration Loop

**The Basic Pattern**:
```
1. Darrin: Arrives with goal or question (stream-of-consciousness thinking)
2. Claude: Responds with "NEXT STEP" + one small lesson + action
3. Darrin: Executes action, reports back with blow-by-blow thoughts
4. Claude: Calibrates understanding based on response
5. → Repeat until goal achieved
```

**Key Principles**:
- **Warm glow zone**: Not too broad (lost), not too narrow (cold), just right (engaged)
- **Call out rabbit holes**: Either of you can detect them forming
- **Calibrate constantly**: Darrin's stream-of-consciousness helps Claude match his mental model
- **Focus keeper role**: Claude gently redirects to current goal when needed

**When to Use**: Every building session, every question, every debugging session

---

## 2. Focus Management Loop (Fighting ADHD Drift)

**The Pattern**:
```
1. Working on current goal (from plan.md)
2. ⚠️ New idea emerges (could be rabbit hole)
3. Claude asks: "Does this serve [current goal]?"
4. Decide together:
   - Continue current goal, or
   - Pivot to new idea (update plan.md), or
   - Capture idea for later (add to "Future Considerations")
5. → Return to focused work
```

**Warning Signs of Rabbit Holes**:
- Exploring a concept not needed for current phase
- Deep-diving into optimization before basics work
- Adding features outside MVP scope
- Researching alternatives after deciding on an approach

**When to Use**: Whenever a shiny new idea appears during focused work

---

## 3. Building Session Loop

**The Pattern**:
```
1. Start: Review plan.md - where are we?
2. Pick: Choose next task from current phase
3. Discuss: What approach? Any decisions needed?
4. Implement: Claude writes code OR Darrin tries + Claude reviews
5. Test: Run it, see what happens
6. Update: Mark task complete in plan.md, update CLAUDE.md if needed
7. → Next task or break
```

**Collaboration Approaches** (pick based on learning goals):
- **"I'll do it"**: Fast, less learning - use when you understand the pattern
- **"Let's discover together"**: Balanced - good default
- **"You try, I review"**: Slow, max learning - use for key concepts
- **"I show, you modify"**: Mixed - good for learning patterns

**When to Use**: Every actual coding/building session

---

## 4. Knowledge Calibration Loop

**The Pattern**:
```
1. Darrin says something that sounds knowledgeable
2. Claude evaluates: Does he know the mechanics or just the concept?
3. If uncertain → Claude includes practical explanation anyway
4. Darrin responds with "wait, I didn't actually know X"
5. Claude updates mental model + CLAUDE.md if significant
6. → Better calibrated for next interaction
```

**Critical Insight**: Darrin is articulate and can sound knowledgeable about things he doesn't fully understand yet. **Assume less knowledge than it seems.**

**When to Use**: Continuously, especially when discussing new topics

---

## 5. Application Data Flow Loops

### Current: Streamlit Direct Connection
```
User types message
  ↓
Streamlit app (session state)
  ↓
Build messages array (system + context + history)
  ↓
OpenAI client → LM Studio API
  ↓
Stream response back
  ↓
Display in UI + save to session state
  ↓
→ Ready for next message
```

### Planned: Queue Server Flow
```
User submits request
  ↓
Streamlit → FastAPI /queue/add endpoint
  ↓
Request added to queue → Get request_id
  ↓
Streamlit → /stream/{request_id} (SSE connection)
  ↓
Wait while queue position > 0
  ↓
Queue worker picks up request
  ↓
Worker → LM Studio API (streaming)
  ↓
Stream chunks → SSE → Streamlit
  ↓
Display response in real-time
  ↓
→ Ready for next request
```

**When to Reference**: When working on either the Streamlit app or queue server, to remember how data flows

---

## 6. Claude Code Capabilities Loops

### File Operations
```
Need to change code
  ↓
Read file first (always required before editing)
  ↓
Edit specific sections (exact string matching)
  OR
  Write new file (if it doesn't exist)
  ↓
Verify changes worked
```

### Planning & Tracking
```
Multi-step task begins
  ↓
TodoWrite: Create task list
  ↓
Mark task as "in_progress" before starting
  ↓
Complete task
  ↓
TodoWrite: Mark as "completed" immediately
  ↓
→ Next task (only ONE in_progress at a time)
```

### Research & Understanding
```
Need to understand codebase
  ↓
Glob: Find files matching pattern
  ↓
Grep: Search for keywords/patterns
  ↓
Read: Read relevant files
  ↓
Analyze: Understand what it does
  ↓
Report: Explain to Darrin
```

### Explain & Teach
```
Darrin asks question or seems uncertain
  ↓
Claude explains with "One Small Lesson" format
  ↓
Provides practical example/code
  ↓
Darrin tries it or asks follow-up
  ↓
Claude adjusts explanation based on response
  ↓
Update CLAUDE.md if calibration changes
```

**When to Reference**: When you want to know "how should I ask Claude to help with X?"

---

## 7. Re-Entry Loop (Coming Back After Time Away)

**The Pattern**:
```
Haven't worked on this in days/weeks
  ↓
Read README.md (quick orientation)
  ↓
Read CLAUDE.md (collaboration context)
  ↓
Check plan.md (where did we leave off?)
  ↓
Read this file (loops.md) to remember patterns
  ↓
Open Claude Code session
  ↓
Say: "I'm back! Read CLAUDE.md and plan.md for context. Where were we?"
  ↓
Claude summarizes current state + next step
  ↓
→ Back in flow
```

**Critical Files for Re-Entry**:
1. README.md - Quick orientation
2. CLAUDE.md - How we work together
3. plan.md - Where we are in the build
4. loops.md - This file (patterns and workflows)

**When to Use**: Every time you return to the project after a break

---

## 8. Session State Tracking Loop (Multi-Day Continuity)

**The Pattern**:
```
Session Start
  ↓
Claude reads CURRENT STATE section in plan.md
  ↓
Gives re-entry briefing: where we are + next action
  ↓
Work on tasks (using TodoWrite for tracking)
  ↓
Complete discrete chunks → update plan.md checkboxes
  ↓
Session ending
  ↓
Claude updates CURRENT STATE section:
  - Last completed: [what was just finished]
  - Next action: [specific, actionable next step]
  - Blockers: [any decisions/questions pending]
  - Date: [YYYY-MM-DD]
  ↓
→ Tomorrow-Claude has clear starting point
```

**What Goes in CURRENT STATE**:
```markdown
## CURRENT STATE (Last Updated: 2025-10-28)

**Last Completed**: Created state tracking loop documentation (CLAUDE.md + loops.md)
**Next Action**: Create requirements.txt with dependencies: streamlit, fastapi, uvicorn, httpx, openai, python-multipart
**Current Phase**: Phase 1 (Foundation & Cleanup) - Task 1.1 pending
**Blockers**: None
```

**Good vs. Bad State Summaries**:

✅ **Good** (specific, actionable):
- "Create requirements.txt with these 5 dependencies: streamlit, fastapi..."
- "Fix the JSON placeholder at queue_server.py:79 - needs model, messages, stream fields"
- "Decide: Should queue use async background task or separate worker process?"

❌ **Bad** (vague, unhelpful):
- "Work on Phase 1" (which part?)
- "Fix the queue server" (fix what specifically?)
- "Continue where we left off" (where was that?)

**When to Update CURRENT STATE**:

**Trigger 1 - Natural Session End (Inferred)**:
Claude detects session-ending phrases from Darrin:
- "I'm off for the day" / "gotta go" / "done for now"
- "I'll pick this up tomorrow" / "that's enough for today"
- "Thanks, I'm good" / "I'm signing off"
- Any goodbye phrasing

**Trigger 2 - Major Milestones (Proactive)**:
Claude offers to update when completing significant chunks:
- "We just finished Phase 1.1. Let me update CURRENT STATE before we move on."
- Helps train Darrin on documentation patterns
- Creates natural "work cycle" boundaries

**Trigger 3 - Explicit Request**:
Darrin can request directly:
- "Update current state" / "update plan.md"
- Useful as backup if Claude misses a cue

**Fallback for Abrupt Endings**:
If session ends unexpectedly (connection drop, window closed):
- Tomorrow-Claude won't have latest update
- Collaborative "where were we?" exploration needed
- Claude checks: git status, recent file edits, plan.md checkboxes
- Together reconstruct what was completed

**Other Updates During Session**:
- **TodoWrite**: For immediate task tracking (ephemeral, within session)
- **plan.md checkboxes**: When discrete tasks complete (permanent)
- **CURRENT STATE**: At triggers above (for re-entry)

**Why This Matters**:
- Multi-day projects lose context fast
- Tomorrow-Claude is a fresh instance with no memory
- Tomorrow-Darrin may have forgotten specifics
- Clear state = faster re-entry = less time lost to "where were we?"

**When to Use**: Every single session - at start and end

---

## Meta-Loop: Learning to Work with AI

**The Overarching Pattern**:
```
Build feature X
  ↓
Notice how Claude helps (planning? coding? reviewing? explaining?)
  ↓
Reflect: "What collaboration pattern worked well here?"
  ↓
Document in CLAUDE.md or this file
  ↓
Next time: Use that pattern intentionally
  ↓
→ Gradually build intuition for AI-augmented development
```

**This is the REAL goal**: Not just building this app, but learning how to work with AI assistants as a core professional skill.

---

## Using This File

**When starting a session**: Skim this to remember the patterns
**When stuck**: Check if you're in one of these loops and where
**When discovering new patterns**: Add them here
**When teaching future-Darrin**: Update with lessons learned

This file grows as you discover what works.

---

*Last updated: 2025-10-27*
*Add new loops as you discover them in your work.*
