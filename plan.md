# TLC LLM Playground - MVP Plan

## Vision
Create a robust, multi-user LLM playground that manages requests through a queue system, supports multiple models, and provides real-time streaming responses. This project serves as both a functional tool and a learning platform for understanding LLM integration, async processing, and web application architecture.

## Core Value Proposition
- **Queue Management**: Handle multiple concurrent users without overwhelming the LLM backend
- **Model Flexibility**: Easy switching between different models with appropriate defaults
- **Real-time Feedback**: Streaming responses for better UX
- **Learning Platform**: Clear, understandable code that teaches concepts as it implements them

---

## MVP Components

### Phase 1: Foundation & Cleanup
**Goal**: Establish a solid foundation with proper dependency management and configuration

#### 1.1 Dependency Management
- [ ] Create `requirements.txt` with all dependencies:
  - streamlit
  - fastapi
  - uvicorn
  - httpx
  - openai
  - python-multipart (for FastAPI form handling)
- [ ] Document Python version requirement
- [ ] Add installation instructions to README

#### 1.2 Configuration Management
- [ ] Create `config.py` for centralized settings:
  - LM Studio URL (currently hard-coded in two places)
  - Available models and their defaults
  - Queue settings (max size, timeout values)
  - Port configurations for FastAPI server
- [ ] Use environment variables for environment-specific settings
- [ ] Create `.env.example` file as template

#### 1.3 Documentation
- [ ] Create `README.md` with:
  - Project description
  - Setup instructions
  - How to run the application
  - Architecture overview
- [x] `CLAUDE.md` for AI assistant context (completed)
- [x] `plan.md` (this file)

**Estimated Complexity**: Low
**Learning Focus**: Python project structure, configuration management, environment variables

---

### Phase 2: Complete the Queue Server
**Goal**: Finish the FastAPI queue server implementation

#### 2.1 Complete Request Processing
- [ ] Fix the incomplete JSON payload at `queue_server.py:79`
- [ ] Implement proper message construction for LM Studio
- [ ] Add request validation and error handling
- [ ] Test streaming endpoint independently

#### 2.2 Implement Queue Worker
- [ ] Create background worker to process queue
- [ ] Add worker lifecycle management (start/stop)
- [ ] Implement proper async handling
- [ ] Add logging for queue operations

**Current Code Issue** (queue_server.py:79):
```python
# Currently has placeholder
json={...},

# Needs to be:
json={
    "model": request_data["model"],
    "messages": [{"role": "user", "content": request_data["prompt"]}],
    "stream": True
}
```

#### 2.3 Enhanced Queue Features
- [ ] Request timeout handling
- [ ] Queue priority system (optional)
- [ ] Request cancellation capability
- [ ] Queue statistics and monitoring

**Estimated Complexity**: Medium
**Learning Focus**: Async programming, FastAPI, background tasks, streaming responses, queue data structures

---

### Phase 3: Integrate Frontend with Queue Server
**Goal**: Connect Streamlit frontend to the queue server instead of directly to LM Studio

#### 3.1 Update Streamlit to Use Queue API
- [ ] Replace direct OpenAI client calls with queue API calls
- [ ] Submit requests to `/queue/add` endpoint
- [ ] Poll or stream from `/stream/{request_id}` endpoint
- [ ] Update UI to show queue position and status

#### 3.2 Enhanced User Feedback
- [ ] Show "Position in queue: X" message
- [ ] Display "Your request is being processed..." when active
- [ ] Handle timeout scenarios gracefully
- [ ] Add ability to see queue status

#### 3.3 Multi-User Support
- [ ] Generate unique user identifiers
- [ ] Track user sessions
- [ ] Show per-user request history
- [ ] Add user-specific rate limiting (optional)

**Estimated Complexity**: Medium
**Learning Focus**: REST API integration, async Streamlit patterns, state management across services

---

### Phase 4: Code Organization & Refactoring
**Goal**: Organize code into maintainable, understandable modules

#### 4.1 Create Modular Structure
```
src/
├── __init__.py
├── frontend/
│   ├── __init__.py
│   ├── app.py              # Main Streamlit app
│   ├── ui_components.py    # Reusable UI elements
│   └── session_manager.py  # Session state management
├── backend/
│   ├── __init__.py
│   ├── server.py           # FastAPI app
│   ├── queue_manager.py    # Queue logic
│   ├── llm_client.py       # LM Studio interaction
│   └── models.py           # Pydantic models for requests/responses
├── utils/
│   ├── __init__.py
│   └── helpers.py          # Shared utilities
└── config.py               # Configuration
```

#### 4.2 Extract Components
- [ ] Move model definitions to separate module
- [ ] Create reusable UI components (chat message, model selector)
- [ ] Extract queue logic into dedicated class
- [ ] Create LLM client wrapper with error handling

