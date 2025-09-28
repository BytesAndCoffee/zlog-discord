import os
from dotenv import load_dotenv
from sqlalchemy.engine import make_url
import subprocess

try:
    from sqlacodegen.cli import main as sqlacodegen_main
except ImportError:
    from sqlacodegen_v2.cli import main as sqlacodegen_main

def build_connection_string():
    load_dotenv()

    user = os.getenv("DATABASE_USERNAME")
    password = os.getenv("DATABASE_PASSWORD")
    host = os.getenv("DATABASE_HOST")
    database = os.getenv("DATABASE")

    # Adjust driver for PlanetScale (MySQL-compatible) with correct SSL parameters
    conn_str = (
        f"mysql+pymysql://{user}:{password}@{host}/{database}"
        "?ssl_ca=/etc/ssl/cert.pem"
    )
    return conn_str

def autogen_models():
    conn_str = build_connection_string()
    print(f"🚀 Usinxg connection: {conn_str}")

    import sys
    from io import StringIO

    out_path = os.path.join(os.path.dirname(__file__), "models.py")
    old_stdout = sys.stdout
    sys_argv_backup = sys.argv
    try:
        with open(out_path, "w") as f:
            sys.stdout = f
            try:
                sys.argv = ["sqlacodegen", conn_str, "--generator", "declarative"]
                sqlacodegen_main()
            finally:
                sys.argv = sys_argv_backup
    finally:
        sys.stdout = old_stdout

    print("✅ Models generated at src/zlog-discord/models.py")

if __name__ == "__main__":
    autogen_models()
