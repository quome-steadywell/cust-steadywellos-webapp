import subprocess
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from one directory above this script
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get values from .env
docker_container_name = "palliative_care_platform-db-1"
db_name = os.getenv("POSTGRES_DB")
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")

if not all([db_name, db_user, db_password]):
    raise ValueError("Missing required environment variables in .env")

# Create the output directory if it doesn't exist
output_dir = Path(__file__).resolve().parent.parent / 'data' / 'sqldump'
output_dir.mkdir(parents=True, exist_ok=True)

# Set output file path
output_file = output_dir / f"{db_name}_dump.sql"

# Command to run pg_dump inside the Docker container
command = [
    "docker", "exec", "-e", f"PGPASSWORD={db_password}",
    docker_container_name,
    "pg_dump", "-U", db_user, db_name
]

# Run the export and write to file
with open(output_file, "w") as f:
    try:
        subprocess.run(command, stdout=f, check=True)
        print(f"✅ Exported database to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to export: {e}")
