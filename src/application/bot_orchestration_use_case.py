import logging

from sqlalchemy.orm import Session

from src.application.conversation_management_use_case import (
    ConversationManagementUseCase,
)
from src.application.menu_management_use_case import MenuManagementUseCase
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.infrastructure.repositories.whatsapp_repository import WhatsappRepository

logger = logging.getLogger("OmniCore.BotOrchestrationUseCase")


class BotOrchestrationUseCase:
    """
    Application Layer: The Brain. Orchestrates message processing and response determination.
    """

    def __init__(self, session: Session):
        self.repo = WhatsappRepository(session)
        self.conv_mgmt = ConversationManagementUseCase(session)
        self.menu_mgmt = MenuManagementUseCase(session)

    def process_incoming_message(
        self, context: CoreContext, phone_number: str, text: str
    ) -> ServiceResponse:
        try:
            text_clean = text.strip().lower()

            # 1. Resolve and Validate Conversation
            conv = self.repo.get_conversation(phone_number)
            if not conv:
                self.repo.create_conversation(phone_number)
                conv = self.repo.get_conversation(phone_number)
                if not conv:
                    return ServiceResponse.error_res(
                        "Could not initialize conversation", "CONV_INIT_ERROR"
                    )

            if conv["is_human_intervening"]:
                return ServiceResponse.success_res(
                    message="Human mode active", data={"silence": True}
                )

            # 2. Global Shortcuts
            if text_clean in [
                "/start",
                "hola",
                "buenas",
                "menu",
                "opciones",
                "volver",
                "menú",
            ]:
                self.repo.update_conversation_menu(phone_number, "main")
                return self.menu_mgmt.get_formatted_menu("main")

            # 3. Menu Navigation
            current_menu_name = conv["current_menu"]
            menu_struct = self.menu_mgmt.get_menu_structure(current_menu_name)

            if menu_struct:
                options = menu_struct.get("options", [])
                chosen_opt = None

                # Flexible Resolution: Match by Index, Technical Key, or Visible Label
                for idx, opt in enumerate(options, 1):
                    # 1. Match by Index (e.g., "1")
                    if text_clean == str(idx):
                        chosen_opt = opt
                        break
                    # 2. Match by Technical Key (e.g., "soporte")
                    if (
                        "option_key" in opt
                        and text_clean == str(opt["option_key"]).lower()
                    ):
                        chosen_opt = opt
                        break
                    # 3. Match by Visible Label (e.g., "Hablar con un asesor")
                    label = opt.get("label", "")
                    if text_clean == str(label).lower():
                        chosen_opt = opt
                        break

                if chosen_opt:
                    action_type = chosen_opt["action_type"]
                    action_value = chosen_opt["value"]

                    if action_type == "NAVIGATE":
                        self.repo.update_conversation_menu(phone_number, action_value)
                        return self.menu_mgmt.get_formatted_menu(action_value)

                    if action_type == "HUMAN":
                        self.conv_mgmt.toggle_human_mode(phone_number, True)
                        return ServiceResponse.success_res(
                            message="Transferring to a human agent..."
                        )

                    if action_type == "COMMAND":
                        return ServiceResponse.success_res(
                            data={
                                "action": "EXECUTE_COMMAND",
                                "command": chosen_opt["command_name"],
                            },
                            message=f"Executing action: {chosen_opt['command_name']}",
                        )

            # 4. Category Switching (Direct menu name match)
            all_menus = self.repo.list_all_menus()
            for m in all_menus:
                if text_clean == m["menu_name"].lower():
                    self.repo.update_conversation_menu(phone_number, m["menu_name"])
                    return self.menu_mgmt.get_formatted_menu(m["menu_name"])

            # 5. Fallback
            fallback = (
                self.repo.get_setting("fallback_message")
                or "No he entendido. Escribe 'menu' para opciones."
            )
            return ServiceResponse.success_res(message=fallback)

        except Exception as e:
            logger.error(f"Orchestration error for {phone_number}: {e}")
            return ServiceResponse.error_res(
                f"Bot flow error: {str(e)}", "BOT_FLOW_ERROR"
            )
