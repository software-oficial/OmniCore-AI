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

    def get_menu_structure(
        self, name: str, credential_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieves a full menu with its options."""
        return self.repo.get_flow_node(name, credential_id)

    def get_formatted_menu(
        self, name: str, credential_id: Optional[str] = None
    ) -> ServiceResponse:
        """Retrieves a menu and formats it for WhatsApp delivery."""
        menu = self.get_menu_structure(name, credential_id)
        if not menu:
            return ServiceResponse.error_res(f"Menu {name} not found", "MENU_NOT_FOUND")

        # In the new bot_flows table, options are stored as JSONB
        options = menu.get("options", [])
        if isinstance(options, str):
            import json

            try:
                options = json.loads(options)
            except (json.JSONDecodeError, TypeError):
                options = []

        options_list = [
            f"{i+1}. {opt.get('label', 'Sin etiqueta')}"
            for i, opt in enumerate(options)
        ]

        full_text = f"{menu.get('prompt', 'Menú')}\n\n{chr(10).join(options_list)}"
        return ServiceResponse.success_res(message=full_text)

    def list_menus(self, credential_id: str) -> ServiceResponse:
        try:
            menus = self.repo.list_all_nodes(credential_id)
            return ServiceResponse.success_res(data=menus, message="Menus retrieved.")
        except Exception as e:
            return ServiceResponse.error_res(f"Error: {str(e)}", "MENU_LIST_ERROR")
