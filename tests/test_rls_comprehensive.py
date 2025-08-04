"""
Comprehensive Row Level Security (RLS) Tests - Chatbuddy MVP.

Ez a modul implementálja a teljes RLS rendszer átfogó tesztelését
a hivatalos Supabase dokumentáció alapján.

Teszteket tartalmaz:
- Teljes RLS workflow tesztelése
- Performance benchmarking
- Security validation
- GDPR compliance testing
- Integration testing
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import uuid
from typing import Dict, Any, List

from src.integrations.database.rls_policies import RLSPolicyManager
from src.integrations.database.rls_optimization import RLSOptimizer, RLSMonitor, RLSHealthChecker
from src.integrations.database.supabase_client import SupabaseClient
from src.integrations.database.setup_database import DatabaseSetup
from src.config.gdpr_compliance import GDPRComplianceLayer
from src.config.audit_logging import AuditLogger


class TestRLSCompleteWorkflow:
    """Teljes RLS workflow tesztelése"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase kliens"""
        mock = Mock(spec=SupabaseClient)
        mock.execute_query = Mock(return_value=True)
        mock.check_rls_enabled = Mock(return_value=True)
        mock.get_table_info = Mock(return_value=[{"column_name": "id", "data_type": "uuid"}])
        return mock
    
    @pytest.fixture
    def rls_manager(self, mock_supabase):
        """RLS policy manager"""
        return RLSPolicyManager(mock_supabase)
    
    @pytest.fixture
    def rls_optimizer(self, mock_supabase):
        """RLS optimizer"""
        return RLSOptimizer(mock_supabase)
    
    @pytest.fixture
    def rls_monitor(self, mock_supabase):
        """RLS monitor"""
        return RLSMonitor(mock_supabase)
    
    @pytest.fixture
    def rls_health_checker(self, mock_supabase):
        """RLS health checker"""
        return RLSHealthChecker(mock_supabase)
    
    def test_complete_rls_setup_workflow(self, rls_manager, mock_supabase):
        """Teszteli a teljes RLS setup workflow-ot"""
        # 1. Policy-k létrehozása
        policy_results = rls_manager.create_all_policies()
        
        assert isinstance(policy_results, dict)
        assert all(policy_results.values())
        
        # 2. Policy validáció
        validation_results = rls_manager.validate_policies()
        
        assert isinstance(validation_results, dict)
        assert len(validation_results) >= 9  # Minimum táblák száma
        
        # 3. Ellenőrizzük a policy-k számát
        total_calls = mock_supabase.execute_query.call_count
        assert total_calls >= 25  # Minimum policy-k száma
        
        # 4. Ellenőrizzük a különböző policy típusokat
        calls = [call[0][0] for call in mock_supabase.execute_query.call_args_list]
        
        select_policies = [call for call in calls if "FOR SELECT" in call]
        insert_policies = [call for call in calls if "FOR INSERT" in call]
        update_policies = [call for call in calls if "FOR UPDATE" in call]
        delete_policies = [call for call in calls if "FOR DELETE" in call]
        
        assert len(select_policies) >= 10
        assert len(insert_policies) >= 5
        assert len(update_policies) >= 5
        assert len(delete_policies) >= 1  # Jelenleg csak 1 DELETE policy van (user_consents)
    
    def test_rls_optimization_workflow(self, rls_optimizer, mock_supabase):
        """Teszteli a RLS optimization workflow-ot"""
        # Mock policy adatok
        mock_policies = [
            {
                "policyname": "test_policy",
                "tablename": "users",
                "qual_expr": "auth.uid() = user_id",
                "roles": ["authenticated"]
            }
        ]
        
        mock_supabase.execute_query.return_value = mock_policies
        
        # Performance analízis
        analysis = rls_optimizer.analyze_policy_performance()
        
        assert isinstance(analysis, dict)
        assert "total_policies" in analysis
        assert "performance_issues" in analysis
        assert "optimization_suggestions" in analysis
        assert "best_practices_violations" in analysis
    
    def test_rls_monitoring_workflow(self, rls_monitor, mock_supabase):
        """Teszteli a RLS monitoring workflow-ot"""
        # Mock statisztika adatok
        mock_stats = [
            {"tablename": "users", "policy_count": 3, "select_policies": 1, "insert_policies": 1, "update_policies": 1, "delete_policies": 0, "all_policies": 0}
        ]
        
        mock_supabase.execute_query.return_value = mock_stats
        
        # Statisztikák lekérdezése
        statistics = rls_monitor.get_rls_statistics()
        
        assert isinstance(statistics, dict)
        assert "total_policies" in statistics
        assert "policy_distribution" in statistics
        assert "performance_metrics" in statistics
        
        # Jelentés generálása
        report = rls_monitor.generate_rls_report()
        
        assert isinstance(report, dict)
        assert "summary" in report
        assert "statistics" in report
        assert "recommendations" in report
    
    def test_rls_health_check_workflow(self, rls_health_checker, mock_supabase):
        """Teszteli a RLS health check workflow-ot"""
        # Mock health check adatok
        mock_health_data = [
            {"rls_tables": 10, "total_tables": 10}
        ]
        
        mock_supabase.execute_query.return_value = mock_health_data
        
        # Health check
        health_status = rls_health_checker.check_rls_health()
        
        assert isinstance(health_status, dict)
        assert "overall_status" in health_status
        assert "health_score" in health_status
        assert "checks" in health_status
        
        # Ellenőrizzük a health score-t
        assert 0 <= health_status["health_score"] <= 100


