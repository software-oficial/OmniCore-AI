import logging
from typing import Dict, Any, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
from core.dispatcher.core_types import CoreContext, ServiceResponse
from infra.db.core_db_manager import core_db_manager
from infra.cache.redis_manager import cache_manager

logger = logging.getLogger("OmniCore.Governance")

class GovernanceService:
    """
    OmniCore-AI Governance Engine.
    Implements Dynamic Governance: Tiers and Permissions are resolved 
    from the Core DB with Redis caching for high performance.
    """
    def __init__(self):
        # Cache for tiers hierarchy to avoid frequent DB hits
        self._tier_hierarchy_cache: Dict[str, int] = {}

    def _get_tier_level(self, tier_name: str) -> int:
        """Resolves the numeric level of a tier from cache or DB."""
        tier_name = tier_name.upper()
        if tier_name in self._tier_hierarchy_cache:
            return self._tier_hierarchy_cache[tier_name]
        
        try:
            result = core_db_manager.execute_raw(
                "SELECT level FROM governance_tiers WHERE tier_name = :name", 
                {"name": tier_name}
            ).scalar()
            
            level = result if result is not None else 1
            self._tier_hierarchy_cache[tier_name] = level
            return level
        except Exception as e:
            logger.error(f"Error fetching tier level for {tier_name}: {e}")
            return 1

    def _get_command_metadata(self, command_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves command requirements from Core DB with Redis caching."""
        cache_key = f"gov:cmd:{command_name}"
        cached = cache_manager.get_session_context(cache_key) # Reuse session_context helper or add generic get
        if cached:
            return cached

        try:
            result = core_db_manager.execute_raw(
                "SELECT permission_key, min_tier FROM governance_commands WHERE command_name = :cmd", 
                {"cmd": command_name}
            ).mappings().first()
            
            if not result:
                return None
            
            meta = {"permission": result.permission_key, "tier": result.min_tier}
            cache_manager.set_session_context(cache_key, meta, ttl=3600)
            return meta
        except Exception as e:
            logger.error(f"Error fetching command metadata for {command_name}: {e}")
            return None

    def validate_access(self, command_name: str, context: CoreContext, session: Session) -> Tuple[bool, Optional[ServiceResponse]]:
        """
        Runs the full governance pipeline.
        Returns (is_allowed, optional_error_response).
        """
        meta = self._get_command_metadata(command_name)
        if not meta:
            logger.warning(f"Command {command_name} has no defined governance metadata. Allowing by default.")
            return True, None

        # 1. SaaS Tier Validation
        tier_ok, tier_res = self._check_tier(context, meta["tier"])
        if not tier_ok: return False, tier_res

        # 2. PBAC Permission Validation
        perm_ok, perm_res = self._check_permission(context, meta["permission"], session)
        if not perm_ok: return False, perm_res

        # 3. Entity Restriction (Still hardcoded for critical system commands)
        entity_ok, entity_res = self._check_entity(command_name, context.entity)
        if not entity_ok: return False, entity_res

        return True, None

    def _check_tier(self, context: CoreContext, required_tier: str) -> Tuple[bool, Optional[ServiceResponse]]:
        current_tier = context.tier.upper()
        required_level = self._get_tier_level(required_tier)
        current_level = self._get_tier_level(current_tier)
        
        if current_level < required_level:
            return False, ServiceResponse.error_res(
                f"Your current plan ({current_tier}) does not include this feature. Required: {required_tier}", 
                "TIER_ACCESS_DENIED"
            )
        return True, None

    def _check_permission(self, context: CoreContext, permission_key: str, session: Session) -> Tuple[bool, Optional[ServiceResponse]]:
        if not permission_key:
            return True, None

        # MASTER role bypasses all checks
        user_query = text("SELECT role FROM users WHERE id = :user_id")
        user = session.execute(user_query, {"user_id": context.user_id}).mappings().first()
        
        if user and user['role'] and user['role'].upper() == 'MASTER':
            return True, None

        # Check roles mapping in external DB
        perm_query = text("""
            SELECT 1 FROM user_roles ur
            JOIN role_permissions rp ON ur.role_id = rp.role_id
            WHERE ur.user_id = :user_id AND rp.permission_key = :perm
        """)
        if session.execute(perm_query, {"user_id": context.user_id, "perm": permission_key}).scalar():
            return True, None

        # Check direct permissions
        direct_query = text("""
            SELECT granted FROM permissions 
            WHERE tenant_id = :tid AND user_id = :uid AND permission_key = :perm
        """)
        res = session.execute(direct_query, {"tid": context.app_id, "uid": context.user_id, "perm": permission_key}).mappings().first()
        if res and res['granted']:
            return True, None

        return False, ServiceResponse.error_res(
            f"Insufficient permissions for: {permission_key}", 
            "USER_PERMISSION_DENIED"
        )

    def _check_entity(self, command_name: str, entity: str) -> Tuple[bool, Optional[ServiceResponse]]:
        # Critical system restrictions remain hardcoded for safety
        restrictions = {
            "cash.close": ["WEB", "CLI", "API"], 
            "system.config": ["CLI", "API"],
            "system.reboot": ["CLI", "API"],
        }
        allowed_entities = restrictions.get(command_name)
        if allowed_entities and entity not in allowed_entities:
            return False, ServiceResponse.error_res(
                f"Command {command_name} cannot be executed from interface {entity}", 
                "ENTITY_RESTRICTION"
            )
        return True, None

# Singleton
governance_service = GovernanceService()
