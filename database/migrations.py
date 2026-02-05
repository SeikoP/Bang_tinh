"""
Database migration system for schema changes.
Implements Migration base class and MigrationManager for applying migrations.
"""
from abc import ABC, abstractmethod
from typing import List
import sqlite3
import logging
from pathlib import Path
from datetime import datetime


class Migration(ABC):
    """Base class for database migrations"""
    
    @property
    @abstractmethod
    def version(self) -> int:
        """Migration version number"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Migration description"""
        pass
    
    @abstractmethod
    def up(self, conn: sqlite3.Connection) -> None:
        """Apply migration"""
        pass
    
    @abstractmethod
    def down(self, conn: sqlite3.Connection) -> None:
        """Rollback migration"""
        pass


class Migration001AddIndexes(Migration):
    """Add indexes on frequently queried columns"""
    
    @property
    def version(self) -> int:
        return 1
    
    @property
    def description(self) -> str:
        return "Add indexes on frequently queried columns"
    
    def up(self, conn: sqlite3.Connection) -> None:
        """Create indexes"""
        cursor = conn.cursor()
        
        # Index on products.name for search operations
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_name 
            ON products(name)
        """)
        
        # Index on products.is_active for filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_active 
            ON products(is_active)
        """)
        
        # Index on session_history.session_date for date range queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_history_date 
            ON session_history(session_date)
        """)
        
        # Index on bank_history.created_at for sorting
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bank_history_created 
            ON bank_history(created_at)
        """)
        
        # Index on stock_change_logs.changed_at for sorting
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_change_logs_changed 
            ON stock_change_logs(changed_at)
        """)
        
        conn.commit()
    
    def down(self, conn: sqlite3.Connection) -> None:
        """Remove indexes"""
        cursor = conn.cursor()
        
        cursor.execute("DROP INDEX IF EXISTS idx_products_name")
        cursor.execute("DROP INDEX IF EXISTS idx_products_active")
        cursor.execute("DROP INDEX IF EXISTS idx_session_history_date")
        cursor.execute("DROP INDEX IF EXISTS idx_bank_history_created")
        cursor.execute("DROP INDEX IF EXISTS idx_stock_change_logs_changed")
        
        conn.commit()


class Migration002AddForeignKeys(Migration):
    """Add foreign key constraints"""
    
    @property
    def version(self) -> int:
        return 2
    
    @property
    def description(self) -> str:
        return "Add foreign key constraints"
    
    def up(self, conn: sqlite3.Connection) -> None:
        """Enable foreign keys"""
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Verify foreign key constraints are properly defined
        # (They should already exist from init_db, this ensures they're enforced)
        
        conn.commit()
    
    def down(self, conn: sqlite3.Connection) -> None:
        """Disable foreign keys"""
        cursor = conn.cursor()
        
        # Disable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        conn.commit()


class Migration003AddAuditColumns(Migration):
    """Add audit columns (created_by, updated_by)"""
    
    @property
    def version(self) -> int:
        return 3
    
    @property
    def description(self) -> str:
        return "Add audit columns (created_by, updated_by)"
    
    def up(self, conn: sqlite3.Connection) -> None:
        """Add audit columns to tables"""
        cursor = conn.cursor()
        
        # Add created_by and updated_by to products
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN created_by TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN updated_by TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add created_by to session_history
        try:
            cursor.execute("ALTER TABLE session_history ADD COLUMN created_by TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add created_by to bank_history
        try:
            cursor.execute("ALTER TABLE bank_history ADD COLUMN created_by TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add soft delete support to session_history
        try:
            cursor.execute("ALTER TABLE session_history ADD COLUMN deleted_at TIMESTAMP")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE session_history_items ADD COLUMN deleted_at TIMESTAMP")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        conn.commit()
    
    def down(self, conn: sqlite3.Connection) -> None:
        """Remove audit columns"""
        # SQLite doesn't support DROP COLUMN easily
        # Would require recreating tables, which is risky
        # For now, we'll leave the columns in place
        pass


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, db_path: Path, migrations: List[Migration] = None):
        self.db_path = db_path
        
        # Default migrations if none provided
        if migrations is None:
            self.migrations = [
                Migration001AddIndexes(),
                Migration002AddForeignKeys(),
                Migration003AddAuditColumns(),
            ]
        else:
            self.migrations = migrations
        
        # Sort migrations by version
        self.migrations = sorted(self.migrations, key=lambda m: m.version)
    
    def _ensure_schema_version_table(self, conn: sqlite3.Connection) -> None:
        """Ensure schema_version table exists"""
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    
    def get_current_version(self) -> int:
        """Get current database version"""
        with sqlite3.connect(self.db_path) as conn:
            self._ensure_schema_version_table(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0
    
    def migrate(self, target_version: int = None, logger: logging.Logger = None) -> None:
        """
        Apply migrations up to target version.
        
        Args:
            target_version: Target version to migrate to (latest if None)
            logger: Logger instance for output
        """
        current = self.get_current_version()
        target = target_version or (self.migrations[-1].version if self.migrations else 0)
        
        if current >= target:
            if logger:
                logger.info(f"Database is already at version {current}")
            return
        
        with sqlite3.connect(self.db_path) as conn:
            self._ensure_schema_version_table(conn)
            
            for migration in self.migrations:
                if current < migration.version <= target:
                    if logger:
                        logger.info(f"Applying migration {migration.version}: {migration.description}")
                    
                    try:
                        migration.up(conn)
                        
                        # Record migration
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                            (migration.version, migration.description)
                        )
                        conn.commit()
                        
                        if logger:
                            logger.info(f"✓ Migration {migration.version} applied successfully")
                    except Exception as e:
                        if logger:
                            logger.error(f"✗ Migration {migration.version} failed: {str(e)}")
                        conn.rollback()
                        raise
    
    def rollback(self, target_version: int = 0, logger: logging.Logger = None) -> None:
        """
        Rollback migrations to target version.
        
        Args:
            target_version: Target version to rollback to
            logger: Logger instance for output
        """
        current = self.get_current_version()
        
        if current <= target_version:
            if logger:
                logger.info(f"Database is already at or below version {target_version}")
            return
        
        with sqlite3.connect(self.db_path) as conn:
            # Rollback migrations in reverse order
            for migration in reversed(self.migrations):
                if target_version < migration.version <= current:
                    if logger:
                        logger.info(f"Rolling back migration {migration.version}: {migration.description}")
                    
                    try:
                        migration.down(conn)
                        
                        # Remove migration record
                        cursor = conn.cursor()
                        cursor.execute(
                            "DELETE FROM schema_version WHERE version = ?",
                            (migration.version,)
                        )
                        conn.commit()
                        
                        if logger:
                            logger.info(f"✓ Migration {migration.version} rolled back successfully")
                    except Exception as e:
                        if logger:
                            logger.error(f"✗ Rollback of migration {migration.version} failed: {str(e)}")
                        conn.rollback()
                        raise
    
    def status(self, logger: logging.Logger = None) -> None:
        """
        Display migration status.
        
        Args:
            logger: Logger instance for output
        """
        current = self.get_current_version()
        if logger:
            logger.info(f"Current database version: {current}")
            logger.info("Available migrations:")
            
            for migration in self.migrations:
                status = "✓ Applied" if migration.version <= current else "○ Pending"
                logger.info(f"  {status} - Version {migration.version}: {migration.description}")
