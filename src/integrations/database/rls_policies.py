"""
Row Level Security (RLS) policies for Chatbuddy MVP.

This module provides RLS policy management:
- Policy creation and management
- GDPR compliance policies
- Security policies for different user roles
- Audit trail policies
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum

from src.config.logging import get_logger
from .supabase_client import SupabaseClient

logger = get_logger(__name__)


class PolicyType(str, Enum):
    """RLS policy típusok"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    ALL = "all"


class RLSPolicyManager:
    """Row Level Security policy kezelő"""
    
    def __init__(self, supabase_client: SupabaseClient):
        """Inicializálja a RLS policy managert"""
        self.supabase = supabase_client
    
    def create_users_policies(self) -> bool:
        """Létrehozza a users tábla RLS policy-jeit"""
        try:
            policies = [
                # Felhasználók csak saját adataikat láthatják
                """
                CREATE POLICY "Users can view own profile"
                ON users FOR SELECT
                TO authenticated
                USING (auth.uid() = id);
                """,
                
                # Felhasználók csak saját adataikat módosíthatják
                """
                CREATE POLICY "Users can update own profile"
                ON users FOR UPDATE
                TO authenticated
                USING (auth.uid() = id)
                WITH CHECK (auth.uid() = id);
                """,
                
                # Adminok minden felhasználót láthatnak
                """
                CREATE POLICY "Admins can view all users"
                ON users FOR SELECT
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE id = auth.uid() AND role = 'admin'
                    )
                );
                """,
                
                # Adminok minden felhasználót módosíthatnak
                """
                CREATE POLICY "Admins can update all users"
                ON users FOR UPDATE
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE id = auth.uid() AND role = 'admin'
                    )
                );
                """,
                
                # Support felhasználók csak customer adatait láthatják
                """
                CREATE POLICY "Support can view customers"
                ON users FOR SELECT
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE id = auth.uid() AND role = 'support'
                    ) AND role = 'customer'
                );
                """
            ]
            
            for policy in policies:
                self.supabase.execute_query(policy)
            
            logger.info("Users tábla RLS policy-k sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a users RLS policy-k létrehozásakor: {e}")
            return False
    
    def create_user_profiles_policies(self) -> bool:
        """Létrehozza a user_profiles tábla RLS policy-jeit"""
        try:
            policies = [
                # Felhasználók csak saját profiljukat láthatják
                """
                CREATE POLICY "Users can view own profile"
                ON user_profiles FOR SELECT
                TO authenticated
                USING (auth.uid() = user_id);
                """,
                
                # Felhasználók csak saját profiljukat módosíthatják
                """
                CREATE POLICY "Users can update own profile"
                ON user_profiles FOR UPDATE
                TO authenticated
                USING (auth.uid() = user_id)
                WITH CHECK (auth.uid() = user_id);
                """,
                
                # Felhasználók saját profiljukat létrehozhatják
                """
                CREATE POLICY "Users can insert own profile"
                ON user_profiles FOR INSERT
                TO authenticated
                WITH CHECK (auth.uid() = user_id);
                """,
                
                # Adminok minden profilt láthatnak
                """
                CREATE POLICY "Admins can view all profiles"
                ON user_profiles FOR SELECT
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE id = auth.uid() AND role = 'admin'
                    )
                );
                """
            ]
            
            for policy in policies:
                self.supabase.execute_query(policy)
            
            logger.info("User profiles tábla RLS policy-k sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a user_profiles RLS policy-k létrehozásakor: {e}")
            return False
    
    def create_user_preferences_policies(self) -> bool:
        """Létrehozza a user_preferences tábla RLS policy-jeit"""
        try:
            policies = [
                # Felhasználók csak saját preferenciáikat láthatják
                """
                CREATE POLICY "Users can view own preferences"
                ON user_preferences FOR SELECT
                TO authenticated
                USING (auth.uid() = user_id);
                """,
                
                # Felhasználók csak saját preferenciáikat módosíthatják
                """
                CREATE POLICY "Users can update own preferences"
                ON user_preferences FOR UPDATE
                TO authenticated
                USING (auth.uid() = user_id)
                WITH CHECK (auth.uid() = user_id);
                """,
                
                # Felhasználók saját preferenciáikat létrehozhatják
                """
                CREATE POLICY "Users can insert own preferences"
                ON user_preferences FOR INSERT
                TO authenticated
                WITH CHECK (auth.uid() = user_id);
                """
            ]
            
            for policy in policies:
                self.supabase.execute_query(policy)
            
            logger.info("User preferences tábla RLS policy-k sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a user_preferences RLS policy-k létrehozásakor: {e}")
            return False
    
    def create_products_policies(self) -> bool:
        """Létrehozza a products tábla RLS policy-jeit"""
        try:
            policies = [
                # Mindenki láthatja az aktív termékeket
                """
                CREATE POLICY "Public can view active products"
                ON products FOR SELECT
                TO authenticated, anon
                USING (status = 'active');
                """,
                
                # Adminok minden terméket láthatnak és módosíthatnak
                """
                CREATE POLICY "Admins can manage all products"
                ON products FOR ALL
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE id = auth.uid() AND role = 'admin'
                    )
                );
                """,
                
                # Support felhasználók termékeket láthatnak
                """
                CREATE POLICY "Support can view products"
                ON products FOR SELECT
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE id = auth.uid() AND role = 'support'
                    )
                );
                """
            ]
            
            for policy in policies:
                self.supabase.execute_query(policy)
            
            logger.info("Products tábla RLS policy-k sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a products RLS policy-k létrehozásakor: {e}")
            return False
    
    def create_orders_policies(self) -> bool:
        """Létrehozza az orders tábla RLS policy-jeit"""
        try:
            policies = [
                # Felhasználók csak saját rendeléseiket láthatják
                """
                CREATE POLICY "Users can view own orders"
                ON orders FOR SELECT
                TO authenticated
                USING (auth.uid() = user_id);
                """,
                
                # Felhasználók saját rendeléseiket létrehozhatják
                """
                CREATE POLICY "Users can create own orders"
                ON orders FOR INSERT
                TO authenticated
                WITH CHECK (auth.uid() = user_id);
                """,
                
                # Adminok minden rendelést láthatnak és módosíthatnak
                """
                CREATE POLICY "Admins can manage all orders"
                ON orders FOR ALL
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE id = auth.uid() AND role = 'admin'
                    )
                );
                """,
                
                # Support felhasználók rendeléseket láthatnak
                """
                CREATE POLICY "Support can view orders"
                ON orders FOR SELECT
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE id = auth.uid() AND role = 'support'
                    )
                );
                """
            ]
            
            for policy in policies:
                self.supabase.execute_query(policy)
            
            logger.info("Orders tábla RLS policy-k sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba az orders RLS policy-k létrehozásakor: {e}")
            return False
    
    def create_chat_sessions_policies(self) -> bool:
        """Létrehozza a chat_sessions tábla RLS policy-jeit"""
        try:
            policies = [
                # Felhasználók csak saját session-jeiket láthatják
                """
                CREATE POLICY "Users can view own sessions"
                ON chat_sessions FOR SELECT
                TO authenticated
                USING (auth.uid() = user_id);
                """,
                
                # Felhasználók saját session-jeiket létrehozhatják
                """
                CREATE POLICY "Users can create own sessions"
                ON chat_sessions FOR INSERT
                TO authenticated
                WITH CHECK (auth.uid() = user_id);
                """,
                
                # Felhasználók saját session-jeiket módosíthatják
                """
                CREATE POLICY "Users can update own sessions"
                ON chat_sessions FOR UPDATE
                TO authenticated
                USING (auth.uid() = user_id)
                WITH CHECK (auth.uid() = user_id);
                """,
                
                # Adminok minden session-t láthatnak
                """
                CREATE POLICY "Admins can view all sessions"
                ON chat_sessions FOR SELECT
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE id = auth.uid() AND role = 'admin'
                    )
                );
                """
            ]
            
            for policy in policies:
                self.supabase.execute_query(policy)
            
            logger.info("Chat sessions tábla RLS policy-k sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a chat_sessions RLS policy-k létrehozásakor: {e}")
            return False
    
    def create_chat_messages_policies(self) -> bool:
        """Létrehozza a chat_messages tábla RLS policy-jeit"""
        try:
            policies = [
                # Felhasználók csak saját session-jeik üzeneteit láthatják
                """
                CREATE POLICY "Users can view own session messages"
                ON chat_messages FOR SELECT
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM chat_sessions 
                        WHERE session_id = chat_messages.session_id 
                        AND user_id = auth.uid()
                    )
                );
                """,
                
                # Felhasználók üzeneteket küldhetnek saját session-jeikbe
                """
                CREATE POLICY "Users can insert messages to own sessions"
                ON chat_messages FOR INSERT
                TO authenticated
                WITH CHECK (
                    EXISTS (
                        SELECT 1 FROM chat_sessions 
                        WHERE session_id = chat_messages.session_id 
                        AND user_id = auth.uid()
                    )
                );
                """,
                
                # Adminok minden üzenetet láthatnak
                """
                CREATE POLICY "Admins can view all messages"
                ON chat_messages FOR SELECT
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE id = auth.uid() AND role = 'admin'
                    )
                );
                """
            ]
            
            for policy in policies:
                self.supabase.execute_query(policy)
            
            logger.info("Chat messages tábla RLS policy-k sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a chat_messages RLS policy-k létrehozásakor: {e}")
            return False
    
    def create_audit_logs_policies(self) -> bool:
        """Létrehozza az audit_logs tábla RLS policy-jeit"""
        try:
            policies = [
                # Felhasználók csak saját audit log-jaikat láthatják
                """
                CREATE POLICY "Users can view own audit logs"
                ON audit_logs FOR SELECT
                TO authenticated
                USING (auth.uid() = user_id);
                """,
                
                # Adminok minden audit log-ot láthatnak
                """
                CREATE POLICY "Admins can view all audit logs"
                ON audit_logs FOR SELECT
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE id = auth.uid() AND role = 'admin'
                    )
                );
                """,
                
                # Rendszer audit log-okat írhat (service role)
                """
                CREATE POLICY "System can insert audit logs"
                ON audit_logs FOR INSERT
                TO service_role
                WITH CHECK (true);
                """
            ]
            
            for policy in policies:
                self.supabase.execute_query(policy)
            
            logger.info("Audit logs tábla RLS policy-k sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba az audit_logs RLS policy-k létrehozásakor: {e}")
            return False
    
    def create_user_consents_policies(self) -> bool:
        """Létrehozza a user_consents tábla RLS policy-jeit GDPR compliance-hoz"""
        try:
            policies = [
                # Felhasználók csak saját consent-jeiket láthatják
                """
                CREATE POLICY "Users can view own consents"
                ON user_consents FOR SELECT
                TO authenticated
                USING (auth.uid() = user_id);
                """,
                
                # Felhasználók saját consent-jeiket létrehozhatják
                """
                CREATE POLICY "Users can create own consents"
                ON user_consents FOR INSERT
                TO authenticated
                WITH CHECK (auth.uid() = user_id);
                """,
                
                # Felhasználók saját consent-jeiket módosíthatják (visszavonás)
                """
                CREATE POLICY "Users can update own consents"
                ON user_consents FOR UPDATE
                TO authenticated
                USING (auth.uid() = user_id)
                WITH CHECK (auth.uid() = user_id);
                """,
                
                # Adminok minden consent-et láthatnak
                """
                CREATE POLICY "Admins can view all consents"
                ON user_consents FOR SELECT
                TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM users 
                        WHERE id = auth.uid() AND role = 'admin'
                    )
                );
                """,
                
                # GDPR compliance: Felhasználók saját adataikat törölhetik
                """
                CREATE POLICY "Users can delete own consents"
                ON user_consents FOR DELETE
                TO authenticated
                USING (auth.uid() = user_id);
                """
            ]
            
            for policy in policies:
                self.supabase.execute_query(policy)
            
            logger.info("User consents tábla RLS policy-k sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a user_consents RLS policy-k létrehozásakor: {e}")
            return False
    
    def create_gdpr_compliance_policies(self) -> bool:
        """Létrehozza a GDPR compliance policy-ket"""
        try:
            # GDPR "right to be forgotten" funkció
            gdpr_function = """
            CREATE OR REPLACE FUNCTION delete_user_data(user_uuid UUID)
            RETURNS VOID
            LANGUAGE plpgsql
            SECURITY DEFINER
            AS $$
            BEGIN
                -- Audit log a törlésről
                INSERT INTO audit_logs (
                    user_id, action, resource_type, resource_id, 
                    details, severity, created_at
                ) VALUES (
                    user_uuid, 'gdpr_data_deletion', 'user', user_uuid,
                    '{"reason": "GDPR right to be forgotten"}', 'info', NOW()
                );
                
                -- Törlés sorrend: függőségek miatt
                DELETE FROM user_consents WHERE user_id = user_uuid;
                DELETE FROM chat_messages WHERE session_id IN (
                    SELECT session_id FROM chat_sessions WHERE user_id = user_uuid
                );
                DELETE FROM chat_sessions WHERE user_id = user_uuid;
                DELETE FROM order_items WHERE order_id IN (
                    SELECT id FROM orders WHERE user_id = user_uuid
                );
                DELETE FROM orders WHERE user_id = user_uuid;
                DELETE FROM user_preferences WHERE user_id = user_uuid;
                DELETE FROM user_profiles WHERE user_id = user_uuid;
                DELETE FROM audit_logs WHERE user_id = user_uuid;
                
                -- Felhasználó adatok anonimizálása (törlés helyett)
                UPDATE users SET 
                    email = 'deleted_' || id || '@deleted.com',
                    name = 'Deleted User',
                    metadata = jsonb_build_object('deleted_at', NOW(), 'gdpr_deletion', true),
                    status = 'inactive'
                WHERE id = user_uuid;
                
            END;
            $$;
            """
            
            self.supabase.execute_query(gdpr_function)
            logger.info("GDPR compliance funkciók sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a GDPR compliance policy-k létrehozásakor: {e}")
            return False
    
    def create_audit_trail_policies(self) -> bool:
        """Létrehozza az audit trail policy-ket"""
        try:
            # Automatikus audit log trigger funkció
            audit_function = """
            CREATE OR REPLACE FUNCTION audit_trigger_function()
            RETURNS TRIGGER
            LANGUAGE plpgsql
            SECURITY DEFINER
            AS $$
            DECLARE
                user_uuid UUID;
                action_type TEXT;
                resource_type TEXT;
                resource_id UUID;
            BEGIN
                -- Felhasználó azonosítása
                user_uuid := auth.uid();
                
                -- Művelet típusa meghatározása
                IF TG_OP = 'INSERT' THEN
                    action_type := 'create';
                    resource_id := NEW.id;
                ELSIF TG_OP = 'UPDATE' THEN
                    action_type := 'update';
                    resource_id := NEW.id;
                ELSIF TG_OP = 'DELETE' THEN
                    action_type := 'delete';
                    resource_id := OLD.id;
                END IF;
                
                -- Resource típus meghatározása
                resource_type := TG_TABLE_NAME;
                
                -- Audit log beszúrása
                INSERT INTO audit_logs (
                    user_id, action, resource_type, resource_id,
                    details, severity, created_at
                ) VALUES (
                    user_uuid, action_type, resource_type, resource_id,
                    jsonb_build_object(
                        'table', TG_TABLE_NAME,
                        'operation', TG_OP,
                        'old_data', CASE WHEN TG_OP = 'UPDATE' OR TG_OP = 'DELETE' 
                                        THEN to_jsonb(OLD) ELSE '{}'::jsonb END,
                        'new_data', CASE WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' 
                                        THEN to_jsonb(NEW) ELSE '{}'::jsonb END
                    ),
                    'info', NOW()
                );
                
                RETURN COALESCE(NEW, OLD);
            END;
            $$;
            """
            
            self.supabase.execute_query(audit_function)
            logger.info("Audit trail funkciók sikeresen létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba az audit trail policy-k létrehozásakor: {e}")
            return False
    
    def create_all_policies(self) -> Dict[str, bool]:
        """Létrehozza az összes RLS policy-t"""
        results = {}
        
        results["users"] = self.create_users_policies()
        results["user_profiles"] = self.create_user_profiles_policies()
        results["user_preferences"] = self.create_user_preferences_policies()
        results["products"] = self.create_products_policies()
        results["orders"] = self.create_orders_policies()
        results["chat_sessions"] = self.create_chat_sessions_policies()
        results["chat_messages"] = self.create_chat_messages_policies()
        results["audit_logs"] = self.create_audit_logs_policies()
        results["user_consents"] = self.create_user_consents_policies()
        results["gdpr_compliance"] = self.create_gdpr_compliance_policies()
        results["audit_trail"] = self.create_audit_trail_policies()
        
        # Eredmények logolása
        for policy, success in results.items():
            if success:
                logger.info(f"✅ {policy} RLS policy-k sikeresen létrehozva")
            else:
                logger.error(f"❌ {policy} RLS policy-k létrehozása sikertelen")
        
        return results
    
    def validate_policies(self) -> Dict[str, Any]:
        """Validálja a RLS policy-ket"""
        tables = [
            "users", "user_profiles", "user_preferences", 
            "products", "orders", "chat_sessions", "chat_messages",
            "audit_logs", "user_consents"
        ]
        
        validation_results = {}
        
        for table in tables:
            try:
                # Policy-k lekérdezése
                query = """
                SELECT 
                    policyname,
                    permissive,
                    roles,
                    cmd,
                    qual,
                    with_check
                FROM pg_policies 
                WHERE tablename = %s;
                """
                
                policies = self.supabase.execute_query(query, {"tablename": table})
                
                validation_results[table] = {
                    "policies_count": len(policies),
                    "policies": policies,
                    "rls_enabled": self.supabase.check_rls_enabled(table)
                }
                
            except Exception as e:
                validation_results[table] = {
                    "error": str(e)
                }
        
        return validation_results 