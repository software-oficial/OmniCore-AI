import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command

logger = logging.getLogger("OmniCore.MenuManager")

class MenuManager:
    """
    Gestiona la estructura de menús dinámicos almacenados en la base de datos del tenant.
    """
    def __init__(self):
        self.logger = logging.getLogger("MenuManager")

    def get_all_menus(self, session: Session, context: CoreContext) -> ServiceResponse:
        """Recupera todos los menús configurados para el tenant."""
        try:
            menus = session.execute(text("SELECT * FROM bot_menus")).mappings().all()
            
            full_menus = []
            for m in menus:
                options = session.execute(
                    text("SELECT * FROM bot_menu_options WHERE menu_id = :id ORDER BY position ASC"), 
                    {"id": m['id']}
                ).mappings().all()
                m_dict = dict(m)
                m_dict['options'] = [dict(o) for o in options]
                full_menus.append(m_dict)
            
            return ServiceResponse.success_res(data=full_menus, message="Menus retrieved.")
        except Exception as e:
            self.logger.error(f"Error cargando menús: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "MENU_LOAD_ERROR")

    @command(
        name="whatsapp.bot.menu.get",
        description="Retrieves the structure of a specific menu by name.",
        params_schema={"menu_name": "string"}
    )
    def get_menu_by_name(self, session: Session, context: CoreContext, name: str) -> Optional[Dict[str, Any]]:
        """Busca un menú específico por su nombre."""

        try:
            menu = session.execute(
                text("SELECT * FROM bot_menus WHERE name ILIKE :name"), 
                {"name": name}
            ).mappings().first()
            
            if menu:
                options = session.execute(
                    text("SELECT * FROM bot_menu_options WHERE menu_id = :id ORDER BY position ASC"), 
                    {"id": menu['id']}
                ).mappings().all()
                menu_dict = dict(menu)
                menu_dict['options'] = [dict(o) for o in options]
                return menu_dict
            return None
        except Exception as e:
            self.logger.error(f"Error buscando menú {name}: {e}")
            return None

# Singleton
menu_manager = MenuManager()
