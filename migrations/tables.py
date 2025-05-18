from typing import List, Dict, Any
import uuid
from datetime import datetime, date
from sqlmodel import Field, SQLModel, Relationship, JSON
from pydantic import EmailStr
from enum import Enum
from sqlalchemy.sql import text
from uuid import UUID

# Common field definitions to avoid repetition
def UUIDPrimaryKey():
    return Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True
    )

def CreatedAtField():
    return Field(
        default=None,
        nullable=False,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )

def UpdatedAtField():
    return Field(
        default=None,
        nullable=False,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP")
        }
    )

# Enums
class UserRole(str, PyEnum):
    USER = "user"
    ADMIN = "admin"

class QuizAttemptStatus(str, Enum):
    """Status options for quiz attempts."""
    PENDING = "pending"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ModuleProgressStatus(str, Enum):
    """Status options for module progress."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class QuestionType(str, Enum):
    """Types of quiz questions."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


class User(SQLModel, table=True):
    """Represents a user in the learning platform."""
    user_id: UUID = UUIDPrimaryKey()
    username: str
    first_name: str | None
    last_name: str | None
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str
    profile_picture_url: str | None = None
    level: int = 1
    points: int = 0
    created_at: datetime = CreatedAtField()
    updated_at: datetime = UpdatedAtField()
    google_id: str | None = Field(default=None, unique=True, index=True)
    notification_preferences: Dict[str, Any] | None = Field(default=None, sa_column=JSON)
    is_active: bool = Field(default=True)
    role: UserRole = Field(default=UserRole.USER)

    quiz_attempts: List["UserQuizAttempt"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete"})
    answers: List["UserAnswer"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete"})
    module_progress: List["UserModuleProgress"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete"})
    badges: List["UserBadge"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete"})
    leaderboard_snapshots: List["LeaderboardSnapshot"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete"})
    notifications: List["Notification"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete"})


class Admin(SQLModel, table=True):
    """Represents an admin who manages content and quizzes."""
    admin_id: UUID = UUIDPrimaryKey()
    name: str
    email: EmailStr = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = CreatedAtField()
    updated_at: datetime = UpdatedAtField()

    created_modules: List["LearningModule"] = Relationship(back_populates="creator", sa_relationship_kwargs={"cascade": "all, delete"})
    reviewed_quizzes: List["Quiz"] = Relationship(back_populates="reviewer", sa_relationship_kwargs={"cascade": "all, delete"})


class LearningModule(SQLModel, table=True):
    """Represents a learning module with content and quizzes."""
    module_id: UUID = UUIDPrimaryKey()
    title: str
    description: str | None = None
    category: str | None = None
    created_by: UUID | None = Field(default=None, foreign_key="admin.admin_id", index=True)
    created_at: datetime = CreatedAtField()
    updated_at: datetime = UpdatedAtField()
    estimated_duration_minutes: int | None = None

    creator: Admin | None = Relationship(back_populates="created_modules")
    content_items: List["ContentItem"] = Relationship(back_populates="module", sa_relationship_kwargs={"cascade": "all, delete"})
    quizzes: List["Quiz"] = Relationship(back_populates="module", sa_relationship_kwargs={"cascade": "all, delete"})
    progress: List["UserModuleProgress"] = Relationship(back_populates="module", sa_relationship_kwargs={"cascade": "all, delete"})
    llm_logs: List["LLMQuizGenerationLog"] = Relationship(back_populates="module", sa_relationship_kwargs={"cascade": "all, delete"})

    @property
    def file_count(self) -> int:
        """Derive file count from content items."""
        return len(self.content_items) if self.content_items else 0


class ContentItem(SQLModel, table=True):
    """Represents a content item within a learning module."""
    content_item_id: UUID = UUIDPrimaryKey()
    module_id: UUID = Field(foreign_key="learningmodule.module_id", index=True)
    title: str | None = None
    content_type: str
    content_data: str  # Sanitize to prevent XSS
    order_in_module: int | None = None
    created_at: datetime = CreatedAtField()

    module: LearningModule = Relationship(back_populates="content_items")
    progress_items: List["UserModuleProgress"] = Relationship(back_populates="last_content_item", sa_relationship_kwargs={"cascade": "all, delete"})


class Quiz(SQLModel, table=True):
    """Represents a quiz associated with a module or standalone."""
    quiz_id: UUID = UUIDPrimaryKey()
    module_id: UUID | None = Field(default=None, foreign_key="learningmodule.module_id", index=True)
    title: str
    description: str | None = None
    is_daily_quiz: bool = False
    generation_date: date | None = None
    created_by_llm: bool = True
    reviewed_by_admin_id: UUID | None = Field(default=None, foreign_key="admin.admin_id", index=True)
    created_at: datetime = CreatedAtField()
    updated_at: datetime = UpdatedAtField()

    module: LearningModule | None = Relationship(back_populates="quizzes")
    reviewer: Admin | None = Relationship(back_populates="reviewed_quizzes")
    questions: List["Question"] = Relationship(back_populates="quiz", sa_relationship_kwargs={"cascade": "all, delete"})
    attempts: List["UserQuizAttempt"] = Relationship(back_populates="quiz", sa_relationship_kwargs={"cascade": "all, delete"})
    llm_logs: List["LLMQuizGenerationLog"] = Relationship(back_populates="quiz", sa_relationship_kwargs={"cascade": "all, delete"})


class Question(SQLModel, table=True):
    """Represents a question in a quiz."""
    question_id: UUID = UUIDPrimaryKey()
    quiz_id: UUID = Field(foreign_key="quiz.quiz_id", index=True)
    question_text: str
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    llm_generated_explanation: str | None = None
    created_at: datetime = CreatedAtField()

    quiz: Quiz = Relationship(back_populates="questions")
    options: List["AnswerOption"] = Relationship(back_populates="question", sa_relationship_kwargs={"cascade": "all, delete"})
    answers: List["UserAnswer"] = Relationship(back_populates="question", sa_relationship_kwargs={"cascade": "all, delete"})


class AnswerOption(SQLModel, table=True):
    """Represents an answer option for a question."""
    option_id: UUID = UUIDPrimaryKey()
    question_id: UUID = Field(foreign_key="question.question_id", index=True)
    option_text: str
    is_correct: bool
    created_at: datetime = CreatedAtField()

    question: Question = Relationship(back_populates="options")


class UserQuizAttempt(SQLModel, table=True):
    """Represents a user's attempt at a quiz."""
    attempt_id: UUID = UUIDPrimaryKey()
    user_id: UUID = Field(foreign_key="user.user_id", index=True)
    quiz_id: UUID = Field(foreign_key="quiz.quiz_id", index=True)
    started_at: datetime = CreatedAtField()
    completed_at: datetime | None = None
    status: QuizAttemptStatus = QuizAttemptStatus.PENDING
    time_taken_seconds: int | None = None

    user: User = Relationship(back_populates="quiz_attempts")
    quiz: Quiz = Relationship(back_populates="attempts")
    answers: List["UserAnswer"] = Relationship(back_populates="attempt", sa_relationship_kwargs={"cascade": "all, delete"})

    @property
    def total_questions(self) -> int:
        """Derive total questions from quiz."""
        return len(self.quiz.questions) if self.quiz and self.quiz.questions else 0
    
    @property
    def correct_answers(self) -> int:
        """Count correct answers."""
        return sum(1 for answer in self.answers if answer.is_correct)
    
    @property
    def incorrect_answers(self) -> int:
        """Count incorrect answers."""
        return sum(1 for answer in self.answers if answer.is_correct is False)
    
    @property
    def score(self) -> int | None:
        """Calculate score based on correct answers."""
        if self.status != QuizAttemptStatus.COMPLETED:
            return None
        total = self.total_questions
        return int((self.correct_answers / total) * 100) if total > 0 else 0


class UserAnswer(SQLModel, table=True):
    """Represents a user's answer to a quiz question."""
    user_answer_id: UUID = UUIDPrimaryKey()
    attempt_id: UUID = Field(foreign_key="userquizattempt.attempt_id", index=True)
    question_id: UUID = Field(foreign_key="question.question_id", index=True)
    user_id: UUID = Field(foreign_key="user.user_id", index=True)
    selected_option_id: UUID | None = Field(default=None, foreign_key="answeroption.option_id", index=True)
    is_correct: bool | None = None
    answered_at: datetime = CreatedAtField()

    attempt: UserQuizAttempt = Relationship(back_populates="answers")
    question: Question = Relationship(back_populates="answers")
    user: User = Relationship(back_populates="answers")


class UserModuleProgress(SQLModel, table=True):
    """Tracks a user's progress in a learning module."""
    progress_id: UUID = UUIDPrimaryKey()
    user_id: UUID = Field(foreign_key="user.user_id", index=True)
    module_id: UUID = Field(foreign_key="learningmodule.module_id", index=True)
    status: ModuleProgressStatus = ModuleProgressStatus.NOT_STARTED
    last_content_item_id: UUID | None = Field(default=None, foreign_key="contentitem.content_item_id", index=True)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime = UpdatedAtField()

    user: User = Relationship(back_populates="module_progress")
    module: LearningModule = Relationship(back_populates="progress")
    last_content_item: ContentItem | None = Relationship(back_populates="progress_items")


class Badge(SQLModel, table=True):
    """Represents a badge that users can earn."""
    badge_id: UUID = UUIDPrimaryKey()
    name: str = Field(unique=True)
    description: str | None = None
    icon_url: str | None = None
    criteria: str | None = None
    created_at: datetime = CreatedAtField()

    earned_by: List["UserBadge"] = Relationship(back_populates="badge", sa_relationship_kwargs={"cascade": "all, delete"})


class UserBadge(SQLModel, table=True):
    """Represents a badge earned by a user."""
    user_badge_id: UUID = UUIDPrimaryKey()
    user_id: UUID = Field(foreign_key="user.user_id", index=True)
    badge_id: UUID = Field(foreign_key="badge.badge_id", index=True)
    earned_at: datetime = CreatedAtField()

    user: User = Relationship(back_populates="badges")
    badge: Badge = Relationship(back_populates="earned_by")


class LeaderboardSnapshot(SQLModel, table=True):
    """Captures a user's leaderboard status for a period."""
    snapshot_id: UUID = UUIDPrimaryKey()
    period_type: str
    period_start_date: date | None = Field(default=None, index=True)
    user_id: UUID = Field(foreign_key="user.user_id", index=True)
    rank: int
    points: int
    created_at: datetime = CreatedAtField()

    user: User = Relationship(back_populates="leaderboard_snapshots")


class Notification(SQLModel, table=True):
    """Represents a notification sent to a user."""
    notification_id: UUID = UUIDPrimaryKey()
    user_id: UUID = Field(foreign_key="user.user_id", index=True)
    notification_type: str
    message: str
    delivery_method: str | None = None
    status: str = "pending"
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None
    read_at: datetime | None = None
    created_at: datetime = CreatedAtField()

    user: User = Relationship(back_populates="notifications")


class LLMQuizGenerationLog(SQLModel, table=True):
    """Logs details of LLM-generated quizzes."""
    log_id: UUID = UUIDPrimaryKey()
    module_id: UUID | None = Field(default=None, foreign_key="learningmodule.module_id", index=True)
    prompt_used: str | None = None
    llm_response: Dict[str, Any] | None = Field(default=None, sa_column=JSON)
    generated_quiz_id: UUID | None = Field(default=None, foreign_key="quiz.quiz_id", index=True)
    status: str | None = None
    error_message: str | None = None
    created_at: datetime = CreatedAtField()

    module: LearningModule | None = Relationship(back_populates="llm_logs")
    quiz: Quiz | None = Relationship(back_populates="llm_logs")