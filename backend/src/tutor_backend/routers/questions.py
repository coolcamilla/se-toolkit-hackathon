"""Question CRUD endpoints."""

from __future__ import annotations

import random

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader
from fastapi import status, Security
from sqlalchemy import func, select

from tutor_backend.database import Question, async_session
from tutor_backend.models import (
    AnswerRequest,
    AnswerResponse,
    Question as QuestionSchema,
    QuestionCreate,
    QuestionUpdate,
)
from tutor_backend.settings import settings

router = APIRouter(prefix="/questions", tags=["questions"])

# API key dependency for write operations
api_key_scheme = APIKeyHeader(name="X-API-Key")


async def require_write(api_key: str = Security(api_key_scheme)):
    if not settings.api_key:
        return api_key
    if api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return api_key


@router.get("/random", response_model=QuestionSchema)
async def get_random_question(topic: str | None = None):
    """Return a random question, optionally filtered by topic."""
    async with async_session() as session:
        if topic:
            stmt = select(Question).where(Question.topic == topic)
        else:
            stmt = select(Question)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        if not rows:
            raise HTTPException(status_code=404, detail="No questions found")
        q = random.choice(rows)
        return QuestionSchema(id=q.id, text=q.text, topic=q.topic)


@router.get("/topics", response_model=list[str])
async def get_topics():
    """Return all available topics."""
    async with async_session() as session:
        result = await session.execute(
            select(Question.topic).distinct().order_by(Question.topic)
        )
        return [row[0] for row in result.all()]


@router.get("", response_model=list[QuestionSchema])
async def list_questions():
    """Return all questions."""
    async with async_session() as session:
        result = await session.execute(select(Question).order_by(Question.id))
        return [
            QuestionSchema(id=q.id, text=q.text, topic=q.topic)
            for q in result.scalars().all()
        ]


@router.post(
    "",
    response_model=QuestionSchema,
    status_code=201,
    dependencies=[Depends(require_write)],
)
async def create_question(data: QuestionCreate):
    """Add a new question."""
    async with async_session() as session:
        q = Question(
            text=data.text, correct_answer=data.correct_answer, topic=data.topic
        )
        session.add(q)
        await session.commit()
        await session.refresh(q)
        return QuestionSchema(id=q.id, text=q.text, topic=q.topic)


@router.put(
    "/{question_id}",
    response_model=QuestionSchema,
    dependencies=[Depends(require_write)],
)
async def update_question(question_id: int, data: QuestionUpdate):
    """Update an existing question."""
    async with async_session() as session:
        result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        q = result.scalar_one_or_none()
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")

        if data.text is not None:
            q.text = data.text
        if data.correct_answer is not None:
            q.correct_answer = data.correct_answer
        if data.topic is not None:
            q.topic = data.topic

        await session.commit()
        await session.refresh(q)
        return QuestionSchema(id=q.id, text=q.text, topic=q.topic)


@router.delete(
    "/{question_id}",
    status_code=204,
    dependencies=[Depends(require_write)],
)
async def delete_question(question_id: int):
    """Delete a question."""
    async with async_session() as session:
        result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        q = result.scalar_one_or_none()
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")
        await session.delete(q)
        await session.commit()


@router.post("/check", response_model=AnswerResponse)
async def check_answer(req: AnswerRequest):
    """Check a user's answer against the correct answer using keyword overlap."""
    async with async_session() as session:
        result = await session.execute(
            select(Question).where(Question.id == req.question_id)
        )
        q = result.scalar_one_or_none()
        if not q:
            raise HTTPException(
                status_code=404, detail=f"Question {req.question_id} not found"
            )

        correct_words = set(q.correct_answer.lower().split())
        answer_words = set(req.user_answer.lower().split())
        overlap = len(correct_words & answer_words)
        total = len(correct_words)
        score = round(overlap / total, 2) if total > 0 else 0.0
        verdict = "✅ Correct" if score >= 0.6 else "❌ Incorrect"

        return AnswerResponse(
            question_id=req.question_id,
            question=q.text,
            user_answer=req.user_answer,
            correct_answer=q.correct_answer,
            keyword_overlap_score=score,
            verdict=verdict,
        )