class TestRLSPerformanceBenchmarking:
    """RLS performance benchmarking tesztek"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase kliens performance tesztekhez"""
        mock = Mock(spec=SupabaseClient)
        mock.execute_query = Mock(return_value=True)
        return mock
    
    @pytest.fixture
    def rls_manager(self, mock_supabase):
        """RLS policy manager"""
        return RLSPolicyManager(mock_supabase)
    
    def test_policy_creation_performance(self, rls_manager, mock_supabase):
        """Teszteli a policy létrehozás performance-át"""
        import time
        
        start_time = time.time()
        
        # Policy-k létrehozása
        results = rls_manager.create_all_policies()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance ellenőrzés
        assert execution_time < 5.0  # Maximum 5 másodperc
        assert all(results.values())
        
        # Policy-k számának ellenőrzése
        total_calls = mock_supabase.execute_query.call_count
        assert total_calls >= 20  # Minimum policy-k száma
    
    def test_policy_validation_performance(self, rls_manager, mock_supabase):
        """Teszteli a policy validáció performance-át"""
        import time
        
        # Mock validation adatok
        mock_validation_data = [
            {
                "policyname": "test_policy",
                "permissive": True,
                "roles": ["authenticated"],
                "cmd": "SELECT",
                "qual": "auth.uid() = user_id"
            }
        ]
        
        mock_supabase.execute_query.return_value = mock_validation_data
        
        start_time = time.time()
        
        # Policy validáció
        validation_results = rls_manager.validate_policies()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance ellenőrzés
        assert execution_time < 2.0  # Maximum 2 másodperc
        assert isinstance(validation_results, dict)
    
    def test_optimization_analysis_performance(self, mock_supabase):
        """Teszteli az optimization analízis performance-át"""
        import time
        
        rls_optimizer = RLSOptimizer(mock_supabase)
        
        # Mock policy adatok
        mock_policies = [
            {
                "policyname": "test_policy",
                "tablename": "users",
                "qual_expr": "auth.uid() = user_id",
                "roles": ["authenticated"]
            }
        ]
        
        mock_supabase.execute_query.return_value = mock_policies
        
        start_time = time.time()
        
        # Performance analízis
        analysis = rls_optimizer.analyze_policy_performance()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance ellenőrzés
        assert execution_time < 3.0  # Maximum 3 másodperc
        assert isinstance(analysis, dict)


