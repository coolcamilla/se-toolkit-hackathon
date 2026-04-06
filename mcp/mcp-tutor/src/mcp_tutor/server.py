"""Stdio MCP server for the tutor question database — PostgreSQL with LLM evaluation and progress tracking."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel
from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    select,
    func,
    text,
    DateTime,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone

from mcp_tutor.settings import (
    get_db_url,
    get_llm_api_key,
    get_llm_api_base,
    get_llm_model,
)

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


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    score = Column(Float, nullable=False)  # 0.0–1.0
    user_answer = Column(Text, nullable=False)
    feedback = Column(Text, nullable=True)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(func.count(Question.id)))
        count = result.scalar()
        if count == 0:
            session.add_all([Question(**q) for q in _SEED_DATA])
            await session.commit()
        await session.execute(
            text(
                "SELECT setval(pg_get_serial_sequence('questions', 'id'), COALESCE((SELECT MAX(id) FROM questions), 1), true)"
            )
        )
        await session.commit()


# ---------------------------------------------------------------------------
# LLM evaluation
# ---------------------------------------------------------------------------


async def _evaluate_answer_with_llm(
    question: str, correct_answer: str, user_answer: str
) -> dict:
    """Use LLM to semantically evaluate user answer. Returns score (0–100) and feedback."""
    api_key = get_llm_api_key()
    api_base = get_llm_api_base()
    model = get_llm_model()

    if not api_key:
        # Fallback: keyword overlap
        correct_words = set(correct_answer.lower().split())
        answer_words = set(user_answer.lower().split())
        overlap = len(correct_words & answer_words)
        total = len(correct_words)
        score = int((overlap / total * 100) if total > 0 else 0)
        return {
            "score": score,
            "feedback": "Keyword-based evaluation (LLM key not configured).",
            "key_concepts_missed": [],
        }

    prompt = (
        f"You are a tutor evaluating a student's answer.\n\n"
        f"Question: {question}\n"
        f"Correct answer: {correct_answer}\n"
        f"Student's answer: {user_answer}\n\n"
        f"Evaluate the student's answer on a scale of 0 to 100.\n"
        f"- 80-100: Correct — captures the key ideas, minor details may differ, synonyms are fine.\n"
        f"- 50-79: Partially correct — some key ideas present, but important concepts missing.\n"
        f"- 0-49: Incorrect — misses the main point or is too vague.\n\n"
        f"Minor omissions and synonyms should NOT be penalized heavily.\n\n"
        f"Return ONLY a JSON object with these fields (no other text):\n"
        f'{{"score": <0-100 integer>, "feedback": "<1-2 sentences explaining what is right and what is missing>", "key_concepts_missed": ["<concept1>", "<concept2>"]}}'
    )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

            # Parse JSON from response
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            result = json.loads(content)
            result["score"] = int(result.get("score", 0))
            result["feedback"] = result.get("feedback", "")
            result["key_concepts_missed"] = result.get("key_concepts_missed", [])
            return result

    except Exception as exc:
        # Fallback
        correct_words = set(correct_answer.lower().split())
        answer_words = set(user_answer.lower().split())
        overlap = len(correct_words & answer_words)
        total = len(correct_words)
        score = int((overlap / total * 100) if total > 0 else 0)
        return {
            "score": score,
            "feedback": f"LLM evaluation failed ({exc}), falling back to keyword overlap.",
            "key_concepts_missed": [],
        }


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
    """Legacy: returns keyword overlap score. Use evaluate_answer for LLM-based scoring."""
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
        # Delete related progress records
        await session.execute(
            text("DELETE FROM user_progress WHERE question_id = :qid"),
            {"qid": question_id},
        )
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
        # Delete related progress records for all questions in this topic
        question_ids = [q.id for q in rows]
        for qid in question_ids:
            await session.execute(
                text("DELETE FROM user_progress WHERE question_id = :qid"),
                {"qid": qid},
            )
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
# Progress tracking
# ---------------------------------------------------------------------------


async def _record_attempt(
    user_id: str, question_id: int, user_answer: str, score: int, feedback: str
) -> dict:
    async with async_session() as session:
        progress = UserProgress(
            user_id=user_id,
            question_id=question_id,
            score=score / 100.0,
            user_answer=user_answer,
            feedback=feedback,
        )
        session.add(progress)
        await session.commit()
        await session.refresh(progress)

        # Compute average score for this question
        result = await session.execute(
            select(func.avg(UserProgress.score), func.count(UserProgress.id)).where(
                UserProgress.user_id == user_id, UserProgress.question_id == question_id
            )
        )
        avg_score, total_attempts = result.one()
        return {
            "status": "recorded",
            "question_id": question_id,
            "score": score,
            "average_score": round(avg_score * 100, 1) if avg_score else None,
            "total_attempts": total_attempts,
        }


async def _get_weak_questions(
    user_id: str, topic: str | None = None, limit: int = 10
) -> dict:
    """Get questions with lowest average score for this user."""
    async with async_session() as session:
        subq = (
            select(
                UserProgress.question_id,
                func.avg(UserProgress.score).label("avg_score"),
                func.count(UserProgress.id).label("attempts"),
            )
            .where(UserProgress.user_id == user_id)
            .group_by(UserProgress.question_id)
            .subquery()
        )

        stmt = (
            select(Question, subq.c.avg_score, subq.c.attempts)
            .join(subq, Question.id == subq.c.question_id)
            .order_by(subq.c.avg_score.asc())
            .limit(limit)
        )

        if topic:
            stmt = stmt.where(Question.topic == topic)

        result = await session.execute(stmt)
        rows = result.all()

        if not rows:
            return {
                "error": "No attempt history found for this user",
                "user_id": user_id,
            }

        questions = [
            {
                "id": r[0].id,
                "text": r[0].text,
                "topic": r[0].topic,
                "average_score": round(float(r[1]) * 100, 1),
                "attempts": int(r[2]),
            }
            for r in rows
        ]
        return {"user_id": user_id, "weak_questions": questions}


async def _get_random_weighted(user_id: str, topic: str | None = None) -> dict:
    """Get a random question weighted toward weak areas. Questions with lower avg scores have higher chance."""
    async with async_session() as session:
        # Get all questions
        stmt = select(Question)
        if topic:
            stmt = stmt.where(Question.topic == topic)
        result = await session.execute(stmt)
        all_questions = result.scalars().all()

        if not all_questions:
            return {"error": "No questions found"}

        # Get user's average scores
        subq = (
            select(
                UserProgress.question_id,
                func.avg(UserProgress.score).label("avg_score"),
            )
            .where(UserProgress.user_id == user_id)
            .group_by(UserProgress.question_id)
            .subquery()
        )

        result = await session.execute(
            select(Question.id, subq.c.avg_score).outerjoin(
                subq, Question.id == subq.c.question_id
            )
        )
        score_map = {
            row[0]: float(row[1]) if row[1] is not None else None
            for row in result.all()
        }

        import random

        # Weight: unanswered questions get weight 3, low-score questions get high weight
        weights = []
        for q in all_questions:
            avg = score_map.get(q.id)
            if avg is None:
                weights.append(3.0)  # Never answered — high priority
            elif avg < 0.3:
                weights.append(2.5)
            elif avg < 0.5:
                weights.append(2.0)
            elif avg < 0.7:
                weights.append(1.5)
            else:
                weights.append(1.0)  # Good — low priority

        chosen = random.choices(all_questions, weights=weights, k=1)[0]
        avg = score_map.get(chosen.id)
        return {
            "id": chosen.id,
            "text": chosen.text,
            "topic": chosen.topic,
            "your_average_score": round(avg * 100, 1) if avg is not None else None,
            "mode": "weighted",
        }


async def _evaluate_answer(question_id: int, user_answer: str) -> dict:
    """Evaluate answer using LLM semantic scoring."""
    async with async_session() as session:
        result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        q = result.scalar_one_or_none()
        if q is None:
            return {"error": f"Question with id={question_id} not found"}

    evaluation = await _evaluate_answer_with_llm(q.text, q.correct_answer, user_answer)
    return {
        "question_id": question_id,
        "question": q.text,
        "correct_answer": q.correct_answer,
        "user_answer": user_answer,
        "score": evaluation["score"],
        "feedback": evaluation["feedback"],
        "key_concepts_missed": evaluation["key_concepts_missed"],
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


class RecordAttemptArgs(BaseModel):
    user_id: str
    question_id: int
    user_answer: str
    score: int  # 0-100
    feedback: str = ""


class GetWeakQuestionsArgs(BaseModel):
    user_id: str
    topic: str | None = None
    limit: int = 10


class GetRandomWeightedArgs(BaseModel):
    user_id: str
    topic: str | None = None


class EvaluateAnswerArgs(BaseModel):
    question_id: int
    user_answer: str


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


async def handle_record_attempt(args: RecordAttemptArgs) -> dict:
    return await _record_attempt(
        args.user_id, args.question_id, args.user_answer, args.score, args.feedback
    )


async def handle_get_weak_questions(args: GetWeakQuestionsArgs) -> dict:
    return await _get_weak_questions(args.user_id, args.topic, args.limit)


async def handle_get_random_weighted(args: GetRandomWeightedArgs) -> dict:
    return await _get_random_weighted(args.user_id, args.topic)


async def handle_evaluate_answer(args: EvaluateAnswerArgs) -> dict:
    return await _evaluate_answer(args.question_id, args.user_answer)


TOOL_SPECS = [
    {
        "name": "get_random_question",
        "description": "Get a random question from the tutor database. Optionally filter by topic.",
        "model": GetRandomQuestionArgs,
        "handler": handle_get_random_question,
    },
    {
        "name": "check_answer",
        "description": "Legacy: Check answer using keyword overlap. Use evaluate_answer for LLM scoring.",
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
    {
        "name": "evaluate_answer",
        "description": "Evaluate a user's answer using LLM semantic scoring. Returns score (0-100), feedback, and missed concepts.",
        "model": EvaluateAnswerArgs,
        "handler": handle_evaluate_answer,
    },
    {
        "name": "record_attempt",
        "description": "Record a quiz attempt: user_id, question_id, score (0-100). Used for progress tracking.",
        "model": RecordAttemptArgs,
        "handler": handle_record_attempt,
    },
    {
        "name": "get_weak_questions",
        "description": "Get the user's weakest questions (lowest average scores) for training mode.",
        "model": GetWeakQuestionsArgs,
        "handler": handle_get_weak_questions,
    },
    {
        "name": "get_random_weighted",
        "description": "Get a random question weighted toward weak areas. Unanswered and low-score questions have higher priority.",
        "model": GetRandomWeightedArgs,
        "handler": handle_get_random_weighted,
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
