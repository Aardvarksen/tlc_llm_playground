# Interaction Loops - AI Collaboration Patterns

This documents the various loops/workflows for working with Claude on projects. Understanding these patterns helps you get back into flow faster.

---

## 1. [Your Name] ↔ Claude Collaboration Loop

**The Basic Pattern**:
```
1. [Your Name]: Arrives with goal or question (stream-of-consciousness thinking)
2. Claude: Responds with "NEXT STEP" + one small lesson + action
3. [Your Name]: Executes action, reports back with blow-by-blow thoughts
4. Claude: Calibrates understanding based on response
5. → Repeat until goal achieved
```

**Key Principles**:
- **Warm glow zone**: Not too broad (lost), not too narrow (cold), just right (engaged)
- **Call out rabbit holes**: Either of you can detect them forming
- **Calibrate constantly**: [Your Name]'s stream-of-consciousness helps Claude match their mental model
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
4. Implement: Claude writes code OR [Your Name] tries + Claude reviews
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
1. [Your Name] says something that sounds knowledgeable
2. Claude evaluates: Does they know the mechanics or just the concept?
3. If uncertain → Claude includes practical explanation anyway
4. [Your Name] responds with "wait, I didn't actually know X"
5. Claude updates mental model + CLAUDE.md if significant
6. → Better calibrated for next interaction
```

**Critical Insight**: [Your Name] is articulate and can sound knowledgeable about things they don't fully understand yet. **Assume less knowledge than it seems.**

**When to Use**: Continuously, especially when discussing new topics

---

## 5. Application-Specific Data Flow Loops

[Fill this in with your project's specific data flow patterns]

**Example Template**:
```
User action
  ↓
[Component A]
  ↓
[Component B]
  ↓
[Processing]
  ↓
Result displayed
  ↓
→ Ready for next action
```

**When to Reference**: When working on [specific components], to remember how data flows

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
Report: Explain to [Your Name]
```

### Explain & Teach
```
[Your Name] asks question or seems uncertain
  ↓
Claude explains with "One Small Lesson" format
  ↓
Provides practical example/code
  ↓
[Your Name] tries it or asks follow-up
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
## CURRENT STATE (Last Updated: YYYY-MM-DD)

**Last Completed**: [Specific accomplishment with context]
**Next Action**: [Specific, actionable next step - not vague]
**Current Phase**: [Phase name/number] - [Brief status]
**Blockers**: [None, or specific decisions/questions needed]
```

**Good vs. Bad State Summaries**:

✅ **Good** (specific, actionable):
- "Created X feature with Y functionality - tested and working"
- "Fix the Z issue at file.py:123 - needs A, B, C fields"
- "Decide: Should we use approach A or B for feature X?"

❌ **Bad** (vague, unhelpful):
- "Work on Phase 1" (which part?)
- "Fix the bug" (what bug? where?)
- "Continue where we left off" (where was that?)

**When to Update CURRENT STATE**:

**Trigger 1 - Natural Session End (Inferred)**:
Claude detects session-ending phrases from [Your Name]:
- "I'm off for the day" / "gotta go" / "done for now"
- "I'll pick this up tomorrow" / "that's enough for today"
- "Thanks, I'm good" / "I'm signing off"
- Any goodbye phrasing

**Trigger 2 - Major Milestones (Proactive)**:
Claude offers to update when completing significant chunks:
- "We just finished Phase X. Let me update CURRENT STATE before we move on."
- Helps train you on documentation patterns
- Creates natural "work cycle" boundaries

**Trigger 3 - Explicit Request**:
You can request directly:
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
- Tomorrow-[Your Name] may have forgotten specifics
- Clear state = faster re-entry = less time lost to "where were we?"

**When to Use**: Every single session - at start and end

---

## 9. "Test Your Understanding" Learning Loop

**The Pattern**:
```
Complete a feature/component
  ↓
Generate 8-10 questions about the working code
  ↓
Answer from memory (mark: ✅🟡❌)
  ↓
Review together, focus on 🟡 and ❌
  ↓
Code walkthrough for fuzzy areas
  ↓
Update CLAUDE.md with understanding status
  ↓
→ Ready to extend with confidence
```

**Why this works**:
- Active recall > passive reading
- Surfaces gaps between "seen it" and "understand it"
- Prevents building on shaky foundations
- Small doses (8-10 questions) prevent cognitive overload

**When to Use**:
- Before adding new features to working code
- After implementing complex concepts
- When you "kinda understand" something
- As part of "refactor for understanding" sessions

**See CLAUDE.md for full details on this pattern**

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
**When teaching future-you**: Update with lessons learned

This file grows as you discover what works.

---

*Last updated: [DATE]*
*Add new loops as you discover them in your work.*
