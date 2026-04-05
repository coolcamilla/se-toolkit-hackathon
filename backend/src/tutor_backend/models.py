"""Pydantic models for the tutor backend."""

from __future__ import annotations

from pydantic import BaseModel


class Question(BaseModel):
    id: int
    text: str
    topic: str


class QuestionCreate(BaseModel):
    text: str
    correct_answer: str
    topic: str


class QuestionUpdate(BaseModel):
    text: str | None = None
    correct_answer: str | None = None
    topic: str | None = None


class AnswerRequest(BaseModel):
    question_id: int
    user_answer: str


class AnswerResponse(BaseModel):
    question_id: int
    question: str
    user_answer: str
    correct_answer: str
    keyword_overlap_score: float
    verdict: str
