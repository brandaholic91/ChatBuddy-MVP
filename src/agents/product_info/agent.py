"""
Product Info Agent - Pydantic AI Tool Implementation for LangGraph.

This module implements the product information agent as a Pydantic AI tool
that can be integrated into the LangGraph workflow.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ...models.agent import AgentType


@dataclass
class ProductInfoDependencies:
    """Product info agent függőségei."""
    user_context: Dict[str, Any]
    supabase_client: Optional[Any] = None
    webshop_api: Optional[Any] = None
    security_context: Optional[Any] = None
    audit_logger: Optional[Any] = None


class ProductInfo(BaseModel):
    """Product információs válasz struktúra."""
    name: str = Field(description="Termék neve")
    price: float = Field(description="Termék ára")
    description: str = Field(description="Termék leírása")
    category: str = Field(description="Termék kategóriája")
    availability: str = Field(description="Elérhetőség")
    specifications: Dict[str, Any] = Field(description="Termék specifikációk", default_factory=dict)
    images: List[str] = Field(description="Termék képek", default_factory=list)
    rating: Optional[float] = Field(description="Értékelés", ge=0.0, le=5.0, default=None)
    review_count: Optional[int] = Field(description="Értékelések száma", ge=0, default=None)


class ProductSearchResult(BaseModel):
    """Termék keresési eredmény."""
    products: List[ProductInfo] = Field(description="Talált termékek", default_factory=list)
    total_count: int = Field(description="Összes találat száma")
    search_query: str = Field(description="Keresési lekérdezés")
    filters_applied: Dict[str, Any] = Field(description="Alkalmazott szűrők", default_factory=dict)


class ProductResponse(BaseModel):
    """Product agent válasz struktúra."""
    response_text: str = Field(description="Agent válasza")
    confidence: float = Field(description="Bizonyosság", ge=0.0, le=1.0)
    category: str = Field(description="Kategória")
    product_info: Optional[ProductInfo] = Field(description="Termék információ", default=None)
    search_results: Optional[ProductSearchResult] = Field(description="Keresési eredmények", default=None)
    metadata: Dict[str, Any] = Field(description="Metaadatok", default_factory=dict)


def create_product_info_agent() -> Agent:
    """
    Product info agent létrehozása Pydantic AI-val.
    
    Returns:
        Product info agent
    """
    agent = Agent(
        'openai:gpt-4o',
        deps_type=ProductInfoDependencies,
        output_type=ProductResponse,
        system_prompt=(
            "Te egy termék információs ügynök vagy a ChatBuddy webshop chatbot-ban. "
            "Feladatod a termékekkel kapcsolatos kérdések megválaszolása. "
            "Válaszolj magyarul, barátságosan és részletesen. "
            "Használd a megfelelő tool-okat a termék információk lekéréséhez. "
            "Ha nem találsz megfelelő terméket, javasolj alternatívákat. "
            "Mindig tartsd szem előtt a biztonsági protokollokat és a GDPR megfelelőséget. "
            "FONTOS: Mindig adj meg egy 'category' mezőt a válaszodban, és használd a tool-okat a termék információk lekéréséhez!"
        )
    )
    
    @agent.tool
    async def search_products(
        ctx: RunContext[ProductInfoDependencies],
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10
    ) -> ProductSearchResult:
        """
        Termékek keresése a webshop adatbázisában.
        
        Args:
            query: Keresési lekérdezés
            category: Kategória szűrő
            min_price: Minimum ár
            max_price: Maximum ár
            limit: Eredmények száma
            
        Returns:
            Keresési eredmények
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual database search
            
            # Audit logging
            if ctx.deps.audit_logger:
                await ctx.deps.audit_logger.log_data_access(
                    user_id=ctx.deps.user_context.get("user_id", "anonymous"),
                    data_type="product_search",
                    operation="search",
                    success=True,
                    details={"query": query, "category": category}
                )
            
            # Mock search results
            mock_products = [
                ProductInfo(
                    name="iPhone 15 Pro",
                    price=450000.0,
                    description="Apple iPhone 15 Pro 128GB Titanium",
                    category="Telefon",
                    availability="Készleten",
                    specifications={
                        "storage": "128GB",
                        "color": "Titanium",
                        "screen": "6.1 inch"
                    },
                    images=["iphone15pro.jpg"],
                    rating=4.8,
                    review_count=156
                ),
                ProductInfo(
                    name="Samsung Galaxy S24",
                    price=380000.0,
                    description="Samsung Galaxy S24 256GB Phantom Black",
                    category="Telefon",
                    availability="Készleten",
                    specifications={
                        "storage": "256GB",
                        "color": "Phantom Black",
                        "screen": "6.2 inch"
                    },
                    images=["galaxys24.jpg"],
                    rating=4.6,
                    review_count=89
                )
            ]
            
            # Filter by query
            filtered_products = [
                p for p in mock_products 
                if query.lower() in p.name.lower() or query.lower() in p.description.lower()
            ]
            
            # Apply category filter
            if category:
                filtered_products = [
                    p for p in filtered_products 
                    if category.lower() in p.category.lower()
                ]
            
            # Apply price filters
            if min_price is not None:
                filtered_products = [p for p in filtered_products if p.price >= min_price]
            
            if max_price is not None:
                filtered_products = [p for p in filtered_products if p.price <= max_price]
            
            # Apply limit
            filtered_products = filtered_products[:limit]
            
            return ProductSearchResult(
                products=filtered_products,
                total_count=len(filtered_products),
                search_query=query,
                filters_applied={
                    "category": category,
                    "min_price": min_price,
                    "max_price": max_price,
                    "limit": limit
                }
            )
            
        except Exception as e:
            # Error handling
            if ctx.deps.audit_logger:
                await ctx.deps.audit_logger.log_data_access(
                    user_id=ctx.deps.user_context.get("user_id", "anonymous"),
                    data_type="product_search",
                    operation="search",
                    success=False,
                    details={"error": str(e)}
                )
            
            # Return empty result on error
            return ProductSearchResult(
                products=[],
                total_count=0,
                search_query=query,
                filters_applied={}
            )
    
    @agent.tool
    async def get_product_details(
        ctx: RunContext[ProductInfoDependencies],
        product_id: str
    ) -> ProductInfo:
        """
        Részletes termék információk lekérése.
        
        Args:
            product_id: Termék azonosító
            
        Returns:
            Termék részletek
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual database query
            
            # Audit logging
            if ctx.deps.audit_logger:
                await ctx.deps.audit_logger.log_data_access(
                    user_id=ctx.deps.user_context.get("user_id", "anonymous"),
                    data_type="product_details",
                    operation="get",
                    success=True,
                    details={"product_id": product_id}
                )
            
            # Mock product details
            mock_product = ProductInfo(
                name="iPhone 15 Pro",
                price=450000.0,
                description="Apple iPhone 15 Pro 128GB Titanium - A legújabb iPhone modell",
                category="Telefon",
                availability="Készleten",
                specifications={
                    "storage": "128GB",
                    "color": "Titanium",
                    "screen": "6.1 inch",
                    "processor": "A17 Pro",
                    "camera": "48MP Main + 12MP Ultra Wide + 12MP Telephoto",
                    "battery": "Up to 23 hours video playback"
                },
                images=["iphone15pro_1.jpg", "iphone15pro_2.jpg"],
                rating=4.8,
                review_count=156
            )
            
            return mock_product
            
        except Exception as e:
            # Error handling
            if ctx.deps.audit_logger:
                await ctx.deps.audit_logger.log_data_access(
                    user_id=ctx.deps.user_context.get("user_id", "anonymous"),
                    data_type="product_details",
                    operation="get",
                    success=False,
                    details={"error": str(e)}
                )
            
            # Return empty product on error
            return ProductInfo(
                name="Ismeretlen termék",
                price=0.0,
                description="Termék információ nem elérhető",
                category="Ismeretlen",
                availability="Nem elérhető",
                specifications={},
                images=[],
                rating=0.0,
                review_count=0
            )
    
    @agent.tool
    async def get_product_categories(
        ctx: RunContext[ProductInfoDependencies]
    ) -> List[str]:
        """
        Elérhető termék kategóriák lekérése.
        
        Returns:
            Kategória lista
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual database query
            
            categories = [
                "Telefon",
                "Laptop",
                "Tablet",
                "Okosóra",
                "Fülhallgató",
                "Hangszóró",
                "Kamera",
                "Játék",
                "Kiegészítő"
            ]
            
            return categories
            
        except Exception as e:
            # Return basic categories on error
            return ["Telefon", "Laptop", "Tablet"]
    
    @agent.tool
    async def get_price_range(
        ctx: RunContext[ProductInfoDependencies],
        category: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Ár tartomány lekérése kategóriához.
        
        Args:
            category: Kategória (opcionális)
            
        Returns:
            Ár tartomány
        """
        try:
            # Mock implementation for development
            # TODO: Implement actual database query
            
            if category == "Telefon":
                return {"min": 150000.0, "max": 600000.0}
            elif category == "Laptop":
                return {"min": 300000.0, "max": 1500000.0}
            else:
                return {"min": 50000.0, "max": 1000000.0}
                
        except Exception as e:
            # Return default range on error
            return {"min": 0.0, "max": 1000000.0}
    
    return agent


# Convenience function for LangGraph integration
async def call_product_info_agent(
    message: str,
    dependencies: ProductInfoDependencies
) -> ProductResponse:
    """
    Product info agent hívása LangGraph workflow-ból.
    
    Args:
        message: Felhasználói üzenet
        dependencies: Agent függőségek
        
    Returns:
        Product agent válasz
    """
    agent = create_product_info_agent()
    result = await agent.run(message, deps=dependencies)
    return result.output 