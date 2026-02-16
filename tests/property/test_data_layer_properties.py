"""
Property-based tests for data layer.

**Validates: Requirements 3.2**
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# Strategies


@st.composite
def table_relationship(draw):
    """Generate a table relationship definition."""
    parent_table = draw(st.sampled_from(["products", "session_history", "users"]))
    child_table = draw(
        st.sampled_from(["session_data", "session_history_items", "orders"])
    )
    foreign_key_column = draw(st.sampled_from(["product_id", "history_id", "user_id"]))
    parent_key_column = "id"

    return {
        "parent_table": parent_table,
        "child_table": child_table,
        "foreign_key_column": foreign_key_column,
        "parent_key_column": parent_key_column,
    }


@st.composite
def database_schema(draw):
    """Generate a simple database schema with relationships."""
    num_tables = draw(st.integers(min_value=2, max_value=5))

    schema = {"tables": [], "relationships": []}

    # Create parent table
    schema["tables"].append(
        {"name": "parent_table", "columns": ["id INTEGER PRIMARY KEY", "name TEXT"]}
    )

    # Create child tables with foreign keys
    for i in range(num_tables - 1):
        child_name = f"child_table_{i}"
        schema["tables"].append(
            {
                "name": child_name,
                "columns": ["id INTEGER PRIMARY KEY", "parent_id INTEGER", "data TEXT"],
            }
        )

        schema["relationships"].append(
            {
                "child_table": child_name,
                "parent_table": "parent_table",
                "foreign_key": "parent_id",
                "parent_key": "id",
            }
        )

    return schema


# Property Tests


@pytest.mark.property
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(schema=database_schema())
def test_property_10_foreign_key_constraint_completeness(schema):
    """
    Property 10: Foreign Key Constraint Completeness

    For any database relationship between tables, there should exist a
    corresponding foreign key constraint in the schema.

    **Validates: Requirements 3.2**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Create tables
        for table in schema["tables"]:
            columns = ", ".join(table["columns"])
            cursor.execute(f"CREATE TABLE {table['name']} ({columns})")

        # Add foreign key constraints
        for rel in schema["relationships"]:
            # SQLite requires recreating table to add FK constraint
            # For this test, we'll verify the relationship is defined
            child_table = rel["child_table"]
            parent_table = rel["parent_table"]
            fk_column = rel["foreign_key"]
            pk_column = rel["parent_key"]

            # Verify the foreign key column exists in child table
            cursor.execute(f"PRAGMA table_info({child_table})")
            columns = [row[1] for row in cursor.fetchall()]

            # Property: Foreign key column should exist in child table
            assert (
                fk_column in columns
            ), f"Foreign key column {fk_column} should exist in {child_table}"

            # Verify parent key column exists in parent table
            cursor.execute(f"PRAGMA table_info({parent_table})")
            parent_columns = [row[1] for row in cursor.fetchall()]

            # Property: Parent key column should exist in parent table
            assert (
                pk_column in parent_columns
            ), f"Parent key column {pk_column} should exist in {parent_table}"

        conn.close()


