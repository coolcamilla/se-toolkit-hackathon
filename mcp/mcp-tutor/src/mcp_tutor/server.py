"""Stdio MCP server exposing tutor question database operations via PostgreSQL."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, select, func, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from mcp_tutor.settings import get_db_url

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

engine = create_async_engine(get_db_url(), echo=False)
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


async def _ensure_db() -> None:
    """Create table and seed data if empty."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(func.count(Question.id)))
        count = result.scalar()
        if count == 0:
            session.add_all([Question(**q) for q in _SEED_DATA])
            await session.commit()
        # Sync sequence
        await session.execute(
            text(
                "SELECT setval(pg_get_serial_sequence('questions', 'id'), COALESCE((SELECT MAX(id) FROM questions), 1), true)"
            )
        )
        await session.commit()


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------


async def _get_random_question(topic: str | None) -> dict:
    async with async_session() as session:
        if topic:
            stmt = select(Question).where(Question.topic == topic)
        else:
            stmt = select(Question)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        if not rows:
            return {"error": "No questions found", "topic": topic}
        import random

        q = random.choice(rows)
        return {"id": q.id, "text": q.text, "topic": q.topic}


async def _check_answer(question_id: int, user_answer: str) -> dict:
    async with async_session() as session:
        result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        q = result.scalar_one_or_none()
        if q is None:
            return {"error": f"Question with id={question_id} not found"}
        correct_words = set(q.correct_answer.lower().split())
        answer_words = set(user_answer.lower().split())
        overlap = len(correct_words & answer_words)
        total = len(correct_words)
        score = overlap / total if total > 0 else 0
        return {
            "question_id": question_id,
            "question": q.text,
            "user_answer": user_answer,
            "correct_answer": q.correct_answer,
            "keyword_overlap_score": round(score, 2),
        }


async def _get_all_topics() -> list[str]:
    async with async_session() as session:
        result = await session.execute(
            select(Question.topic).distinct().order_by(Question.topic)
        )
        return [row[0] for row in result.all()]


async def _add_question(text_val: str, correct_answer: str, topic: str) -> dict:
    async with async_session() as session:
        q = Question(text=text_val, correct_answer=correct_answer, topic=topic)
        session.add(q)
        await session.commit()
        await session.refresh(q)
        return {
            "id": q.id,
            "text": q.text,
            "correct_answer": q.correct_answer,
            "topic": q.topic,
        }


async def _delete_question(question_id: int) -> dict:
    async with async_session() as session:
        result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        q = result.scalar_one_or_none()
        if q is None:
            return {"error": f"Question with id={question_id} not found"}
        info = {"id": q.id, "text": q.text, "topic": q.topic, "status": "deleted"}
        await session.delete(q)
        await session.commit()
        return info


async def _update_question(
    question_id: int,
    text_val: str | None,
    correct_answer: str | None,
    topic: str | None,
) -> dict:
    async with async_session() as session:
        result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        q = result.scalar_one_or_none()
        if q is None:
            return {"error": f"Question with id={question_id} not found"}
        if text_val is not None:
            q.text = text_val
        if correct_answer is not None:
            q.correct_answer = correct_answer
        if topic is not None:
            q.topic = topic
        await session.commit()
        await session.refresh(q)
        return {
            "id": q.id,
            "text": q.text,
            "correct_answer": q.correct_answer,
            "topic": q.topic,
            "status": "updated",
        }


async def _delete_topic(topic: str) -> dict:
    async with async_session() as session:
        result = await session.execute(select(Question).where(Question.topic == topic))
        rows = result.scalars().all()
        if not rows:
            return {"error": f"No questions found for topic '{topic}'"}
        count = len(rows)
        questions = [{"id": q.id, "text": q.text, "topic": q.topic} for q in rows]
        for q in rows:
            await session.delete(q)
        await session.commit()
        return {
            "status": "deleted",
            "topic": topic,
            "count": count,
            "questions": questions,
        }


