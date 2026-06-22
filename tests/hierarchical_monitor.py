import os
import time

from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway"
)

# ANSI Colors
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def render_tree():
    with engine.connect() as conn:
        users = conn.execute(text("SELECT id, email FROM users")).mappings().all()
        os.system("cls" if os.name == "nt" else "clear")

        print(f"{BOLD}{BLUE}=== MONITOR HIERÁRQUICO USUARIO -> EMPRESA ==={RESET}")
        print(f"{YELLOW}Actualizado: {time.strftime('%H:%M:%S')}{RESET}\n")

        for u in users:
            apps = (
                conn.execute(
                    text("SELECT id, name FROM apps WHERE owner_id = :uid"),
                    {"uid": u["id"]},
                )
                .mappings()
                .all()
            )

            if not apps:
                continue

            print(f"👤 {BOLD}{u['email']}{RESET}")

            for a in apps:
                # Sales count
                sales = conn.execute(
                    text("SELECT COUNT(*) FROM sales WHERE app_id = :aid"),
                    {"aid": a["id"]},
                ).scalar()

                # Employee count: users linked to the app via app_id and not the owner
                emp_query = text(
                    """
                    SELECT COUNT(id) 
                    FROM users 
                    WHERE app_id = :aid AND role != 'owner'
                """
                )
                emps = conn.execute(emp_query, {"aid": a["id"]}).scalar()

                print(f"  └── 🏢 {BOLD}{a['name']}{RESET}")
                print(f"      ├── 👥 Empleados: {GREEN}{emps}{RESET}")
                print(f"      └── 💰 Ventas: {GREEN}{sales}{RESET}")

        if not users:
            print("No se encontraron usuarios.")


def if_main():
    while True:
        try:
            render_tree()
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
        time.sleep(2)


if __name__ == "__main__":
    if_main()
