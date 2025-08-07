"""
Row Level Security (RLS) Optimization and Monitoring - Chatbuddy MVP.

Ez a modul implementálja a RLS performance optimalizálást és monitoring-ot
a Supabase hivatalos dokumentáció alapján.

Funkciók:
- Performance optimalizálás
- Index javaslatok
- Policy monitoring
- Performance metrikák
- Best practices ellenőrzés
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json

from src.config.logging import get_logger
from .supabase_client import SupabaseClient

logger = get_logger(__name__)


class RLSOptimizer:
    """RLS performance optimalizáló"""
    
    def __init__(self, supabase_client: SupabaseClient):
        """Inicializálja a RLS optimizert"""
        self.supabase = supabase_client
    
    def analyze_policy_performance(self) -> Dict[str, Any]:
        """Analizálja a RLS policy-k performance-át"""
        try:
            # Policy performance lekérdezése
            query = """
            SELECT 
                schemaname,
                tablename,
                policyname,
                permissive,
                roles,
                cmd,
                qual,
                with_check,
                pg_get_expr(qual, polrelid) as qual_expr,
                pg_get_expr(with_check, polrelid) as with_check_expr
            FROM pg_policies 
            WHERE schemaname = 'public'
            ORDER BY tablename, policyname;
            """
            
            policies = self.supabase.execute_query(query)
            
            analysis_results = {
                "total_policies": len(policies),
                "tables_with_policies": {},
                "performance_issues": [],
                "optimization_suggestions": [],
                "best_practices_violations": []
            }
            
            # Policy-k csoportosítása táblák szerint
            for policy in policies:
                table_name = policy["tablename"]
                if table_name not in analysis_results["tables_with_policies"]:
                    analysis_results["tables_with_policies"][table_name] = []
                
                analysis_results["tables_with_policies"][table_name].append(policy)
            
            # Performance analízis
            self._analyze_performance_issues(policies, analysis_results)
            
            # Optimization javaslatok
            self._generate_optimization_suggestions(policies, analysis_results)
            
            # Best practices ellenőrzés
            self._check_best_practices(policies, analysis_results)
            
            logger.info(f"RLS policy performance analízis elkészült: {len(policies)} policy")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Hiba a RLS policy performance analízis során: {e}")
            return {"error": str(e)}
    
    def _analyze_performance_issues(self, policies: List[Dict], analysis: Dict[str, Any]):
        """Analizálja a performance problémákat"""
        for policy in policies:
            qual_expr = policy.get("qual_expr", "")
            with_check_expr = policy.get("with_check_expr", "")
            
            # SELECT wrapper hiánya ellenőrzése
            if "auth.uid()" in qual_expr and "(select auth.uid())" not in qual_expr:
                analysis["performance_issues"].append({
                    "type": "missing_select_wrapper",
                    "policy": policy["policyname"],
                    "table": policy["tablename"],
                    "issue": "auth.uid() should be wrapped in (select auth.uid()) for better performance",
                    "severity": "medium"
                })
            
            # TO clause hiánya ellenőrzése
            if not policy.get("roles"):
                analysis["performance_issues"].append({
                    "type": "missing_to_clause",
                    "policy": policy["policyname"],
                    "table": policy["tablename"],
                    "issue": "Policy should specify TO clause for better performance",
                    "severity": "low"
                })
            
            # Komplex join-ok ellenőrzése
            if "JOIN" in qual_expr.upper() or "EXISTS" in qual_expr.upper():
                analysis["performance_issues"].append({
                    "type": "complex_join",
                    "policy": policy["policyname"],
                    "table": policy["tablename"],
                    "issue": "Complex joins in policies can impact performance",
                    "severity": "high"
                })
    
    def _generate_optimization_suggestions(self, policies: List[Dict], analysis: Dict[str, Any]):
        """Generál optimization javaslatokat"""
        # Index javaslatok
        index_suggestions = self._suggest_indexes(policies)
        analysis["optimization_suggestions"].extend(index_suggestions)
        
        # Policy optimalizálási javaslatok
        for policy in policies:
            qual_expr = policy.get("qual_expr", "")
            
            # SELECT wrapper javaslat
            if "auth.uid()" in qual_expr and "(select auth.uid())" not in qual_expr:
                analysis["optimization_suggestions"].append({
                    "type": "select_wrapper",
                    "policy": policy["policyname"],
                    "table": policy["tablename"],
                    "suggestion": "Wrap auth.uid() in (select auth.uid()) for better performance",
                    "impact": "high"
                })
            
            # TO clause javaslat
            if not policy.get("roles"):
                analysis["optimization_suggestions"].append({
                    "type": "to_clause",
                    "policy": policy["policyname"],
                    "table": policy["tablename"],
                    "suggestion": "Add TO clause to specify target roles",
                    "impact": "medium"
                })
    
    def _suggest_indexes(self, policies: List[Dict]) -> List[Dict]:
        """Javasol indexeket a policy-k alapján"""
        index_suggestions = []
        
        for policy in policies:
            qual_expr = policy.get("qual_expr", "")
            table_name = policy["tablename"]
            
            # user_id index javaslat
            if "user_id" in qual_expr:
                index_suggestions.append({
                    "type": "index_suggestion",
                    "table": table_name,
                    "column": "user_id",
                    "suggestion": f"CREATE INDEX idx_{table_name}_user_id ON {table_name}(user_id);",
                    "reason": "Policy uses user_id for filtering",
                    "impact": "high"
                })
            
            # role index javaslat
            if "role" in qual_expr:
                index_suggestions.append({
                    "type": "index_suggestion",
                    "table": table_name,
                    "column": "role",
                    "suggestion": f"CREATE INDEX idx_{table_name}_role ON {table_name}(role);",
                    "reason": "Policy uses role for filtering",
                    "impact": "medium"
                })
        
        return index_suggestions
    
    def _check_best_practices(self, policies: List[Dict], analysis: Dict[str, Any]):
        """Ellenőrzi a best practices-eket"""
        for policy in policies:
            # Túl sok permissive policy ellenőrzése
            table_name = policy["tablename"]
            table_policies = [p for p in policies if p["tablename"] == table_name]
            
            if len(table_policies) > 3:
                analysis["best_practices_violations"].append({
                    "type": "too_many_policies",
                    "table": table_name,
                    "issue": f"Table has {len(table_policies)} policies, consider consolidating",
                    "severity": "medium"
                })
            
            # Security definer funkciók javaslata
            qual_expr = policy.get("qual_expr", "")
            if "EXISTS" in qual_expr and "SELECT" in qual_expr:
                analysis["best_practices_violations"].append({
                    "type": "security_definer_suggestion",
                    "policy": policy["policyname"],
                    "table": table_name,
                    "issue": "Consider using security definer functions for complex policies",
                    "severity": "low"
                })


class RLSMonitor:
    """RLS monitoring és metrikák"""
    
    def __init__(self, supabase_client: SupabaseClient):
        """Inicializálja a RLS monitort"""
        self.supabase = supabase_client
    
    def get_rls_statistics(self) -> Dict[str, Any]:
        """Lekéri a RLS statisztikákat"""
        try:
            # RLS engedélyezett táblák
            rls_tables_query = """
            SELECT 
                schemaname,
                tablename,
                rowsecurity
            FROM pg_tables 
            WHERE schemaname = 'public' AND rowsecurity = true;
            """
            
            rls_tables = self.supabase.execute_query(rls_tables_query)
            
            # Policy statisztikák
            policy_stats_query = """
            SELECT 
                tablename,
                COUNT(*) as policy_count,
                COUNT(CASE WHEN cmd = 'SELECT' THEN 1 END) as select_policies,
                COUNT(CASE WHEN cmd = 'INSERT' THEN 1 END) as insert_policies,
                COUNT(CASE WHEN cmd = 'UPDATE' THEN 1 END) as update_policies,
                COUNT(CASE WHEN cmd = 'DELETE' THEN 1 END) as delete_policies,
                COUNT(CASE WHEN cmd = 'ALL' THEN 1 END) as all_policies
            FROM pg_policies 
            WHERE schemaname = 'public'
            GROUP BY tablename;
            """
            
            policy_stats = self.supabase.execute_query(policy_stats_query)
            
            # Performance metrikák
            performance_metrics = self._get_performance_metrics()
            
            statistics = {
                "rls_enabled_tables": len(rls_tables),
                "total_policies": sum(stat["policy_count"] for stat in policy_stats),
                "policy_distribution": {
                    "select": sum(stat["select_policies"] for stat in policy_stats),
                    "insert": sum(stat["insert_policies"] for stat in policy_stats),
                    "update": sum(stat["update_policies"] for stat in policy_stats),
                    "delete": sum(stat["delete_policies"] for stat in policy_stats),
                    "all": sum(stat["all_policies"] for stat in policy_stats)
                },
                "table_policy_counts": {
                    stat["tablename"]: stat["policy_count"] 
                    for stat in policy_stats
                },
                "performance_metrics": performance_metrics,
                "last_updated": datetime.now().isoformat()
            }
            
            logger.info(f"RLS statisztikák lekérdezve: {statistics['total_policies']} policy")
            return statistics
            
        except Exception as e:
            logger.error(f"Hiba a RLS statisztikák lekérdezése során: {e}")
            return {"error": str(e)}
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Lekéri a performance metrikákat"""
        try:
            # Query performance metrikák
            performance_query = """
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                rows
            FROM pg_stat_statements 
            WHERE query LIKE '%auth.uid()%' OR query LIKE '%RLS%'
            ORDER BY total_time DESC
            LIMIT 10;
            """
            
            # Megjegyzés: pg_stat_statements extension szükséges lehet
            performance_data = self.supabase.execute_query(performance_query)
            
            return {
                "slow_queries": len(performance_data),
                "total_calls": sum(row.get("calls", 0) for row in performance_data),
                "total_time": sum(row.get("total_time", 0) for row in performance_data),
                "avg_time": sum(row.get("mean_time", 0) for row in performance_data) / len(performance_data) if performance_data else 0
            }
            
        except Exception as e:
            logger.warning(f"Performance metrikák lekérdezése sikertelen: {e}")
            return {"error": "Performance metrics not available"}
    
    def generate_rls_report(self) -> Dict[str, Any]:
        """Generál egy átfogó RLS jelentést"""
        try:
            # Statisztikák
            statistics = self.get_rls_statistics()
            
            # Performance analízis
            optimizer = RLSOptimizer(self.supabase)
            performance_analysis = optimizer.analyze_policy_performance()
            
            # Jelentés összeállítása
            report = {
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_tables_with_rls": statistics.get("rls_enabled_tables", 0),
                    "total_policies": statistics.get("total_policies", 0),
                    "performance_issues": len(performance_analysis.get("performance_issues", [])),
                    "optimization_suggestions": len(performance_analysis.get("optimization_suggestions", [])),
                    "best_practices_violations": len(performance_analysis.get("best_practices_violations", []))
                },
                "statistics": statistics,
                "performance_analysis": performance_analysis,
                "recommendations": self._generate_recommendations(statistics, performance_analysis)
            }
            
            logger.info("RLS jelentés generálva")
            return report
            
        except Exception as e:
            logger.error(f"Hiba a RLS jelentés generálása során: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, statistics: Dict, analysis: Dict) -> List[Dict]:
        """Generál ajánlásokat a statisztikák alapján"""
        recommendations = []
        
        # Policy szám ajánlások
        total_policies = statistics.get("total_policies", 0)
        if total_policies > 50:
            recommendations.append({
                "type": "policy_count",
                "priority": "medium",
                "title": "Túl sok RLS policy",
                "description": f"Jelenleg {total_policies} policy van. Fontold meg a konszolidációt.",
                "action": "Review and consolidate policies where possible"
            })
        
        # Performance ajánlások
        performance_issues = analysis.get("performance_issues", [])
        high_severity_issues = [issue for issue in performance_issues if issue.get("severity") == "high"]
        
        if high_severity_issues:
            recommendations.append({
                "type": "performance",
                "priority": "high",
                "title": "Kritikus performance problémák",
                "description": f"{len(high_severity_issues)} kritikus performance probléma található.",
                "action": "Address high severity performance issues immediately"
            })
        
        # Index ajánlások
        index_suggestions = analysis.get("optimization_suggestions", [])
        index_suggestions = [s for s in index_suggestions if s.get("type") == "index_suggestion"]
        
        if index_suggestions:
            recommendations.append({
                "type": "indexes",
                "priority": "medium",
                "title": "Index javaslatok",
                "description": f"{len(index_suggestions)} index javaslat a performance javításához.",
                "action": "Review and implement suggested indexes"
            })
        
        return recommendations


class RLSHealthChecker:
    """RLS health check és validáció"""
    
    def __init__(self, supabase_client: SupabaseClient):
        """Inicializálja a RLS health checkert"""
        self.supabase = supabase_client
    
    def check_rls_health(self) -> Dict[str, Any]:
        """Ellenőrzi a RLS health állapotát"""
        try:
            health_checks = {
                "rls_enabled_tables": self._check_rls_enabled_tables(),
                "policy_coverage": self._check_policy_coverage(),
                "security_coverage": self._check_security_coverage(),
                "performance_health": self._check_performance_health(),
                "gdpr_compliance": self._check_gdpr_compliance()
            }
            
            # Összesített health score
            total_checks = len(health_checks)
            passed_checks = sum(1 for check in health_checks.values() if check.get("status") == "healthy")
            health_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            
            health_status = {
                "overall_status": "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical",
                "health_score": round(health_score, 2),
                "checks": health_checks,
                "last_checked": datetime.now().isoformat()
            }
            
            logger.info(f"RLS health check elkészült: {health_score}%")
            return health_status
            
        except Exception as e:
            logger.error(f"Hiba a RLS health check során: {e}")
            return {"error": str(e)}
    
    def _check_rls_enabled_tables(self) -> Dict[str, Any]:
        """Ellenőrzi a RLS engedélyezett táblákat"""
        try:
            query = """
            SELECT COUNT(*) as rls_tables
            FROM pg_tables 
            WHERE schemaname = 'public' AND rowsecurity = true;
            """
            
            result = self.supabase.execute_query(query)
            rls_tables = result[0]["rls_tables"] if result else 0
            
            # Összes tábla számának lekérdezése
            total_query = """
            SELECT COUNT(*) as total_tables
            FROM pg_tables 
            WHERE schemaname = 'public';
            """
            
            total_result = self.supabase.execute_query(total_query)
            total_tables = total_result[0]["total_tables"] if total_result else 0
            
            coverage = (rls_tables / total_tables) * 100 if total_tables > 0 else 0
            
            return {
                "status": "healthy" if coverage >= 90 else "warning" if coverage >= 70 else "critical",
                "rls_tables": rls_tables,
                "total_tables": total_tables,
                "coverage_percentage": round(coverage, 2),
                "message": f"{rls_tables}/{total_tables} táblánál engedélyezett a RLS"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _check_policy_coverage(self) -> Dict[str, Any]:
        """Ellenőrzi a policy lefedettséget"""
        try:
            query = """
            SELECT 
                t.tablename,
                COUNT(p.policyname) as policy_count
            FROM pg_tables t
            LEFT JOIN pg_policies p ON t.tablename = p.tablename AND p.schemaname = 'public'
            WHERE t.schemaname = 'public' AND t.rowsecurity = true
            GROUP BY t.tablename;
            """
            
            results = self.supabase.execute_query(query)
            
            tables_without_policies = [row for row in results if row["policy_count"] == 0]
            tables_with_policies = [row for row in results if row["policy_count"] > 0]
            
            coverage = (len(tables_with_policies) / len(results)) * 100 if results else 0
            
            return {
                "status": "healthy" if coverage >= 95 else "warning" if coverage >= 80 else "critical",
                "tables_with_policies": len(tables_with_policies),
                "tables_without_policies": len(tables_without_policies),
                "coverage_percentage": round(coverage, 2),
                "message": f"{len(tables_with_policies)}/{len(results)} táblánál vannak policy-k"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _check_security_coverage(self) -> Dict[str, Any]:
        """Ellenőrzi a biztonsági lefedettséget"""
        try:
            query = """
            SELECT 
                cmd,
                COUNT(*) as count
            FROM pg_policies 
            WHERE schemaname = 'public'
            GROUP BY cmd;
            """
            
            results = self.supabase.execute_query(query)
            
            policy_types = {row["cmd"]: row["count"] for row in results}
            
            # Ellenőrizzük a kritikus műveletek védelmét
            has_select = policy_types.get("SELECT", 0) > 0
            has_insert = policy_types.get("INSERT", 0) > 0
            has_update = policy_types.get("UPDATE", 0) > 0
            has_delete = policy_types.get("DELETE", 0) > 0
            
            critical_operations_covered = all([has_select, has_insert, has_update, has_delete])
            
            return {
                "status": "healthy" if critical_operations_covered else "warning",
                "select_policies": has_select,
                "insert_policies": has_insert,
                "update_policies": has_update,
                "delete_policies": has_delete,
                "critical_operations_covered": critical_operations_covered,
                "message": "Kritikus műveletek védelme ellenőrizve"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _check_performance_health(self) -> Dict[str, Any]:
        """Ellenőrzi a performance health-et"""
        try:
            # SELECT wrapper használat ellenőrzése
            query = """
            SELECT COUNT(*) as total_policies,
                   COUNT(CASE WHEN qual LIKE '%(select auth.uid())%' THEN 1 END) as optimized_policies
            FROM pg_policies 
            WHERE schemaname = 'public' AND qual LIKE '%auth.uid()%';
            """
            
            result = self.supabase.execute_query(query)
            if result:
                total = result[0]["total_policies"]
                optimized = result[0]["optimized_policies"]
                optimization_rate = (optimized / total) * 100 if total > 0 else 0
                
                return {
                    "status": "healthy" if optimization_rate >= 80 else "warning" if optimization_rate >= 50 else "critical",
                    "total_policies": total,
                    "optimized_policies": optimized,
                    "optimization_rate": round(optimization_rate, 2),
                    "message": f"{optimized}/{total} policy optimalizált"
                }
            
            return {"status": "healthy", "message": "Nincs optimalizálási adat"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _check_gdpr_compliance(self) -> Dict[str, Any]:
        """Ellenőrzi a GDPR compliance-t"""
        try:
            # GDPR funkciók ellenőrzése
            query = """
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_schema = 'public' 
            AND routine_name LIKE '%delete%user%data%';
            """
            
            gdpr_functions = self.supabase.execute_query(query)
            
            # User consents tábla ellenőrzése
            consent_query = """
            SELECT COUNT(*) as consent_count
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'user_consents';
            """
            
            consent_result = self.supabase.execute_query(consent_query)
            has_consent_table = consent_result[0]["consent_count"] > 0 if consent_result else False
            
            gdpr_compliant = len(gdpr_functions) > 0 and has_consent_table
            
            return {
                "status": "healthy" if gdpr_compliant else "warning",
                "gdpr_functions": len(gdpr_functions),
                "has_consent_table": has_consent_table,
                "gdpr_compliant": gdpr_compliant,
                "message": "GDPR compliance ellenőrizve"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)} 