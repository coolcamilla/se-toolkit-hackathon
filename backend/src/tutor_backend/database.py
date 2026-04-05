"""Database connection and initialization for the tutor backend."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from tutor_backend.settings import settings

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    topic TEXT NOT NULL
);
"""

_SEED_DATA = [
    (1, "What is recursion?", "Recursion is a function calling itself until it reaches a base case", "Algorithms"),
    (2, "What is Big O notation?", "Big O describes the upper bound of an algorithm time complexity in the worst case", "Algorithms"),
    (3, "What is the difference between stack and heap?", "Stack is automatic memory for local variables, heap is dynamic memory for objects", "Memory"),
    (4, "What does the HTTP GET method do?", "GET requests data from a server without modifying it", "Web"),
    (5, "What is the HTTP POST method?", "POST sends data to a server to create a resource", "Web"),
    (6, "What is a REST API?", "REST is an architectural style for web services using HTTP methods and status codes", "Web"),
    (7, "What is a hash table?", "A hash table is a data structure that stores key-value pairs with average O(1) access", "Data Structures"),
    (8, "What is a linked list?", "A linked list is a linear structure where each element holds a reference to the next", "Data Structures"),
    (9, "What is Docker?", "Docker is a platform for containerizing applications, isolating the process and its dependencies", "DevOps"),
    (10, "What is Git?", "Git is a distributed version control system for tracking changes in source code", "DevOps"),
]


def get_db_path() -> Path:
    return Path(settings.db_path)


def init_db() -> None:
    """Create tables and seed demo data if the database is empty."""
    db = get_db_path()
    conn = sqlite3.connect(str(db))
    try:
        conn.execute(_SCHEMA_SQL)
        cursor = conn.execute("SELECT COUNT(*) FROM questions")
        (count,) = cursor.fetchone()
        if count == 0:
            conn.executemany(
                "INSERT OR IGNORE INTO questions (id, text, correct_answer, topic) VALUES (?, ?, ?, ?)",
                _SEED_DATA,
            )
        conn.commit()
    finally:
        conn.close()


def get_connection() -> sqlite3.Connection:
    """Return a new connection with row_factory set."""
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    return conn
