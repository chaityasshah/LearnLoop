import os
import datetime
import subprocess

def backup_database():
    """
    Backs up the PostgreSQL database safely.
    Does NOT automatically delete old backups.
    Does NOT automatically upload data anywhere.
    """
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url or "postgresql" not in db_url:
        print("Backup script currently configured for PostgreSQL only.")
        return
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"learnloop_backup_{timestamp}.sql"
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    filepath = os.path.join(backup_dir, backup_file)
    
    # Very basic pg_dump invocation (requires pg_dump in PATH and appropriate auth)
    # E.g., pg_dump -d postgresql://postgres:password@localhost:5432/learnloop -f backup.sql
    try:
        print(f"Starting backup to {filepath}...")
        # WARNING: In a real production system, do not pass passwords via command line arguments.
        # This is just a script outline.
        subprocess.run(["pg_dump", "-d", db_url, "-f", filepath], check=True, capture_output=True)
        print("Backup completed successfully.")
    except Exception as e:
        print(f"Failed to backup database: {e}. Is pg_dump installed and in PATH?")

if __name__ == "__main__":
    backup_database()
