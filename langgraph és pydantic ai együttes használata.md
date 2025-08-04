<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Főbb következtetés

Igen, egyetlen AI-ügynökön belül használható egyszerre **Pydantic AI** az agent‐definíciókhoz és **LangGraph** a routing‐logika és állapőgazdálkodás kezeléséhez – együtt működnek, és kiegészítik egymást.

# Integrációs minta

1. **Pydantic AI Agent**
    - Definiálj egy `Agent` osztályt rendszerpromptokkal, függőségekkel és eszközökkel (tools).[^1_1]
    - Használd a `@agent.tool` dekorátort eszközfüggvényekre, amelyek Pydantic modelleket használnak bemenetként és validált kimenetet adnak vissza.[^1_1]
2. **LangGraph stateful workflow**
    - Definiáld a globális állapotot Pydantic `BaseModel`-ként vagy `TypedDict`-ként, amely tartalmazza a beszélgetés történetét, a lépések listáját, a kérdést stb..[^1_2]
    - Építs egy `StateGraph`‐et, ahol minden node egy-egy függvény, például:
        - agent elindítása (Pydantic AI agent run)
        - tool invocation (eszközhívás)
        - routing (folytassa vagy álljon le)
    - Állítsd be az élkapcsolatokat (`add_edge`, `add_conditional_edges`), hogy a graph a `continue` vagy `end` jelzése alapján iteráljon vagy záródjon.[^1_2]

# Példa kód (részlet)

```python
from pydantic_ai import Agent, RunContext
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List
from pydantic import BaseModel

# 1. Pydantic AI agent definiálása
agent = Agent('openai:gpt-4o', deps_type=None, output_type=str)

@agent.tool
async def wiki_lookup(ctx: RunContext[None], query: str) -> str:
    # Wikipédia-összefoglaló lekérése
    return wikipedia.summary(query, sentences=3)

# 2. Állapot modell
class AgentState(BaseModel):
    messages: List[str]
    steps: List[str]
    question: str
    final_answer: str = None

# 3. LangGraph node-ok
def run_agent(state: AgentState) -> dict:
    result = agent.run_sync(state.question)
    return {"messages": state.messages + [result.output]}

def decide(state: AgentState) -> str:
    last = state.messages[-1]
    return "continue" if not last.startswith("FINAL:") else "end"

# 4. Graph építése
builder = StateGraph(AgentState)
builder.add_node("run_agent", run_agent)
builder.add_node("decide", decide)
builder.add_edge(START, "run_agent")
builder.add_edge("run_agent", "decide")
builder.add_conditional_edges("decide", decide, {"continue": "run_agent", "end": END})
graph = builder.compile()

# 5. Futás
init = AgentState(messages=[], steps=[], question="Ki volt Ada Lovelace?")
output = graph.invoke(init)
print(output)
```


# Előnyök és szempontok

- **Típusbiztonság és validáció**: Pydantic AI garantálja az LLM-kimenetek struktúráját és típusát.[^1_1]
- **Állapotkezelés**: LangGraph képességeivel a futás során checkpointolható, visszatekerhető és emberi beavatkozással folytatható az ügynök.[^1_2]
- **Moduláris felépítés**: Az agent logikát Pydantic AI-ben, a workflow-ot LangGraph-ben tartod, így könnyen bővíthető és karbantartható a kód.[^1_3]
- **Teljesítmény**: Ügynökök aszinkron hívásai és állapotfrissítések hatékonyak, de figyelj a token- és API-költségekre.


# Következtetés

A **Pydantic AI + LangGraph** kombóval létrehozhatsz egy erős, típusbiztos és állapot-követő AI ügynököt, amely jól skálázható és könnyen karbantartható.
– Pydantic AI az **agent \& eszköz definiálás**,
– LangGraph az **üzleti logika és állapot-menedzsment** felelőse.
Ezzel a két keretrendszer zökkenőmentesen együttműködik a komplex AI-workflowk megvalósításához.

<div style="text-align: center">⁂</div>

[^1_1]: https://ai.pydantic.dev/api/agent/

[^1_2]: https://langchain-ai.github.io/langgraph/how-tos/graph-api/

[^1_3]: https://www.reddit.com/r/LangChain/comments/1ji4d2k/langgraph_vs_pydantic_ai/

[^1_4]: https://www.youtube.com/watch?v=P3qH5GVIxD0

[^1_5]: https://ai.pydantic.dev/agents/

[^1_6]: https://www.youtube.com/watch?v=tIrHI7iKpD0

