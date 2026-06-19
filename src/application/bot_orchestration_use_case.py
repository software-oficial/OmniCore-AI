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
            cid = context.credential_id

            if not cid:
                return ServiceResponse.error_res(
                    "credential_id is required for bot orchestration.",
                    "CREDENTIAL_REQUIRED",
                )

            # 1. Resolve and Validate Conversation
            conv = self.repo.get_conversation(phone_number, cid)
            if not conv:
                self.repo.create_conversation(phone_number, cid)
                conv = self.repo.get_conversation(phone_number, cid)
                if not conv:
                    return ServiceResponse.error_res(
                        "Could not initialize conversation", "CONV_INIT_ERROR"
                    )

            if conv["status"] == "PENDING_HUMAN":
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
                self.repo.update_conversation_node(phone_number, cid, "main")
                return self.menu_mgmt.get_formatted_menu("main")

            # 3. Menu Navigation (Bot Flows)
            current_node = conv["current_node"]
            node_struct = self.repo.get_flow_node(current_node, cid)

            if node_struct:
                options = node_struct.get("options", [])
                chosen_opt = None

                # Resolve options (similar logic to before, but based on flow options)
                # Note: In a real scenario, options would be parsed from JSON
                import json

                try:
                    if isinstance(options, str):
                        options = json.loads(options)
                except (json.JSONDecodeError, TypeError):
                    pass

                for idx, opt in enumerate(options, 1):
                    if text_clean == str(idx):
                        chosen_opt = opt
                        break
                    if (
                        "option_key" in opt
                        and text_clean == str(opt["option_key"]).lower()
                    ):
                        chosen_opt = opt
                        break
                    if text_clean == str(opt.get("label", "")).lower():
                        chosen_opt = opt
                        break

                if chosen_opt:
                    action_type = chosen_opt.get("action_type")
                    action_value = chosen_opt.get("value")

                    if action_type == "NAVIGATE":
                        self.repo.update_conversation_node(
                            phone_number, cid, action_value
                        )
                        # We reuse menu_mgmt to format the response for the new node
                        return self.menu_mgmt.get_formatted_menu(action_value)

                    if action_type == "HUMAN":
                        self.conv_mgmt.toggle_human_mode(phone_number, True, cid)
                        return ServiceResponse.success_res(
                            message="Transferring to a human agent..."
                        )

                    if action_type == "COMMAND":
                        return ServiceResponse.success_res(
                            data={
                                "action": "EXECUTE_COMMAND",
                                "command": chosen_opt.get("command_name"),
                            },
                            message=f"Executing action: {chosen_opt.get('command_name')}",
                        )

            # 4. Node Switching (Direct node name match)
            all_nodes = self.repo.list_all_nodes(cid)
            for node in all_nodes:
                if text_clean == node["node_id"].lower():
                    self.repo.update_conversation_node(
                        phone_number, cid, node["node_id"]
                    )
                    return self.menu_mgmt.get_formatted_menu(node["node_id"], cid)

            # 5. Fallback
            fallback_msg = (
                context.settings.get("fallback_message")
                or "No he entendido. Escribe 'menu' para opciones."
            )
            return ServiceResponse.success_res(message=fallback_msg)

        except Exception as e:
            logger.error(f"Orchestration error for {phone_number}: {e}")
            return ServiceResponse.error_res(
                f"Bot flow error: {str(e)}", "BOT_FLOW_ERROR"
            )
