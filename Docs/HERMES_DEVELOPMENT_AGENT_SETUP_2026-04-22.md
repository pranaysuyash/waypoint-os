# TRAVEL AGENCY APPLICATION — HERMES INTEGRATION ASSESSMENT
**Product**: travel_agency_agent (Travel Agency SaaS to Sell)  
**Development Agent**: Hermes (Your AI Coding Assistant)  
**Date**: 2026-04-22  
**Model**: nemotron-3-super (via Ollama Cloud)  
**Prepared by**: Hermes (as your development agent)  
**Status**: Final — Actionable Guidance  

## Executive Summary — Correct Perspective  
You are building a **travel agency application** to sell.  
**Hermes is your development agent** — not something to embed in your product.  

Your question should be:  
**"How should I configure/setup Hermes (my development agent) to most effectively build and maintain the travel_agency_agent application?"**  

NOT:  
"How does the travel agency app use Hermes?" (which makes no sense as a product)  

Let me provide a practical assessment and setup guide for using Hermes effectively as your development agent for this travel agency project.

---

## 🎯 GOAL: Optimize Hermes as Your Development Agent
For building/selling: **travel_agency_agent** (travel agency operating system)

### ✅ What Hermes Brings as Your Development Agent:
- **3,000+ skills** for accelerated development  
- **Multi-agent orchestration** for complex tasks  
- **Specialized tooling** (browser, terminal, web, vision, file, etc.)  
- **Memory persistence** across sessions/projects  
- **Established workflows** (debugging, testing, research, documentation)  
- **Quality gates** and verification patterns  
- **Communication & coordination** patterns  

### 🚫 What Hermes Is NOT (For Your Product):
- Not a component to embed in travel_agency_agent  
- Not an AI feature for your end users  
- Not part of your travel agency's tech stack  
- Not something your customers will interact with directly  

---

## 🔧 RECOMMENDED HERMES SETUP FOR DEVELOPMENT
Based on AGENTS.md and workspace standards, here’s how to configure Hermes for optimal travel agency development:

### 1. **Project-Specific Configuration** (Already Partially Done)  
Your `.agent/` directory shows proper project alignment:
- `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt` — Project-specific instructions  
- `Docs/context/agent-start/SESSION_CONTEXT.md` — Loaded project context  
- `Docs/context/agent-start/STEP1_ENV.sh` — Environment setup  

**Verify**: These should be auto-loaded when you `cd` into `/Users/pranay/Projects/travel_agency_agent/`

### 2. **Skills Discovery Protocol** — CRITICAL for Efficiency  
When working on travel_agency_agent tasks, Hermes **MUST** follow this order to find relevant skills:

```
1. ~/.claude/skills/*/              → User-level Claude skills (~72)
2. ~/.agents/skills/*/              → User-level agents skills (~98, incl Azure/Marketing)  
3. ~/Projects/skills/*/             → **PROJECT-LEVEL SHARED (47 curated engineering) ⭐ CHECK THIS FIRST**
4. ~/Projects/external-skills/*/    → Community imports (2,898+ skills)
5. ~/Projects/openai-skills/        → OpenAI Codex standard repo
6. $CODEX_HOME/skills/*/            → Codex runtime-installed (when set)
7. ~/.codex/skills/*/               → Codex local saved (default path)
8. ~/.codex/skills/.system/*/       → Codex app bundled/system (read-only)
```

**Never default to `.claude` or `gstack` only** — check ALL locations first.

### 3. **Priority Skills for Travel Agency Development**  
Load these first for common travel agency tasks:

| Task Type | Priority Skills to Load First | Location |
|-----------|-------------------------------|----------|
| **Debugging issues** | `systematic-debugging` | `~/Projects/skills/` |
| **Writing tested features** | `tdd-workflow`, `verification-before-completion` | `~/Projects/skills/` |  
| **Frontend/UI work** | `frontend-design`, `react-effect-discipline` | `~/Projects/skills/` |
| **Research/investigation** | `search-first`, `web_extract` | `~/Projects/skills/` |
| **API/backend work** | `api-design`, `backend-patterns`, `docker-patterns` | `~/Projects/skills/` |  
| **Testing/QA** | `qa`, `qa-only`, `browse` (headless browser) | `~/.agents/skills/` |
| **Documentation** | `doc`, `article-writing`, `copywriting` | Multiple locations — check all |
| **Performance optimization** | `performance`, `performance-profiling` | `~/Projects/skills/` |
| **Security review** | `security-review`, `security-scan` | Multiple locations |

