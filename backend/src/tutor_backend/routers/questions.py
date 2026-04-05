"""Question CRUD endpoints."""

from __future__ import annotations

import random

from fastapi import APIRouter, HTTPException

from tutor_backend.database import get_connection
from tutor_backend.models import (
    AnswerRequest,
    AnswerResponse,
    Question,
    QuestionCreate,
    QuestionUpdate,
)

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/random", response_model=Question)
async def get_random_question(topic: str | None = None):
    """Return a random question, optionally filtered by topic."""
    conn = get_connection()
    try:
        if topic:
            cursor = conn.execute(
                "SELECT id, text, topic FROM questions WHERE topic = ?", (topic,)
            )
        else:
            cursor = conn.execute("SELECT id, text, topic FROM questions")
        rows = cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No questions found")
        row = random.choice(rows)
        return Question(id=row["id"], text=row["text"], topic=row["topic"])
    finally:
        conn.close()


@router.get("/topics", response_model=list[str])
async def get_topics():
    """Return all available topics."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT DISTINCT topic FROM questions ORDER BY topic")
        return [row["topic"] for row in cursor.fetchall()]
    finally:
        conn.close()


@router.get("", response_model=list[Question])
async def list_questions():
    """Return all questions."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT id, text, topic FROM questions ORDER BY id")
        return [
            Question(id=row["id"], text=row["text"], topic=row["topic"])
            for row in cursor.fetchall()
        ]
    finally:
        conn.close()


@router.post("", response_model=Question, status_code=201)
async def create_question(data: QuestionCreate):
    """Add a new question."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO questions (text, correct_answer, topic) VALUES (?, ?, ?)",
            (data.text, data.correct_answer, data.topic),
        )
        conn.commit()
        return Question(id=cursor.lastrowid, text=data.text, topic=data.topic)
    finally:
        conn.close()


@router.put("/{question_id}", response_model=Question)
async def update_question(question_id: int, data: QuestionUpdate):
    """Update an existing question."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT id FROM questions WHERE id = ?", (question_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Question not found")

        updates: dict[str, str] = {}
        if data.text is not None:
            updates["text"] = data.text
        if data.correct_answer is not None:
            updates["correct_answer"] = data.correct_answer
        if data.topic is not None:
            updates["topic"] = data.topic

        if updates:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            conn.execute(
                f"UPDATE questions SET {set_clause} WHERE id = ?",
                (*updates.values(), question_id),
            )
            conn.commit()

        cursor = conn.execute(
            "SELECT id, text, topic FROM questions WHERE id = ?", (question_id,)
        )
        row = cursor.fetchone()
        return Question(id=row["id"], text=row["text"], topic=row["topic"])
    finally:
        conn.close()


@router.delete("/{question_id}", status_code=204)
async def delete_question(question_id: int):
    """Delete a question."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM questions WHERE id = ?", (question_id,)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Question not found")
    finally:
        conn.close()


@router.post("/check", response_model=AnswerResponse)
async def check_answer(req: AnswerRequest):
    """Check a user's answer against the correct answer using keyword overlap."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT correct_answer, text FROM questions WHERE id = ?",
            (req.question_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=404, detail=f"Question {req.question_id} not found"
            )

        correct = row["correct_answer"]
        correct_words = set(correct.lower().split())
        answer_words = set(req.user_answer.lower().split())
        overlap = len(correct_words & answer_words)
        total = len(correct_words)
        score = round(overlap / total, 2) if total > 0 else 0.0
        verdict = "✅ Correct" if score >= 0.6 else "❌ Incorrect"

        return AnswerResponse(
            question_id=req.question_id,
            question=row["text"],
            user_answer=req.user_answer,
            correct_answer=correct,
            keyword_overlap_score=score,
            verdict=verdict,
        )
    finally:
        conn.close()