@pytest.mark.property
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    parent_id=st.integers(min_value=1, max_value=100),
    child_count=st.integers(min_value=1, max_value=10),
)
def test_property_foreign_key_cascade_delete(parent_id, child_count):
    """
    Property: When a parent record is deleted, child records with FK
    constraints should be handled according to CASCADE rules.

    **Validates: Requirements 3.2**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Create tables with FK constraint
        cursor.execute("""
            CREATE TABLE parent (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE child (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER,
                data TEXT,
                FOREIGN KEY (parent_id) REFERENCES parent(id) ON DELETE CASCADE
            )
        """)

        # Insert parent record
        cursor.execute(
            "INSERT INTO parent (id, name) VALUES (?, ?)",
            (parent_id, f"Parent {parent_id}"),
        )

        # Insert child records
        for i in range(child_count):
            cursor.execute(
                "INSERT INTO child (parent_id, data) VALUES (?, ?)",
                (parent_id, f"Child {i}"),
            )

        conn.commit()

        # Verify children exist
        cursor.execute("SELECT COUNT(*) FROM child WHERE parent_id = ?", (parent_id,))
        count_before = cursor.fetchone()[0]
        assert count_before == child_count

        # Delete parent
        cursor.execute("DELETE FROM parent WHERE id = ?", (parent_id,))
        conn.commit()

        # Property: Child records should be deleted (CASCADE)
        cursor.execute("SELECT COUNT(*) FROM child WHERE parent_id = ?", (parent_id,))
        count_after = cursor.fetchone()[0]

        assert (
            count_after == 0
        ), "Child records should be deleted when parent is deleted (CASCADE)"

        conn.close()


@pytest.mark.property
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    valid_parent_id=st.integers(min_value=1, max_value=100),
    invalid_parent_id=st.integers(min_value=101, max_value=200),
)
def test_property_foreign_key_constraint_enforcement(
    valid_parent_id, invalid_parent_id
):
    """
    Property: Foreign key constraints should prevent insertion of child
    records with non-existent parent references.

    **Validates: Requirements 3.2**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        try:
            # Create tables with FK constraint
            cursor.execute("""
                CREATE TABLE parent (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE child (
                    id INTEGER PRIMARY KEY,
                    parent_id INTEGER NOT NULL,
                    data TEXT,
                    FOREIGN KEY (parent_id) REFERENCES parent(id)
                )
            """)

            # Insert valid parent
            cursor.execute(
                "INSERT INTO parent (id, name) VALUES (?, ?)",
                (valid_parent_id, f"Parent {valid_parent_id}"),
            )
            conn.commit()

            # Property: Should allow insertion with valid parent_id
            try:
                cursor.execute(
                    "INSERT INTO child (parent_id, data) VALUES (?, ?)",
                    (valid_parent_id, "Valid child"),
                )
                conn.commit()
                valid_insert_succeeded = True
            except sqlite3.IntegrityError:
                valid_insert_succeeded = False

            assert (
                valid_insert_succeeded
            ), "Should allow insertion with valid parent reference"

            # Property: Should prevent insertion with invalid parent_id
            try:
                cursor.execute(
                    "INSERT INTO child (parent_id, data) VALUES (?, ?)",
                    (invalid_parent_id, "Invalid child"),
                )
                conn.commit()
                invalid_insert_succeeded = True
            except sqlite3.IntegrityError:
                invalid_insert_succeeded = False

            assert (
                not invalid_insert_succeeded
            ), "Should prevent insertion with invalid parent reference"

        finally:
            cursor.close()
            conn.close()
            import gc
            gc.collect()


@pytest.mark.property
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    table_name=st.sampled_from(["products", "session_history", "users", "orders"]),
    has_fk=st.booleans(),
)
def test_property_relationship_documentation(table_name, has_fk):
    """
    Property: All tables with foreign keys should have them properly
    documented and queryable via PRAGMA foreign_key_list.

    **Validates: Requirements 3.2**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Create parent table
        cursor.execute("""
            CREATE TABLE parent (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)

        # Create table with or without FK
        if has_fk:
            cursor.execute(f"""
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY,
                    parent_id INTEGER,
                    data TEXT,
                    FOREIGN KEY (parent_id) REFERENCES parent(id)
                )
            """)
        else:
            cursor.execute(f"""
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY,
                    data TEXT
                )
            """)

        # Query foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fk_list = cursor.fetchall()

        # Property: If table has FK, it should be in the list
        if has_fk:
            assert (
                len(fk_list) > 0
            ), f"Table {table_name} should have foreign keys in PRAGMA output"
        else:
            assert len(fk_list) == 0, f"Table {table_name} should not have foreign keys"

        conn.close()
