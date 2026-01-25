"""
Migration Helper - Utilities for Alembic migration management
"""

import subprocess
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MigrationHelper:
    """Helper class for managing Alembic migrations"""
    
    def __init__(self, migration_dir: str | None = None):
        """
        Initialize migration helper.
        
        Args:
            migration_dir: Path to migration directory (default: current dir)
        """
        if migration_dir is None:
            migration_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.migration_dir = migration_dir
        self.alembic_ini = os.path.join(migration_dir, "alembic.ini")
    
    def init_migrations(self, project_name: str = "project") -> bool:
        """
        Initialize Alembic for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            True if successful
        """
        try:
            cmd = f"alembic init -t generic {project_name}"
            subprocess.run(cmd, cwd=self.migration_dir, check=True)
            logger.info(f"Migrations initialized for {project_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize migrations: {e}")
            return False
    
    def create_migration(self, message: str, autogenerate: bool = True) -> bool:
        """
        Create a new migration file.
        
        Args:
            message: Migration description
            autogenerate: Auto-generate migration from models
            
        Returns:
            True if successful
        """
        try:
            auto_flag = "--autogenerate" if autogenerate else ""
            cmd = f"alembic revision {auto_flag} -m \"{message}\""
            subprocess.run(cmd, cwd=self.migration_dir, check=True)
            logger.info(f"Migration created: {message}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create migration: {e}")
            return False
    
    def upgrade(self, revision: str = "head") -> bool:
        """
        Apply migrations.
        
        Args:
            revision: Target revision (default: head)
            
        Returns:
            True if successful
        """
        try:
            cmd = f"alembic upgrade {revision}"
            subprocess.run(cmd, cwd=self.migration_dir, check=True)
            logger.info(f"Migrated to {revision}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def downgrade(self, revision: str) -> bool:
        """
        Rollback migrations.
        
        Args:
            revision: Target revision
            
        Returns:
            True if successful
        """
        try:
            cmd = f"alembic downgrade {revision}"
            subprocess.run(cmd, cwd=self.migration_dir, check=True)
            logger.info(f"Rolled back to {revision}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def get_current_revision(self) -> str:
        """
        Get current database revision.
        
        Returns:
            Current revision ID or error message
        """
        try:
            result = subprocess.run(
                "alembic current",
                cwd=self.migration_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get current revision: {e}")
            return "unknown"
    
    def get_migration_history(self) -> list[str]:
        """
        Get migration history.
        
        Returns:
            List of migration revisions
        """
        try:
            result = subprocess.run(
                "alembic history",
                cwd=self.migration_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get migration history: {e}")
            return []
    
    def show_migrations(self) -> None:
        """Display migration files in the versions directory."""
        versions_dir = os.path.join(self.migration_dir, "versions")
        if not os.path.exists(versions_dir):
            logger.info("No migrations yet")
            return
        
        migrations = sorted(Path(versions_dir).glob("*.py"))
        for migration in migrations:
            print(f"  {migration.name}")