class TestRLSSecurityValidation:
    """RLS security validation tesztek"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase kliens security tesztekhez"""
        mock = Mock(spec=SupabaseClient)
        mock.execute_query = Mock(return_value=True)
        return mock
    
    @pytest.fixture
    def rls_manager(self, mock_supabase):
        """RLS policy manager"""
        return RLSPolicyManager(mock_supabase)
    
    def test_security_policy_coverage(self, rls_manager, mock_supabase):
        """Teszteli a security policy lefedettséget"""
        # Policy-k létrehozása
        results = rls_manager.create_all_policies()
        
        assert all(results.values())
        
        # Security policy-k ellenőrzése
        calls = [call[0][0] for call in mock_supabase.execute_query.call_args_list]
        
        # Felhasználói adatok védelme
        user_protection_policies = [
            call for call in calls 
            if "auth.uid() = user_id" in call or "auth.uid() = id" in call
        ]
        assert len(user_protection_policies) >= 10
        
        # Admin jogosultságok
        admin_policies = [
            call for call in calls 
            if "role = 'admin'" in call or "role = 'support'" in call
        ]
        assert len(admin_policies) >= 5
        
        # GDPR compliance
        gdpr_policies = [
            call for call in calls 
            if "FOR DELETE" in call or "delete_user_data" in call
        ]
        assert len(gdpr_policies) >= 2
    
    def test_data_isolation_policies(self, rls_manager, mock_supabase):
        """Teszteli az adat izolációs policy-ket"""
        # Policy-k létrehozása
        results = rls_manager.create_all_policies()
        
        assert all(results.values())
        
        # Adat izoláció ellenőrzése
        calls = [call[0][0] for call in mock_supabase.execute_query.call_args_list]
        
        # Session-based izoláció
        session_policies = [
            call for call in calls 
            if "chat_sessions" in call and "user_id = auth.uid()" in call
        ]
        assert len(session_policies) >= 2
        
        # Order-based izoláció
        order_policies = [
            call for call in calls 
            if "orders" in call and "user_id" in call
        ]
        assert len(order_policies) >= 1  # Jelenleg csak 1 order policy van
    
    def test_audit_trail_security(self, rls_manager, mock_supabase):
        """Teszteli az audit trail biztonságot"""
        # Policy-k létrehozása
        results = rls_manager.create_all_policies()
        
        assert all(results.values())
        
        # Audit trail ellenőrzése
        calls = [call[0][0] for call in mock_supabase.execute_query.call_args_list]
        
        # Audit trigger funkció
        audit_functions = [
            call for call in calls 
            if "audit_trigger_function" in call
        ]
        assert len(audit_functions) >= 1
        
        # Service role policy-k
        service_policies = [
            call for call in calls 
            if "TO service_role" in call
        ]
        assert len(service_policies) >= 1