### 4. **Development Workflow Optimization**  
Use Hermes most effectively with these patterns:

#### **A. Complex Problem Solving**  
Instead of struggling alone:
```
1. Load systematic-debugging skill
2. Spawn research subagent: delegate_task(goal="Investigate [specific issue]...", toolsets=['web','terminal','file'])  
3. Load relevant domain skills (api-design, frontend-patterns, etc.)
4. Implement solution with verified patterns
5. Run verification-before-completion before marking done
```

#### **B. Feature Development**  
Test-driven, verified approach:
```
1. Load tdd-workflow skill  
2. Load verification-before-completion skill
3. Write failing test first (terminal subagent)
4. Implement minimum code to pass (terminal subagent)  
5. Run tests, refactor, verify
6. Use verification-before-completion checklist
```

#### **C. Research & Learning**  
Efficient investigation:
```
1. Load search-first skill (research-before-coding)
2. Use web_search for initial investigation  
3. Extract relevant sources with web_extract  
4. Load domain-specific skills as needed (api-design, frontend-patterns, etc.)  
5. Synthesize findings with article-writing or copywriting skills
6. Document learnings in project docs (not just code comments)
```

#### **D. Quality Assurance**  
Systematic validation:
```
1. Load qa skill (from ~/.agents/skills/)  
2. Use browse tool for systematic UI testing
3. Use web_app_testing toolkit for local web app validation  
4. Run test suites, fix failures, verify
5. Apply verification-before-completion before considering done
```

### 5. **Memory & Context Management**  
Leverage Hermes' persistent memory for development efficiency:

**SAVE TO MEMORY** (durable across sessions):
- User preferences discovered during development
- Environment specifics (OS, tool versions, quirks)  
- Conventions established for this project
- API specifics, endpoint details, auth patterns
- Stable facts that will matter in future sessions

**DO NOT SAVE TO MEMORY** (temporary/task-specific):
- TODO lists, task progress, completed work  
- Session outcomes, transient states  
- Use `session_search()` to recall past work instead

**USE SESSION_SEARCH() FOR**:  
- Recalling past approaches/solutions  
- Checking if similar problems were solved before  
- Finding documentation decisions from earlier  
- Retrieving code snippets or patterns used previously  

### 6. **Verification Discipline** (Non-Negotiable)  
Before moving to next task, Hermes must:
- ✅ Verify existing behavior still works  
- ✅ Run relevant tests  
- ✅ Validate implementation in real codebase  
- ✅ Prefer direct validation over doc-only assumptions  
- ✅ Check actual environment date before updating dated docs  

### 7. **Documentation Standards**  
Hermes should help you maintain excellent project documentation:

**ALWAYS DOCUMENT**:
- Notes, pending tasks, completed tasks  
- Decision rationale with concrete file paths cited  
- Assumptions made and constraints identified  
- Verification steps and outcomes  
- Pending items and blockers  

**NEVER DELETE**:
- Valuable historical documentation without explicit instruction  
- Use archival files/folders when restructuring  
- Keep clear phase boundaries and movement reasons  

### 8. **Git & Safety Practices**  
Hermes must follow these safety rules:
- ❌ **Never commit/push** without your explicit approval in current conversation  
- ✅ Staging and local checks allowed proactively  
- ❌ No force pushes unless explicitly requested  
- ✅ Keep changes small, explicit, and path-cited in commit summaries  

