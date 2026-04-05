"""Database connection and initialization for the tutor backend."""

from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text, select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from tutor_backend.settings import settings

engine = create_async_engine(settings.db_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    topic = Column(String, nullable=False)


_SEED_DATA = [
    {
        "id": 1,
        "text": "What is recursion?",
        "correct_answer": "Recursion is a function calling itself until it reaches a base case",
        "topic": "Algorithms",
    },
    {
        "id": 2,
        "text": "What is Big O notation?",
        "correct_answer": "Big O describes the upper bound of an algorithm time complexity in the worst case",
        "topic": "Algorithms",
    },
    {
        "id": 3,
        "text": "What is the difference between stack and heap?",
        "correct_answer": "Stack is automatic memory for local variables, heap is dynamic memory for objects",
        "topic": "Memory",
    },
    {
        "id": 4,
        "text": "What does the HTTP GET method do?",
        "correct_answer": "GET requests data from a server without modifying it",
        "topic": "Web",
    },
    {
        "id": 5,
        "text": "What is the HTTP POST method?",
        "correct_answer": "POST sends data to a server to create a resource",
        "topic": "Web",
    },
    {
        "id": 6,
        "text": "What is a REST API?",
        "correct_answer": "REST is an architectural style for web services using HTTP methods and status codes",
        "topic": "Web",
    },
    {
        "id": 7,
        "text": "What is a hash table?",
        "correct_answer": "A hash table is a data structure that stores key-value pairs with average O(1) access",
        "topic": "Data Structures",
    },
    {
        "id": 8,
        "text": "What is a linked list?",
        "correct_answer": "A linked list is a linear structure where each element holds a reference to the next",
        "topic": "Data Structures",
    },
    {
        "id": 9,
        "text": "What is Docker?",
        "correct_answer": "Docker is a platform for containerizing applications, isolating the process and its dependencies",
        "topic": "DevOps",
    },
    {
        "id": 10,
        "text": "What is Git?",
        "correct_answer": "Git is a distributed version control system for tracking changes in source code",
        "topic": "DevOps",
    },
]


async def init_db() -> None:
    """Create tables and seed demo data if the database is empty."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(func.count(Question.id)))
        count = result.scalar()
        if count == 0:
            session.add_all([Question(**q) for q in _SEED_DATA])
            await session.commit()