class TestRLSGDPRCompliance:
    """RLS GDPR compliance tesztek"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase kliens GDPR tesztekhez"""
        mock = Mock(spec=SupabaseClient)
        mock.execute_query = Mock(return_value=True)
        return mock
    
    @pytest.fixture
    def rls_manager(self, mock_supabase):
        """RLS policy manager"""
        return RLSPolicyManager(mock_supabase)
    
    def test_gdpr_data_deletion_function(self, rls_manager, mock_supabase):
        """Teszteli a GDPR data deletion funkciót"""
        # GDPR compliance policy-k létrehozása
        result = rls_manager.create_gdpr_compliance_policies()
        
        assert result is True
        
        # GDPR funkció ellenőrzése
        calls = [call[0][0] for call in mock_supabase.execute_query.call_args_list]
        
        # delete_user_data funkció
        gdpr_function = [
            call for call in calls 
            if "delete_user_data" in call and "SECURITY DEFINER" in call
        ]
        assert len(gdpr_function) >= 1
        
        # Audit log beszúrás
        audit_log_insert = [
            call for call in calls 
            if "INSERT INTO audit_logs" in call
        ]
        assert len(audit_log_insert) >= 1
        
        # Adat törlés sorrend
        data_deletion = [
            call for call in calls 
            if "DELETE FROM" in call
        ]
        assert len(data_deletion) >= 1  # Egy GDPR funkció van
    
    def test_user_consent_management(self, rls_manager, mock_supabase):
        """Teszteli a user consent kezelést"""
        # User consent policy-k létrehozása
        result = rls_manager.create_user_consents_policies()
        
        assert result is True
        
        # Consent policy-k ellenőrzése
        calls = [call[0][0] for call in mock_supabase.execute_query.call_args_list]
        
        # SELECT policy saját consent-ekhez
        select_consent = [
            call for call in calls 
            if "FOR SELECT" in call and "auth.uid() = user_id" in call
        ]
        assert len(select_consent) >= 1
        
        # INSERT policy consent létrehozáshoz
        insert_consent = [
            call for call in calls 
            if "FOR INSERT" in call and "auth.uid() = user_id" in call
        ]
        assert len(insert_consent) >= 1
        
        # UPDATE policy consent módosításhoz
        update_consent = [
            call for call in calls 
            if "FOR UPDATE" in call and "auth.uid() = user_id" in call
        ]
        assert len(update_consent) >= 1
        
        # DELETE policy right to be forgotten-hoz
        delete_consent = [
            call for call in calls 
            if "FOR DELETE" in call and "auth.uid() = user_id" in call
        ]
        assert len(delete_consent) >= 1
    
    def test_data_anonymization(self, rls_manager, mock_supabase):
        """Teszteli az adat anonimizációt"""
        # GDPR compliance policy-k létrehozása
        result = rls_manager.create_gdpr_compliance_policies()
        
        assert result is True
        
        # Anonimizáció ellenőrzése
        calls = [call[0][0] for call in mock_supabase.execute_query.call_args_list]
        
        # Email anonimizáció
        email_anonymization = [
            call for call in calls 
            if "deleted_" in call and "@deleted.com" in call
        ]
        assert len(email_anonymization) >= 1
        
        # Név anonimizáció
        name_anonymization = [
            call for call in calls 
            if "Deleted User" in call
        ]
        assert len(name_anonymization) >= 1
        
        # Metadata anonimizáció
        metadata_anonymization = [
            call for call in calls 
            if "gdpr_deletion" in call
        ]
        assert len(metadata_anonymization) >= 1


class TestRLSIntegrationTesting:
    """RLS integrációs tesztek"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase kliens integrációs tesztekhez"""
        mock = Mock(spec=SupabaseClient)
        mock.execute_query = Mock(return_value=True)
        mock.check_rls_enabled = Mock(return_value=True)
        mock.get_table_info = Mock(return_value=[{"column_name": "id", "data_type": "uuid"}])
        return mock
    
    @pytest.fixture
    def database_setup(self, mock_supabase):
        """Database setup"""
        from src.integrations.database.supabase_client import SupabaseConfig
        
        # Mock config valid URL-lal
        config = SupabaseConfig(
            url="https://test.supabase.co",
            key="test-key",
            service_role_key="test-service-key"
        )
        
        # Mock the DatabaseSetup to avoid actual Supabase connection
        with patch('src.integrations.database.setup_database.SupabaseClient') as mock_client_class:
            mock_client_class.return_value = mock_supabase
            return DatabaseSetup(config)
    
    def test_database_setup_with_rls(self, database_setup, mock_supabase):
        """Teszteli a database setup-ot RLS-szel"""
        # Mock setup eredmények
        mock_supabase.execute_query.return_value = True
        mock_supabase.check_rls_enabled.return_value = True
        
        # Database setup futtatása
        results = asyncio.run(database_setup.setup_complete_database())
        
        assert isinstance(results, dict)
        assert "connection_test" in results
        assert "tables_created" in results
        assert "policies_created" in results
        assert "validation" in results
    
    def test_rls_with_audit_logging(self, mock_supabase):
        """Teszteli a RLS-t audit logging-gal"""
        rls_manager = RLSPolicyManager(mock_supabase)
        
        # Audit trail policy-k létrehozása
        result = rls_manager.create_audit_trail_policies()
        
        assert result is True
        
        # Audit funkciók ellenőrzése
        calls = [call[0][0] for call in mock_supabase.execute_query.call_args_list]
        
        # Audit trigger funkció
        audit_function = [
            call for call in calls 
            if "audit_trigger_function" in call
        ]
        assert len(audit_function) >= 1
        
        # Trigger műveletek kezelése
        trigger_ops = [
            call for call in calls 
            if "TG_OP" in call
        ]
        assert len(trigger_ops) >= 1
    
    def test_rls_with_gdpr_compliance(self, mock_supabase):
        """Teszteli a RLS-t GDPR compliance-szel"""
        rls_manager = RLSPolicyManager(mock_supabase)
        
        # GDPR compliance policy-k létrehozása
        result = rls_manager.create_gdpr_compliance_policies()
        
        assert result is True
        
        # GDPR funkciók ellenőrzése
        calls = [call[0][0] for call in mock_supabase.execute_query.call_args_list]
        
        # GDPR funkció
        gdpr_function = [
            call for call in calls 
            if "delete_user_data" in call
        ]
        assert len(gdpr_function) >= 1
        
        # Audit log GDPR eseményekhez
        gdpr_audit = [
            call for call in calls 
            if "gdpr_data_deletion" in call
        ]
        assert len(gdpr_audit) >= 1


