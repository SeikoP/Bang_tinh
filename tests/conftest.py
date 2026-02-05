"""
Shared test fixtures and utilities for pytest.
Provides database fixtures, sample data, and Hypothesis strategies.
"""
import pytest
import sqlite3
import tempfile
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date
from typing import Generator
from hypothesis import strategies as st

# Import models
from core.models import Product, SessionData
from database.connection import init_db


@pytest.fixture
def test_db() -> Generator[Path, None, None]:
    """
    Create temporary test database with schema initialized.
    Automatically cleaned up after test completion.
    
    Usage:
        def test_something(test_db):
            conn = sqlite3.connect(test_db)
            # ... test code
    """
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    # Initialize schema
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            large_unit TEXT NOT NULL,
            conversion INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            is_active INTEGER DEFAULT 1,
            is_favorite INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_data (
            product_id INTEGER PRIMARY KEY,
            handover_qty INTEGER DEFAULT 0,
            closing_qty INTEGER DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_date DATE NOT NULL,
            shift_name TEXT,
            total_amount REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_history_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            history_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            large_unit TEXT NOT NULL,
            conversion INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            handover_qty INTEGER DEFAULT 0,
            closing_qty INTEGER DEFAULT 0,
            used_qty INTEGER DEFAULT 0,
            amount REAL DEFAULT 0,
            FOREIGN KEY (history_id) REFERENCES session_history (id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bank_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_str TEXT,
            source TEXT,
            amount TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_change_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            old_qty INTEGER NOT NULL,
            new_qty INTEGER NOT NULL,
            change_type TEXT NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def sample_products() -> list[Product]:
    """
    Create sample products for testing.
    
    Returns:
        List of Product instances with various configurations
    """
    return [
        Product(
            id=1,
            name="Nước suối",
            large_unit="Thùng",
            conversion=24,
            unit_price=Decimal("10.50"),
            is_active=True,
            is_favorite=False
        ),
        Product(
            id=2,
            name="Trứng gà",
            large_unit="Vỉ",
            conversion=30,
            unit_price=Decimal("3.00"),
            is_active=True,
            is_favorite=True
        ),
        Product(
            id=3,
            name="Xúc xích",
            large_unit="Gói",
            conversion=10,
            unit_price=Decimal("5.50"),
            is_active=True,
            is_favorite=False
        ),
        Product(
            id=4,
            name="Chai sành",
            large_unit="Két",
            conversion=20,
            unit_price=Decimal("15.00"),
            is_active=False,
            is_favorite=False
        ),
    ]


@pytest.fixture
def populated_test_db(test_db: Path, sample_products: list[Product]) -> Path:
    """
    Test database populated with sample products.
    
    Usage:
        def test_with_data(populated_test_db):
            conn = sqlite3.connect(populated_test_db)
            # Products already exist in database
    """
    conn = sqlite3.connect(str(test_db))
    cursor = conn.cursor()
    
    # Insert sample products
    for product in sample_products:
        cursor.execute(
            """
            INSERT INTO products (id, name, large_unit, conversion, unit_price, is_active, is_favorite)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product.id,
                product.name,
                product.large_unit,
                product.conversion,
                float(product.unit_price),
                1 if product.is_active else 0,
                1 if product.is_favorite else 0
            )
        )
        
        # Initialize session_data for each product
        cursor.execute(
            "INSERT INTO session_data (product_id, handover_qty, closing_qty) VALUES (?, 0, 0)",
            (product.id,)
        )
    
    conn.commit()
    conn.close()
    
    return test_db


# Hypothesis strategies for property-based testing

# Valid product names (non-empty, max 200 chars)
product_name_strategy = st.text(
    min_size=1,
    max_size=200,
    alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))
).filter(lambda s: len(s.strip()) > 0)

# Valid large units
large_unit_strategy = st.sampled_from([
    "Thùng", "Vỉ", "Gói", "Két", "Hộp", "Chai"
])

# Valid conversion factors (positive integers)
conversion_strategy = st.integers(min_value=1, max_value=1000)

# Valid unit prices (non-negative decimals with 2 decimal places)
unit_price_strategy = st.decimals(
    min_value=0,
    max_value=10000,
    places=2,
    allow_nan=False,
    allow_infinity=False
)

# Product strategy
product_strategy = st.builds(
    Product,
    id=st.one_of(st.none(), st.integers(min_value=1)),
    name=product_name_strategy,
    large_unit=large_unit_strategy,
    conversion=conversion_strategy,
    unit_price=unit_price_strategy,
    is_active=st.booleans(),
    is_favorite=st.booleans(),
    created_at=st.one_of(st.none(), st.datetimes()),
    updated_at=st.one_of(st.none(), st.datetimes())
)

# Session data strategy (with valid business rules)
session_data_strategy = st.builds(
    SessionData,
    product=product_strategy,
    handover_qty=st.integers(min_value=0, max_value=10000),
    closing_qty=st.integers(min_value=0, max_value=10000)
).filter(lambda s: s.closing_qty <= s.handover_qty)

# Quantity string strategy for calculator testing
quantity_string_strategy = st.one_of(
    # Integer only: "5"
    st.integers(min_value=0, max_value=1000).map(str),
    # Decimal: "3.5"
    st.decimals(
        min_value=0,
        max_value=1000,
        places=1,
        allow_nan=False,
        allow_infinity=False
    ).map(str),
    # With unit: "3t5" or "2.5v"
    st.tuples(
        st.integers(min_value=0, max_value=100),
        st.sampled_from(['t', 'v', 'g', 'k', 'h', 'c']),
        st.integers(min_value=0, max_value=100)
    ).map(lambda x: f"{x[0]}{x[1]}{x[2]}")
)

# SQL injection payload strategy
sql_injection_strategy = st.sampled_from([
    "'; DROP TABLE products; --",
    "1' OR '1'='1",
    "admin'--",
    "' OR 1=1--",
    "1; DELETE FROM products WHERE 1=1",
    "' UNION SELECT * FROM products--",
    "1' AND '1'='1",
])

# XSS payload strategy
xss_payload_strategy = st.sampled_from([
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "javascript:alert('XSS')",
    "<svg onload=alert('XSS')>",
])

# Environment variable names strategy
env_var_name_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(whitelist_categories=('Lu',), whitelist_characters='_')
)

# License key format strategy (simplified)
license_key_strategy = st.text(
    min_size=32,
    max_size=128,
    alphabet=st.characters(whitelist_categories=('Lu', 'Nd'), whitelist_characters='-')
)
