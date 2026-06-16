import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.application.menu_management_use_case import MenuManagementUseCase
from src.core.dispatcher.core_types import CoreContext, ServiceResponse

logger = logging.getLogger("OmniCore.MenuManager")


class MenuManager:
    """
    Thin Delegate for Menu Management.
    Delegates all operations to MenuManagementUseCase.
    """

    def __init__(self):
        pass

    def get_all_menus(self, session: Session, context: CoreContext) -> ServiceResponse:
        return MenuManagementUseCase(session).list_menus()

    def get_menu_by_name(
        self, session: Session, context: CoreContext, name: str
    ) -> Optional[Dict[str, Any]]:
        return MenuManagementUseCase(session).get_menu_structure(name)


# Singleton
menu_manager = MenuManager()