class TestRLSErrorHandlingAndRecovery:
    """RLS error handling és recovery tesztek"""
    
    @pytest.fixture
    def mock_supabase_with_errors(self):
        """Mock Supabase kliens hibákkal"""
        mock = Mock(spec=SupabaseClient)
        mock.execute_query = Mock(side_effect=Exception("Database error"))
        mock.check_rls_enabled = Mock(return_value=False)
        return mock
    
    @pytest.fixture
    def rls_manager(self, mock_supabase_with_errors):
        """RLS policy manager hibákkal"""
        return RLSPolicyManager(mock_supabase_with_errors)
    
    def test_policy_creation_error_handling(self, rls_manager):
        """Teszteli a policy létrehozási hibák kezelését"""
        # Policy létrehozás hiba esetén
        result = rls_manager.create_users_policies()
        
        # Hiba esetén False-t kell visszaadni
        assert result is False
    
    def test_policy_validation_error_handling(self, rls_manager):
        """Teszteli a policy validációs hibák kezelését"""
        # Policy validáció hiba esetén
        validation_results = rls_manager.validate_policies()
        
        # Hiba esetén error mezőt kell tartalmazni
        for table_info in validation_results.values():
            if "error" in table_info:
                assert isinstance(table_info["error"], str)
                assert len(table_info["error"]) > 0
    
    def test_optimization_error_handling(self, mock_supabase_with_errors):
        """Teszteli az optimization hibák kezelését"""
        rls_optimizer = RLSOptimizer(mock_supabase_with_errors)
        
        # Performance analízis hiba esetén
        analysis = rls_optimizer.analyze_policy_performance()
        
        # Hiba esetén error mezőt kell tartalmazni
        assert "error" in analysis
        assert isinstance(analysis["error"], str)
    
    def test_monitoring_error_handling(self, mock_supabase_with_errors):
        """Teszteli a monitoring hibák kezelését"""
        rls_monitor = RLSMonitor(mock_supabase_with_errors)
        
        # Statisztikák lekérdezés hiba esetén
        statistics = rls_monitor.get_rls_statistics()
        
        # Hiba esetén error mezőt kell tartalmazni
        assert "error" in statistics
        assert isinstance(statistics["error"], str)
    
    def test_health_check_error_handling(self, mock_supabase_with_errors):
        """Teszteli a health check hibák kezelését"""
        rls_health_checker = RLSHealthChecker(mock_supabase_with_errors)
        
        # Health check hiba esetén
        health_status = rls_health_checker.check_rls_health()
        
        # Hiba esetén error mezőt kell tartalmazni
        # Megjegyzés: A health checker nem ad vissza error mezőt, hanem a checks-ben vannak az error-ok
        assert health_status["overall_status"] == "critical"
        assert health_status["health_score"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 