#### 4.3 Add Type Hints
- [ ] Add type hints to all functions
- [ ] Use Pydantic models for data validation
- [ ] Add docstrings explaining parameters and return values

**Estimated Complexity**: Medium
**Learning Focus**: Python modules, project organization, type systems, Pydantic

---

### Phase 5: Testing & Reliability
**Goal**: Ensure the system works reliably and handles edge cases

#### 5.1 Error Handling
- [ ] Network error handling (LM Studio down, timeout)
- [ ] Invalid input validation
- [ ] Queue overflow handling
- [ ] Model loading failure handling
- [ ] User-friendly error messages

#### 5.2 Testing
- [ ] Create `tests/` directory
- [ ] Unit tests for queue operations
- [ ] Integration tests for API endpoints
- [ ] Test streaming functionality
- [ ] Test multi-user scenarios

#### 5.3 Logging & Monitoring
- [ ] Add structured logging throughout
- [ ] Log request/response times
- [ ] Track queue metrics
- [ ] Create simple monitoring dashboard (optional)

**Estimated Complexity**: Medium
**Learning Focus**: Testing in Python, pytest, error handling patterns, logging

---

## Implementation Sequence

### Recommended Order
1. **Start with Phase 1** (Foundation) - Get the basics right
2. **Complete Phase 2** (Queue Server) - Core functionality
3. **Move to Phase 3** (Integration) - Connect the pieces
4. **Refactor with Phase 4** (Organization) - Clean up as you understand
5. **Strengthen with Phase 5** (Testing) - Make it robust

### Why This Order?
- **Foundation first**: Hard to build without proper dependencies and config
- **Backend before frontend integration**: Test queue independently
- **Refactor after understanding**: Better to understand the flow before organizing
- **Testing throughout**: Add tests as you build each phase

---

## Key Technical Decisions to Discuss

### 1. Queue Processing Model
**Options:**
- **A) Background thread**: Simple, but may have GIL limitations
- **B) Async background task**: More Pythonic for I/O-bound work
- **C) Separate worker process**: Most robust, but more complex

**Recommendation**: Start with B (async background task), move to C if needed

### 2. Frontend-Backend Communication
**Options:**
- **A) Polling**: Frontend checks status every N seconds
- **B) Server-Sent Events (SSE)**: Server pushes updates to client
- **C) WebSockets**: Full duplex communication

**Recommendation**: Start with B (SSE via StreamingResponse) - already partially implemented

### 3. Session Management
**Options:**
- **A) Simple in-memory**: Fast but lost on restart
- **B) Redis/similar**: Persistent, supports scaling
- **C) Database**: Full persistence and history

**Recommendation**: Start with A (in-memory), document path to B/C

---

## Success Criteria for MVP

### Must Have
- ✓ Queue system successfully processes requests sequentially
- ✓ Multiple users can submit requests without conflicts
- ✓ Streaming responses work through queue server
- ✓ Clear error messages when things go wrong
- ✓ Basic documentation exists and is accurate

### Should Have
- ✓ Configuration is centralized and manageable
- ✓ Code is organized into logical modules
- ✓ Basic tests exist for core functionality
- ✓ Logging helps debug issues

### Nice to Have
- ◯ Queue monitoring dashboard
- ◯ Request history and export
- ◯ Advanced queue features (priority, cancellation)
- ◯ Performance metrics

---

## Learning Outcomes

By completing this MVP, you (Darrin) will deeply understand:

1. **Async Python**: How async/await works, event loops, concurrent execution
2. **Web Frameworks**: FastAPI request handling, Streamlit state management
3. **API Design**: REST principles, request/response patterns, streaming
4. **Queue Systems**: FIFO queues, background processing, concurrency control
5. **LLM Integration**: OpenAI-compatible APIs, streaming, context management
6. **Project Structure**: How to organize a multi-component Python project
7. **Error Handling**: Graceful degradation, user-friendly errors, logging

---

## Next Steps

1. **Review this plan** - Does this align with your vision?
2. **Prioritize phases** - Want to adjust the order?
3. **Start with Phase 1.1** - Create requirements.txt together
4. **Discuss technical decisions** - Which options make sense for your learning goals?

---

## Questions for Darrin

Before we proceed, let's align on:

1. **Learning vs. Speed**: Should we take extra time to deeply explain concepts, or move faster?
2. **Scope**: Is this MVP the right size, or should we add/remove components?
3. **Technical Depth**: Want to explore alternatives (e.g., different queue implementations) or stick to one approach?
4. **Deployment**: Is running locally sufficient, or planning to deploy somewhere?

---

*Last Updated: 2025-10-27*
*Status: Ready for review and Phase 1 kickoff*