async def _search_questions(keyword: str) -> dict:
    async with async_session() as session:
        pattern = f"%{keyword}%"
        stmt = select(Question).where(
            Question.text.ilike(pattern) | Question.topic.ilike(pattern)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        if not rows:
            return {"error": f"No questions found matching '{keyword}'"}
        return {
            "keyword": keyword,
            "count": len(rows),
            "questions": [{"id": q.id, "text": q.text, "topic": q.topic} for q in rows],
        }


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


class GetRandomQuestionArgs(BaseModel):
    topic: str | None = None


class CheckAnswerArgs(BaseModel):
    question_id: int
    user_answer: str


class GetTopicsArgs(BaseModel):
    pass


class AddQuestionArgs(BaseModel):
    text: str
    correct_answer: str
    topic: str


class DeleteQuestionArgs(BaseModel):
    question_id: int


class UpdateQuestionArgs(BaseModel):
    question_id: int
    text: str | None = None
    correct_answer: str | None = None
    topic: str | None = None


class DeleteTopicArgs(BaseModel):
    topic: str


class SearchQuestionsArgs(BaseModel):
    keyword: str


async def handle_get_random_question(args: GetRandomQuestionArgs) -> dict:
    return await _get_random_question(args.topic)


async def handle_check_answer(args: CheckAnswerArgs) -> dict:
    return await _check_answer(args.question_id, args.user_answer)


async def handle_get_topics(args: GetTopicsArgs) -> list[str]:
    return await _get_all_topics()


async def handle_add_question(args: AddQuestionArgs) -> dict:
    return await _add_question(args.text, args.correct_answer, args.topic)


async def handle_delete_question(args: DeleteQuestionArgs) -> dict:
    return await _delete_question(args.question_id)


async def handle_update_question(args: UpdateQuestionArgs) -> dict:
    return await _update_question(
        args.question_id, args.text, args.correct_answer, args.topic
    )


async def handle_delete_topic(args: DeleteTopicArgs) -> dict:
    return await _delete_topic(args.topic)


async def handle_search_questions(args: SearchQuestionsArgs) -> dict:
    return await _search_questions(args.keyword)


TOOL_SPECS = [
    {
        "name": "get_random_question",
        "description": "Get a random question from the tutor database. Optionally filter by topic.",
        "model": GetRandomQuestionArgs,
        "handler": handle_get_random_question,
    },
    {
        "name": "check_answer",
        "description": "Check a user's answer against the correct answer for a given question. Returns keyword overlap score.",
        "model": CheckAnswerArgs,
        "handler": handle_check_answer,
    },
    {
        "name": "get_all_topics",
        "description": "Get a list of all available question topics.",
        "model": GetTopicsArgs,
        "handler": handle_get_topics,
    },
    {
        "name": "add_question",
        "description": "Add a new question to the tutor database. Requires question text, correct answer, and topic.",
        "model": AddQuestionArgs,
        "handler": handle_add_question,
    },
    {
        "name": "delete_question",
        "description": "Delete a question from the tutor database by its ID.",
        "model": DeleteQuestionArgs,
        "handler": handle_delete_question,
    },
    {
        "name": "update_question",
        "description": "Update an existing question. Provide question_id and any fields to change.",
        "model": UpdateQuestionArgs,
        "handler": handle_update_question,
    },
    {
        "name": "delete_topic",
        "description": "Delete all questions belonging to a specific topic.",
        "model": DeleteTopicArgs,
        "handler": handle_delete_topic,
    },
    {
        "name": "search_questions",
        "description": "Search for questions by keyword in text or topic name.",
        "model": SearchQuestionsArgs,
        "handler": handle_search_questions,
    },
]

TOOLS_BY_NAME = {spec["name"]: spec for spec in TOOL_SPECS}


def _text(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False))]


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------


def create_server() -> Server:
    server = Server("tutor")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        tools = []
        for spec in TOOL_SPECS:
            tools.append(
                Tool(
                    name=spec["name"],
                    description=spec["description"],
                    inputSchema=spec["model"].model_json_schema(),
                )
            )
        return tools

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[TextContent]:
        spec = TOOLS_BY_NAME.get(name)
        if spec is None:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        try:
            args = spec["model"].model_validate(arguments or {})
            result = await spec["handler"](args)
            return _text(result)
        except Exception as exc:
            return [
                TextContent(type="text", text=f"Error: {type(exc).__name__}: {exc}")
            ]

    _ = list_tools, call_tool
    return server


async def main() -> None:
    await _ensure_db()
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
