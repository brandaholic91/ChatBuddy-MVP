# Pydantic AI Pattern Javítások

## 🚨 Kritikus Javítások Összefoglalója

A hivatalos Pydantic AI dokumentáció alapján **kritikus hibákat** találtunk és javítottunk a tervezési dokumentumokban.

---

## 📋 **Javított Hibák:**

### **1. ❌ HIBÁS: BaseModel Dependency Classes**

**PROBLÉMA:**
```python
# ❌ HIBÁS (eredeti tervben):
from pydantic import BaseModel

class CoordinatorDependencies(BaseModel):
    session_data: dict
    supabase_client: Any
```

**✅ HELYES:**
```python
# ✅ JAVÍTOTT:
from dataclasses import dataclass

@dataclass
class CoordinatorDependencies:
    session_data: dict
    supabase_client: Any
    database: Any
    user_context: dict
```

**INDOKLÁS:** Pydantic AI dependency injection `@dataclass`-t használ, **NEM** `BaseModel`-t!

---

### **2. ✅ HELYES Agent Létrehozás**

```python
# Minden agent így nézzen ki:
agent = Agent(
    'openai:gpt-4o',
    deps_type=YourDependenciesClass,  # @dataclass
    output_type=YourOutputModel,      # BaseModel (strukturált kimenet)
    system_prompt="Your instructions..."
)
```

---

### **3. ✅ HELYES Tool/System Prompt Pattern**

```python
@agent.tool
async def your_tool(
    ctx: RunContext[YourDependenciesClass],  # 👈 MINDIG első paraméter
    other_param: str
) -> ReturnType:
    """Tool leírása az LLM számára"""
    # Dependency elérés:
    data = await ctx.deps.supabase_client.get_data()
    return data

@agent.system_prompt
async def dynamic_prompt(ctx: RunContext[YourDependenciesClass]) -> str:
    user_name = await ctx.deps.supabase_client.get_user_name()
    return f"A felhasználó neve: {user_name}"
```

---

## 🎯 **Javított Agent Példák**

### **Koordinátor Ügynök:**
```python
@dataclass
class CoordinatorDependencies:
    session_data: dict
    supabase_client: Any
    database: Any
    user_context: dict

class AgentDecision(BaseModel):
    target_agent: Literal["product_info", "order_status", "recommendation", "general"]
    confidence: float
    reasoning: str

coordinator_agent = Agent(
    'openai:gpt-4o',
    deps_type=CoordinatorDependencies,
    output_type=AgentDecision,
    system_prompt="Te egy koordinátor vagy..."
)

@coordinator_agent.tool
async def analyze_message_intent(
    ctx: RunContext[CoordinatorDependencies], 
    user_message: str
) -> str:
    # Dependency használat:
    user_data = await ctx.deps.supabase_client.get_user(
        ctx.deps.user_context['user_id']
    )
    return f"Analyzed: {user_message} for user: {user_data['name']}"
```

### **Termékinformációs Ügynök:**
```python
@dataclass
class ProductInfoDependencies:
    supabase_client: Any
    webshop_api: Any
    user_context: dict

class ProductInfo(BaseModel):
    name: str
    price: float
    description: str
    availability: str
    category: str

product_info_agent = Agent(
    'openai:gpt-4o',
    deps_type=ProductInfoDependencies,
    output_type=ProductInfo,
    system_prompt="Te egy termék információs specialista vagy..."
)

@product_info_agent.tool
async def search_products(
    ctx: RunContext[ProductInfoDependencies], 
    query: str,
    category: Optional[str] = None
) -> List[dict]:
    results = await ctx.deps.webshop_api.search_products(
        query=query, 
        category=category
    )
    return results
```

---

## 📝 **Agent Használat Pattern:**

```python
# Dependency létrehozás:
deps = YourDependenciesClass(
    supabase_client=supabase_client,
    webshop_api=webshop_api,
    user_context={'user_id': 123}
)

# Agent futtatás:
result = await agent.run("User kérdése", deps=deps)

# Strukturált kimenet (validált):
print(result.output)  # YourOutputModel instance
print(result.output.field_name)  # Type-safe hozzáférés
```

---

## ⚡ **Főbb Előnyök:**

1. **Type Safety:** `RunContext[DepsType]` biztosítja a típusbiztonságot
2. **Dependency Injection:** Tiszta, tesztelhető kód
3. **Strukturált Kimenet:** Pydantic BaseModel validáció
4. **Async Support:** Teljes aszinkron támogatás
5. **Tool Integration:** LLM-callable Python függvények

---

## 🔄 **Következő Lépések:**

1. ✅ **Dokumentáció javítva**
2. 🔄 **Konkrét implementáció következik**
3. 🔄 **B Opció mérlegelése:** LangGraph prebuilt komponensek

---

## 📚 **Referenciák:**

- [Pydantic AI Official Docs](https://ai.pydantic.dev/)
- [Dependency Injection Guide](https://ai.pydantic.dev/dependencies/)
- [Agent Examples](https://ai.pydantic.dev/examples/)