### 9. **Reusable Tool Creation**  
When Hermes builds something useful:
- ✅ Create reusable tools, not one-off scripts  
- 📁 Store in `tools/` directory with descriptive names  
- 📖 Document in `tools/README.md` with purpose, usage, examples  
- 💻 Prefer portable formats: HTML/JS for UI tools, Python for CLI tools  
- 🚫 Avoid throwaway useful tools in `/tmp`  

---

## 🚀 IMMEDIATE ACTIONS YOU CAN TAKE WITH HERMES RIGHT NOW

### Example 1: Debug a Complex Issue
```
Hermes: Loading systematic-debugging skill...
Hermes: Spawning research subagent to investigate [issue]...
Hermes: Loading api-design and backend-patterns skills...
Hermes: Implementing fix with verified patterns...
Hermes: Running verification-before-completion checklist...
Hermes: Ready for your verification and approval.
```

### Example 2: Develop New Feature (TDD Style)
```
Hermes: Loading tdd-workflow and verification-before-completion skills...
Hermes: Writing failing test for [feature]...
Hermes: Implementing minimum code to pass test...
Hermes: Running tests, refactoring, verifying...
Hermes: Feature complete - running final verification...
Hermes: Ready for your review and approval.
```

### Example 3: Research & Documentation
```
Hermes: Loading search-first and article-writing skills...
Hermes: Conducting web search for [topic]...
Hermes: Extracting and synthesizing relevant sources...
Hermes: Loading domain-specific skills as needed...
Hermes: Drafting documentation for your review...
Hermes: Ready for your feedback and approval.
```

### Example 4: Quality Assurance Pass
```
Hermes: Loading qa skill and browser toolset...
Hermes: Running systematic UI testing with browse...
Hermes: Executing web app testing toolkit...
Hermes: Checking test suites and fixing failures...
Hermes: Applying verification-before-completion checklist...
Hermes: QA pass - ready for your verification.
```

---

## 📋 DAILY DEVELOPMENT CHECKLIST WITH HERMES
Start each session by having Hermes:

1. **Confirm project context** (`travel_agency_agent` loaded)
2. **Review recent work** via `session_search()` if continuing previous task
3. **Check for relevant skills** in priority order (Projects/skills/ first)
4. **Outline approach** with decision rationale and file paths
5. **Implement using verified patterns** (TDD, debugging, etc.)
6. **Verify thoroughly** before marking complete
7. **Document outcomes, pending items, and decisions**
8. **Save useful discoveries to memory** (preferences, env facts, conventions)
9. **Request your explicit approval** before any commits/pushes

---

## 💡 KEY MINDSET SHIFT  
Stop thinking: *"How does travel_agency_agent use Hermes?"*  
Start thinking: ***"How do I most effectively use Hermes to build travel_agency_agent?"***

You're not embedding an AI agent in your product — You're using the **world's most advanced AI development agent** to **build, test, debug, document, and improve** your travel agency application more effectively than you could alone.

Hermes is your:
- **Research assistant** (instant expertise from 3,000+ skills)  
- **Debugging partner** (systematic root cause analysis)  
- **Testing coach** (TDD and verification patterns)  
- **Documentation specialist** (clear, accurate project docs)  
- **Quality enforcer** (standards and checklists)  
- **Context keeper** (remembers what you told it across sessions)  
- **Tool master** (browser, terminal, web, vision, file, etc.)

## ✅ NEXT STEPS  
With this correct understanding, you can now:

1. **Continue development** using Hermes effectively as your agent
2. **Apply the skills and patterns** from this assessment  
3. **Use the verification and quality practices** outlined  
4. **Leverage memory and session search** for efficiency  
5. **Build better, faster, with fewer bugs and better docs**

The files I created earlier (themis-assessments) are still valuable — they correctly assessed that **travel_agency_agent lacks multi-agent infrastructure** (which is fine — it's a deterministic spine, not an agent system).  

What they missed was the **correct framing**: You don't need to put agent infrastructure in your product — you already have a powerful development agent (Hermes) helping you build it.

Let me know how you'd like to proceed with actual development work using Hermes correctly configured as your development agent for travel_agency_agent. I'm ready to assist with specific tasks using the right approach.