[^1_7]: https://ai.pydantic.dev/multi-agent-applications/

[^1_8]: https://langchain-ai.github.io/langgraph/concepts/multi_agent/

[^1_9]: https://atalupadhyay.wordpress.com/2025/02/15/a-step-by-step-guide-with-pydantic-ai-and-langgraph-to-build-ai-agents/

[^1_10]: https://ai.pydantic.dev

[^1_11]: https://www.langchain.com/langgraph

[^1_12]: https://randbee.com/blog/the-design-of-ai-agents-with-a-langgraph-and-pydantic-demo

[^1_13]: https://www.youtube.com/watch?v=YAo3w7UZmTk

[^1_14]: https://justaithings.org/building-a-text-analysis-langgraph-pipeline-state-management-flexible-95a8dce1e015

[^1_15]: https://www.projectpro.io/article/pydantic-ai/1088

[^1_16]: https://github.com/pydantic/pydantic-ai

[^1_17]: https://duplocloud.com/langchain-vs-langgraph/

[^1_18]: https://www.youtube.com/watch?v=vVGXPRjtAJE

[^1_19]: https://ai.pydantic.dev/models/

[^1_20]: https://github.com/langchain-ai/langgraph/discussions/5113


---

# Források a Pydantic AI és LangGraph együttes használatához

Az alábbi, magyarul is olvasható vagy könnyen érthető angol nyelvű online források példákat és útmutatókat nyújtanak arra, hogyan lehet egyetlen AI-ügynökön belül egyszerre használni a Pydantic AI keretrendszert az agent-definíciókhoz, valamint a LangGraph-ot a routing-logika és állapotkezelés kezeléséhez:


| Forrás címe és típusa | Leírás | Hivatkozás |
| :-- | :-- | :-- |
| A Step-by-Step Guide with Pydantic AI and LangGraph to Build AI Agents (blogposzt) | Részletes, lépésről lépésre útmutató Pydantic AI eszközök definiálására, állapotmodell és LangGraph-workflow egyesítésére. | web:9 |
| Langgraph vs Pydantic AI : r/LangChain (Reddit-vita) | Fejléc, rövid magyarázat, hogy LangGraph a workflow-építő, Pydantic AI pedig a tipizált „traffic layer” egy node-ként a graphban. | web:6 |
| The design of AI Agents with a LangGraph and Pydantic Demo (Randbee blog) | Áttekintő bejegyzés és demo, amely bemutatja a két keretrendszer párhuzamos használatát, installációtól a graph-node definiálásáig (kezdőknek is). | web:12 |
| PydanticAI + Langgraph: The Ultimate Match for Smarter AI Agents! (YouTube bemutató) | Videós walkthrough, kódpéldákkal, ahol LangChain-es ügynököket építenek Pydantic AI eszközökkel, LangGraph node-okkal és edge-ekkel. | web:3 |
| Use the Graph API – LangGraph dokumentáció (hogyan használjunk Pydantic modellt állapotként) | Hivatalos LangGraph-dokumentáció, bemutatja, hogy a `state_schema` lehet Pydantic `BaseModel`, futásidőben validál, és mutatja a graph definiálást. | web:2 |

Ezekkel a forrásokkal közvetlen példák és kódminták állnak rendelkezésre a Pydantic AI és LangGraph keretrendszerek együttes használatára.

<div style="text-align: center">⁂</div>

[^2_1]: https://realpython.com/langgraph-python/

[^2_2]: https://langchain-ai.github.io/langgraph/concepts/why-langgraph/

[^2_3]: https://randbee.com/blog/the-design-of-ai-agents-with-a-langgraph-and-pydantic-demo

[^2_4]: https://langchain-ai.github.io/langgraph/how-tos/graph-api/

[^2_5]: https://www.youtube.com/shorts/XfsVkO9swIw

[^2_6]: https://www.youtube.com/watch?v=P3qH5GVIxD0

[^2_7]: https://www.reddit.com/r/aidevs/comments/1joxpzh/tutorial_how_to_build_ai_agents_with_langgraph/

[^2_8]: https://www.projectpro.io/article/pydantic-ai/1088

[^2_9]: https://ai.pydantic.dev

[^2_10]: https://www.youtube.com/watch?v=vVGXPRjtAJE

[^2_11]: https://atalupadhyay.wordpress.com/2025/02/15/a-step-by-step-guide-with-pydantic-ai-and-langgraph-to-build-ai-agents/

[^2_12]: https://www.reddit.com/r/LangChain/comments/1ji4d2k/langgraph_vs_pydantic_ai/

