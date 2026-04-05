"""Stdio MCP server exposing tutor question database operations as typed tools."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import aiosqlite
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel

from mcp_tutor.settings import get_db_path

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    topic TEXT NOT NULL
);
"""

_SEED_SQL = """
INSERT OR IGNORE INTO questions (id, text, correct_answer, topic) VALUES
(1, 'What is recursion?', 'Recursion is a function calling itself until it reaches a base case', 'Algorithms'),
(2, 'What is Big O notation?', 'Big O describes the upper bound of an algorithm time complexity in the worst case', 'Algorithms'),
(3, 'What is the difference between stack and heap?', 'Stack is automatic memory for local variables, heap is dynamic memory for objects', 'Memory'),
(4, 'What does the HTTP GET method do?', 'GET requests data from a server without modifying it', 'Web'),
(5, 'What is the HTTP POST method?', 'POST sends data to a server to create a resource', 'Web'),
(6, 'What is a REST API?', 'REST is an architectural style for web services using HTTP methods and status codes', 'Web'),
(7, 'What is a hash table?', 'A hash table is a data structure that stores key-value pairs with average O(1) access', 'Data Structures'),
(8, 'What is a linked list?', 'A linked list is a linear structure where each element holds a reference to the next', 'Data Structures'),
(9, 'What is Docker?', 'Docker is a platform for containerizing applications, isolating the process and its dependencies', 'DevOps'),
(10, 'What is Git?', 'Git is a distributed version control system for tracking changes in source code', 'DevOps');
"""


async def _ensure_db(db_path: Path) -> None:
    """Create tables and seed demo data if the database is empty."""
    async with aiosqlite.connect(str(db_path)) as conn:
        await conn.execute(_SCHEMA_SQL)
        cursor = await conn.execute("SELECT COUNT(*) FROM questions")
        (count,) = await cursor.fetchone()
        if count == 0:
            await conn.executescript(_SEED_SQL)
        await conn.commit()


async def _get_random_question(topic: str | None) -> dict:
    async with aiosqlite.connect(str(get_db_path())) as conn:
        conn.row_factory = aiosqlite.Row
        if topic:
            cursor = await conn.execute(
                "SELECT id, text, topic FROM questions WHERE topic = ? ORDER BY RANDOM() LIMIT 1",
                (topic,),
            )
        else:
            cursor = await conn.execute(
                "SELECT id, text, topic FROM questions ORDER BY RANDOM() LIMIT 1"
            )
        row = await cursor.fetchone()
        if row is None:
            return {"error": "No questions found", "topic": topic}
        return {"id": row["id"], "text": row["text"], "topic": row["topic"]}


async def _check_answer(question_id: int, user_answer: str) -> dict:
    async with aiosqlite.connect(str(get_db_path())) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT correct_answer, text FROM questions WHERE id = ?",
            (question_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return {"error": f"Question with id={question_id} not found"}
        correct = row["correct_answer"]
        # Simple keyword overlap check — the LLM will do semantic evaluation
        correct_words = set(correct.lower().split())
        answer_words = set(user_answer.lower().split())
        overlap = len(correct_words & answer_words)
        total = len(correct_words)
        score = overlap / total if total > 0 else 0
        return {
            "question_id": question_id,
            "question": row["text"],
            "user_answer": user_answer,
            "correct_answer": correct,
            "keyword_overlap_score": round(score, 2),
        }


async def _get_all_topics() -> list[str]:
    async with aiosqlite.connect(str(get_db_path())) as conn:
        cursor = await conn.execute(
            "SELECT DISTINCT topic FROM questions ORDER BY topic"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def _add_question(text: str, correct_answer: str, topic: str) -> dict:
    async with aiosqlite.connect(str(get_db_path())) as conn:
        cursor = await conn.execute(
            "INSERT INTO questions (text, correct_answer, topic) VALUES (?, ?, ?)",
            (text, correct_answer, topic),
        )
        await conn.commit()
        return {
            "id": cursor.lastrowid,
            "text": text,
            "correct_answer": correct_answer,
            "topic": topic,
        }


async def _delete_question(question_id: int) -> dict:
    async with aiosqlite.connect(str(get_db_path())) as conn:
        cursor = await conn.execute(
            "SELECT id, text, topic FROM questions WHERE id = ?", (question_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return {"error": f"Question with id={question_id} not found"}
        await conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        await conn.commit()
        return {
            "id": row[0],
            "text": row[1],
            "topic": row[2],
            "status": "deleted",
        }


async def _update_question(
    question_id: int, text: str | None, correct_answer: str | None, topic: str | None
) -> dict:
    async with aiosqlite.connect(str(get_db_path())) as conn:
        cursor = await conn.execute(
            "SELECT id, text, correct_answer, topic FROM questions WHERE id = ?",
            (question_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return {"error": f"Question with id={question_id} not found"}

        new_text = text if text is not None else row[1]
        new_answer = correct_answer if correct_answer is not None else row[2]
        new_topic = topic if topic is not None else row[3]

        await conn.execute(
            "UPDATE questions SET text = ?, correct_answer = ?, topic = ? WHERE id = ?",
            (new_text, new_answer, new_topic, question_id),
        )
        await conn.commit()
        return {
            "id": question_id,
            "text": new_text,
            "correct_answer": new_answer,
            "topic": new_topic,
            "status": "updated",
        }


async def _delete_topic(topic: str) -> dict:
    async with aiosqlite.connect(str(get_db_path())) as conn:
        cursor = await conn.execute(
            "SELECT id, text, topic FROM questions WHERE topic = ?", (topic,)
        )
        rows = await cursor.fetchall()
        if not rows:
            return {"error": f"No questions found for topic '{topic}'"}
        count = len(rows)
        questions = [{"id": r[0], "text": r[1], "topic": r[2]} for r in rows]
        await conn.execute("DELETE FROM questions WHERE topic = ?", (topic,))
        await conn.commit()
        return {
            "status": "deleted",
            "topic": topic,
            "count": count,
            "questions": questions,
        }


async def _search_questions(keyword: str) -> dict:
    """Search questions by keyword in text or topic."""
    async with aiosqlite.connect(str(get_db_path())) as conn:
        pattern = f"%{keyword}%"
        cursor = await conn.execute(
            "SELECT id, text, topic FROM questions WHERE text LIKE ? OR topic LIKE ?",
            (pattern, pattern),
        )
        rows = await cursor.fetchall()
        if not rows:
            return {"error": f"No questions found matching '{keyword}'"}
        return {
            "keyword": keyword,
            "count": len(rows),
            "questions": [{"id": r[0], "text": r[1], "topic": r[2]} for r in rows],
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
        "description": "Update an existing question. Provide question_id and any fields to change (text, correct_answer, topic).",
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
            schema = spec["model"].model_json_schema()
            tools.append(
                Tool(
                    name=spec["name"],
                    description=spec["description"],
                    inputSchema=schema,
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
    db_path = get_db_path()
    await _ensure_db(db_path)
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
