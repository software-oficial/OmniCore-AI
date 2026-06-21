import json

from src.core.module_loader import module_loader

# Force loading all domains
domains = ["sales", "stock", "system", "whatsapp"]
for domain in domains:
    module_loader.load_module(domain)

# Export registry
registry = {
    k: {"description": v["description"]}
    for k, v in module_loader._command_registry.items()
}
print(json.dumps(registry, indent=2))
