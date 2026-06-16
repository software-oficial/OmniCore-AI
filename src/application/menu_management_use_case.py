import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import ServiceResponse
from src.infrastructure.repositories.whatsapp_repository import WhatsappRepository

logger = logging.getLogger("OmniCore.MenuManagementUseCase")


class MenuManagementUseCase:
    """
    Application Layer: Manages the dynamic bot menu structures and navigation formatting.
    """

    def __init__(self, session: Session):
        self.repo = WhatsappRepository(session)

    def get_menu_structure(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a full menu with its options."""
        return self.repo.get_menu_by_name(name)

    def get_formatted_menu(self, name: str) -> ServiceResponse:
        """Retrieves a menu and formats it for WhatsApp delivery."""
        menu = self.get_menu_structure(name)
        if not menu:
            return ServiceResponse.error_res(f"Menu {name} not found", "MENU_NOT_FOUND")

        options = menu.get("options", [])
        options_list = [f"{i+1}. {opt['label']}" for i, opt in enumerate(options)]

        full_text = f"{menu['text']}\n\n{chr(10).join(options_list)}"
        return ServiceResponse.success_res(message=full_text)

    def list_menus(self) -> ServiceResponse:
        try:
            menus = self.repo.list_all_menus()
            return ServiceResponse.success_res(data=menus, message="Menus retrieved.")
        except Exception as e:
            return ServiceResponse.error_res(f"Error: {str(e)}", "MENU_LIST_ERROR")
