"""
Database schema manager for Chatbuddy MVP.

This module provides schema management functionality:
- Table creation and migration
- Schema validation
- Index management
- Constraint management
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from src.config.logging import get_logger
from .supabase_client import SupabaseClient

logger = get_logger(__name__)


class SchemaManager:
    """Adatbázis schema kezelő"""
    
    def __init__(self, supabase_client: SupabaseClient):
        """Inicializálja a schema managert"""
        self.supabase = supabase_client
        self.schema_path = Path(__file__).parent / "schemas"
        self.schema_path.mkdir(exist_ok=True)
    
    def create_users_table(self) -> bool:
        """Létrehozza a users táblát"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'customer' CHECK (role IN ('customer', 'admin', 'support', 'agent')),
                status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'pending')),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_login TIMESTAMP WITH TIME ZONE,
                metadata JSONB DEFAULT '{}'::jsonb
            );
            
            -- Indexek
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
            CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
            CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
            
            -- RLS engedélyezése
            ALTER TABLE users ENABLE ROW LEVEL SECURITY;
            """
            
            self.supabase.execute_query(query)
            logger.info("Users tábla sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a users tábla létrehozásakor: {e}")
            return False
    
    def create_user_profiles_table(self) -> bool:
        """Létrehozza a user_profiles táblát"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                phone VARCHAR(50),
                address TEXT,
                city VARCHAR(100),
                postal_code VARCHAR(20),
                country VARCHAR(100) DEFAULT 'Hungary',
                birth_date DATE,
                gender VARCHAR(20),
                language VARCHAR(10) DEFAULT 'hu',
                timezone VARCHAR(50) DEFAULT 'Europe/Budapest',
                avatar_url TEXT,
                bio TEXT,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Indexek
            CREATE INDEX IF NOT EXISTS idx_user_profiles_country ON user_profiles(country);
            CREATE INDEX IF NOT EXISTS idx_user_profiles_language ON user_profiles(language);
            
            -- RLS engedélyezése
            ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
            """
            
            self.supabase.execute_query(query)
            logger.info("User profiles tábla sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a user_profiles tábla létrehozásakor: {e}")
            return False
    
    def create_user_preferences_table(self) -> bool:
        """Létrehozza a user_preferences táblát"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                notification_email BOOLEAN DEFAULT TRUE,
                notification_sms BOOLEAN DEFAULT FALSE,
                notification_push BOOLEAN DEFAULT TRUE,
                marketing_emails BOOLEAN DEFAULT TRUE,
                newsletter BOOLEAN DEFAULT FALSE,
                chat_history BOOLEAN DEFAULT TRUE,
                auto_save_cart BOOLEAN DEFAULT TRUE,
                product_recommendations BOOLEAN DEFAULT TRUE,
                personalized_offers BOOLEAN DEFAULT TRUE,
                theme VARCHAR(20) DEFAULT 'light',
                language VARCHAR(10) DEFAULT 'hu',
                currency VARCHAR(10) DEFAULT 'HUF',
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- RLS engedélyezése
            ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
            """
            
            self.supabase.execute_query(query)
            logger.info("User preferences tábla sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a user_preferences tábla létrehozásakor: {e}")
            return False
    
    def create_products_table(self) -> bool:
        """Létrehozza a products táblát pgvector támogatással"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS products (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                short_description TEXT,
                price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
                original_price DECIMAL(10,2) CHECK (original_price >= 0),
                currency VARCHAR(10) DEFAULT 'HUF',
                category_id UUID,
                brand VARCHAR(100),
                sku VARCHAR(100) UNIQUE,
                barcode VARCHAR(100),
                weight DECIMAL(8,3) CHECK (weight >= 0),
                dimensions JSONB DEFAULT '{}'::jsonb,
                status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'out_of_stock', 'discontinued', 'draft')),
                product_type VARCHAR(50) DEFAULT 'physical' CHECK (product_type IN ('physical', 'digital', 'service', 'subscription')),
                stock_quantity INTEGER DEFAULT 0,
                min_stock_level INTEGER DEFAULT 0,
                max_stock_level INTEGER,
                is_featured BOOLEAN DEFAULT FALSE,
                is_bestseller BOOLEAN DEFAULT FALSE,
                is_new BOOLEAN DEFAULT FALSE,
                is_on_sale BOOLEAN DEFAULT FALSE,
                sale_percentage INTEGER CHECK (sale_percentage >= 0 AND sale_percentage <= 100),
                tags TEXT[] DEFAULT '{}',
                images TEXT[] DEFAULT '{}',
                main_image TEXT,
                embedding VECTOR(1536), -- OpenAI text-embedding-ada-002 dimenzió
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Indexek
            CREATE INDEX IF NOT EXISTS idx_products_name ON products USING gin(to_tsvector('hungarian', name));
            CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
            CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
            CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
            CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
            CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
            CREATE INDEX IF NOT EXISTS idx_products_tags ON products USING gin(tags);
            CREATE INDEX IF NOT EXISTS idx_products_created_at ON products(created_at);
            
            -- Vector index a similarity search-hez
            CREATE INDEX IF NOT EXISTS idx_products_embedding ON products USING hnsw (embedding vector_cosine_ops);
            
            -- RLS engedélyezése
            ALTER TABLE products ENABLE ROW LEVEL SECURITY;
            """
            
            self.supabase.execute_query(query)
            logger.info("Products tábla sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a products tábla létrehozásakor: {e}")
            return False
    
    def create_product_categories_table(self) -> bool:
        """Létrehozza a product_categories táblát"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS product_categories (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                parent_id UUID REFERENCES product_categories(id),
                slug VARCHAR(255) UNIQUE NOT NULL,
                image_url TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                sort_order INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                path TEXT[] DEFAULT '{}',
                product_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Indexek
            CREATE INDEX IF NOT EXISTS idx_product_categories_parent ON product_categories(parent_id);
            CREATE INDEX IF NOT EXISTS idx_product_categories_slug ON product_categories(slug);
            CREATE INDEX IF NOT EXISTS idx_product_categories_level ON product_categories(level);
            CREATE INDEX IF NOT EXISTS idx_product_categories_path ON product_categories USING gin(path);
            
            -- RLS engedélyezése
            ALTER TABLE product_categories ENABLE ROW LEVEL SECURITY;
            """
            
            self.supabase.execute_query(query)
            logger.info("Product categories tábla sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a product_categories tábla létrehozásakor: {e}")
            return False
    
    def create_orders_table(self) -> bool:
        """Létrehozza a orders táblát"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS orders (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                order_number VARCHAR(100) UNIQUE NOT NULL,
                user_id UUID NOT NULL REFERENCES users(id),
                status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded', 'partially_refunded', 'returned', 'on_hold')),
                payment_status VARCHAR(50) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'authorized', 'paid', 'failed', 'refunded', 'partially_refunded', 'cancelled')),
                payment_method VARCHAR(50) CHECK (payment_method IN ('credit_card', 'debit_card', 'bank_transfer', 'cash_on_delivery', 'paypal', 'apple_pay', 'google_pay', 'crypto')),
                subtotal DECIMAL(10,2) NOT NULL CHECK (subtotal >= 0),
                tax_amount DECIMAL(10,2) DEFAULT 0 CHECK (tax_amount >= 0),
                shipping_amount DECIMAL(10,2) DEFAULT 0 CHECK (shipping_amount >= 0),
                discount_amount DECIMAL(10,2) DEFAULT 0 CHECK (discount_amount >= 0),
                total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
                currency VARCHAR(10) DEFAULT 'HUF',
                shipping_method VARCHAR(50) CHECK (shipping_method IN ('standard', 'express', 'next_day', 'same_day', 'pickup', 'international')),
                shipping_address JSONB DEFAULT '{}'::jsonb,
                billing_address JSONB DEFAULT '{}'::jsonb,
                tracking_number VARCHAR(100),
                tracking_url TEXT,
                estimated_delivery TIMESTAMP WITH TIME ZONE,
                notes TEXT,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Indexek
            CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
            CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
            CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
            CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders(payment_status);
            CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
            
            -- RLS engedélyezése
            ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
            """
            
            self.supabase.execute_query(query)
            logger.info("Orders tábla sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba az orders tábla létrehozásakor: {e}")
            return False
    
    def create_order_items_table(self) -> bool:
        """Létrehozza az order_items táblát"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS order_items (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                product_id UUID NOT NULL REFERENCES products(id),
                variant_id UUID,
                product_name VARCHAR(255) NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
                total_price DECIMAL(10,2) NOT NULL CHECK (total_price >= 0),
                discount_amount DECIMAL(10,2) DEFAULT 0 CHECK (discount_amount >= 0),
                tax_amount DECIMAL(10,2) DEFAULT 0 CHECK (tax_amount >= 0),
                attributes JSONB DEFAULT '{}'::jsonb,
                image_url TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Indexek
            CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
            CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
            
            -- RLS engedélyezése
            ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
            """
            
            self.supabase.execute_query(query)
            logger.info("Order items tábla sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba az order_items tábla létrehozásakor: {e}")
            return False
    
    def create_chat_sessions_table(self) -> bool:
        """Létrehozza a chat_sessions táblát"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                context JSONB DEFAULT '{}'::jsonb,
                is_active BOOLEAN DEFAULT TRUE,
                agent_used VARCHAR(100),
                message_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Indexek
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_started_at ON chat_sessions(started_at);
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_activity ON chat_sessions(last_activity);
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_is_active ON chat_sessions(is_active);
            
            -- RLS engedélyezése
            ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
            """
            
            self.supabase.execute_query(query)
            logger.info("Chat sessions tábla sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a chat_sessions tábla létrehozásakor: {e}")
            return False
    
    def create_chat_messages_table(self) -> bool:
        """Létrehozza a chat_messages táblát"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                type VARCHAR(20) NOT NULL CHECK (type IN ('user', 'assistant', 'system', 'error', 'tool')),
                content TEXT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                metadata JSONB DEFAULT '{}'::jsonb,
                agent_used VARCHAR(100),
                confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Indexek
            CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp);
            CREATE INDEX IF NOT EXISTS idx_chat_messages_type ON chat_messages(type);
            CREATE INDEX IF NOT EXISTS idx_chat_messages_agent ON chat_messages(agent_used);
            
            -- RLS engedélyezése
            ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
            """
            
            self.supabase.execute_query(query)
            logger.info("Chat messages tábla sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a chat_messages tábla létrehozásakor: {e}")
            return False
    
    def create_audit_logs_table(self) -> bool:
        """Létrehozza az audit_logs táblát"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                session_id UUID REFERENCES chat_sessions(session_id),
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(50),
                resource_id UUID,
                details JSONB DEFAULT '{}'::jsonb,
                ip_address INET,
                user_agent TEXT,
                severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Indexek
            CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_session_id ON audit_logs(session_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_severity ON audit_logs(severity);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
            
            -- RLS engedélyezése
            ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
            """
            
            self.supabase.execute_query(query)
            logger.info("Audit logs tábla sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba az audit_logs tábla létrehozásakor: {e}")
            return False
    
    def create_user_consents_table(self) -> bool:
        """Létrehozza a user_consents táblát GDPR compliance-hoz"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS user_consents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                consent_type VARCHAR(100) NOT NULL,
                consent_version VARCHAR(20) NOT NULL,
                granted BOOLEAN NOT NULL,
                granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                revoked_at TIMESTAMP WITH TIME ZONE,
                ip_address INET,
                user_agent TEXT,
                consent_text TEXT,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Indexek
            CREATE INDEX IF NOT EXISTS idx_user_consents_user_id ON user_consents(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_consents_type ON user_consents(consent_type);
            CREATE INDEX IF NOT EXISTS idx_user_consents_granted ON user_consents(granted);
            CREATE INDEX IF NOT EXISTS idx_user_consents_granted_at ON user_consents(granted_at);
            
            -- RLS engedélyezése
            ALTER TABLE user_consents ENABLE ROW LEVEL SECURITY;
            """
            
            self.supabase.execute_query(query)
            logger.info("User consents tábla sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a user_consents tábla létrehozásakor: {e}")
            return False
    
    def create_all_tables(self) -> Dict[str, bool]:
        """Létrehozza az összes táblát"""
        results = {}
        
        # pgvector extension engedélyezése
        results["pgvector_extension"] = self.supabase.enable_pgvector_extension()
        
        # Táblák létrehozása
        results["users"] = self.create_users_table()
        results["user_profiles"] = self.create_user_profiles_table()
        results["user_preferences"] = self.create_user_preferences_table()
        results["product_categories"] = self.create_product_categories_table()
        results["products"] = self.create_products_table()
        results["orders"] = self.create_orders_table()
        results["order_items"] = self.create_order_items_table()
        results["chat_sessions"] = self.create_chat_sessions_table()
        results["chat_messages"] = self.create_chat_messages_table()
        results["audit_logs"] = self.create_audit_logs_table()
        results["user_consents"] = self.create_user_consents_table()
        
        # Eredmények logolása
        for table, success in results.items():
            if success:
                logger.info(f"✅ {table} tábla sikeresen létrehozva")
            else:
                logger.error(f"❌ {table} tábla létrehozása sikertelen")
        
        return results
    
    def validate_schema(self) -> Dict[str, Any]:
        """Validálja a schema-t"""
        tables = [
            "users", "user_profiles", "user_preferences", 
            "product_categories", "products", "orders", "order_items",
            "chat_sessions", "chat_messages", "audit_logs", "user_consents"
        ]
        
        validation_results = {}
        
        for table in tables:
            try:
                info = self.supabase.get_table_info(table)
                rls_enabled = self.supabase.check_rls_enabled(table)
                
                validation_results[table] = {
                    "exists": len(info) > 0,
                    "columns": len(info),
                    "rls_enabled": rls_enabled,
                    "columns_info": info
                }
                
            except Exception as e:
                validation_results[table] = {
                    "exists": False,
                    "error": str(e)
                }
        
        return validation_results 