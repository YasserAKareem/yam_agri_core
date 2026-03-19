# YAM Server Agents - Repository Creation Guide

> **Repository:** `yam-server-agents`
> **Purpose:** A2A agent definitions, tool wrappers, policy packs, orchestration patterns
> **Owner:** Agent Platform Team, AI Application Developers
> **Release Cadence:** Frequent - agents are experimental and evolve rapidly

---

## GitHub Repository Form

### Repository Name
```
yam-server-agents
```

### Description
```
A2A agent definitions, tool wrappers, and orchestration patterns for YAM Server. Build agents that coordinate with each other.
```

### Topics
```
ai-agents, agent-orchestration, a2a, function-calling, tools,
agent-policies, yam-server, autonomous-agents
```

---

## File Structure

```
yam-server-agents/
├── agents/
│   ├── research/
│   │   ├── web-researcher.yaml
│   │   └── document-analyzer.yaml
│   ├── coding/
│   │   ├── code-reviewer.yaml
│   │   └── test-generator.yaml
│   ├── business/
│   │   ├── email-drafter.yaml
│   │   └── meeting-summarizer.yaml
│   └── creative/
│       ├── content-writer.yaml
│       └── brainstormer.yaml
├── tools/
│   ├── web/
│   │   ├── searxng.py
│   │   └── web-scraper.py
│   ├── filesystem/
│   │   ├── file-reader.py
│   │   └── file-writer.py
│   ├── database/
│   │   ├── query-executor.py
│   │   └── schema-inspector.py
│   └── api/
│       ├── rest-client.py
│       └── graphql-client.py
├── policies/
│   ├── allowed-tools.yaml
│   ├── resource-limits.yaml
│   ├── approval-workflows.yaml
│   └── safety-constraints.yaml
├── orchestration/
│   ├── patterns/
│   │   ├── sequential.yaml
│   │   ├── parallel.yaml
│   │   └── hierarchical.yaml
│   └── examples/
│       ├── research-pipeline.yaml
│       └── code-review-workflow.yaml
├── prompts/
│   ├── system/
│   │   ├── researcher.txt
│   │   ├── coder.txt
│   │   └── analyst.txt
│   └── examples/
│       ├── few-shot-coding.yaml
│       └── chain-of-thought.yaml
└── docs/
    ├── AGENT_DESIGN.md
    ├── TOOL_DEVELOPMENT.md
    └── ORCHESTRATION.md
```

---

## Key Concepts

### Agent Definition

```yaml
# agents/research/web-researcher.yaml
name: web-researcher
version: "1.0"
description: "Researches topics using web search and synthesis"

capabilities:
  - web-search
  - content-synthesis
  - citation-tracking

tools:
  - searxng
  - web-scraper
  - url-validator

model_preferences:
  primary: llama-3.1-8b-q8
  fallback: llama-3.2-3b-q4

system_prompt: |
  You are a thorough research assistant. When given a topic:
  1. Break it into searchable questions
  2. Search for authoritative sources
  3. Synthesize findings with citations
  4. Identify gaps in knowledge

policy:
  max_tool_calls: 10
  max_execution_time_seconds: 300
  requires_approval: false
  allowed_domains:
    - "*.edu"
    - "*.gov"
    - "arxiv.org"
    - "github.com"

routing:
  semantic_route: research
  temperature: 0.3
  max_tokens: 2048
```

### Tool Wrapper

```python
# tools/web/searxng.py
from typing import List, Dict
import httpx

async def search(
    query: str,
    num_results: int = 5,
    categories: List[str] = ["general"]
) -> List[Dict]:
    """
    Search using SearXNG instance.

    Args:
        query: Search query
        num_results: Number of results to return
        categories: Search categories

    Returns:
        List of search results with title, url, snippet
    """
    searxng_url = "http://searxng:8080"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{searxng_url}/search",
            params={
                "q": query,
                "format": "json",
                "categories": ",".join(categories)
            }
        )

    results = response.json()["results"][:num_results]

    return [
        {
            "title": r["title"],
            "url": r["url"],
            "snippet": r["content"]
        }
        for r in results
    ]


# Tool schema for function calling
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Search the web using SearXNG",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results (1-10)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
}
```

---

## README Highlights

```markdown
# YAM Server Agents

> Build agents that coordinate with each other.

## What is A2A?

**Agent-to-Agent (A2A)** orchestration allows multiple specialized agents
to collaborate on complex tasks.

Example: Document Analysis Pipeline
```
User uploads PDF →
  [Document Parser Agent] extracts text →
    [Summarizer Agent] creates summary →
      [Fact Checker Agent] verifies claims →
        [Report Generator Agent] produces final report
```

## Built-In Agents

| Agent | Purpose | Tools Used |
|-------|---------|------------|
| **Web Researcher** | Research topics | SearXNG, scraper |
| **Code Reviewer** | Review code | Git, linter, analyzer |
| **Document Analyzer** | Extract insights | Tika, embeddings, LLM |
| **Email Drafter** | Draft emails | Template engine, tone analyzer |

## Creating an Agent

1. Define in YAML
2. Specify tools, model, policy
3. Test with `agent-runner.py`
4. Deploy via orchestration pattern

## Safety Policies

All agents run with:
- Tool allow-lists (explicit permission required)
- Resource limits (execution time, API calls)
- Approval workflows for sensitive actions
- Audit logging for all tool invocations
```

---

**Status:** Ready for creation
