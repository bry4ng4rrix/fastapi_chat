from sqlmodel import SQLModel, Field, Relationship, String, DateTime
from typing import Optional, List
from datetime import datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_type=String(50))
    email: str = Field(sa_type=String(100), unique=True)
    password: str = Field(sa_type=String(100))

    # --- Relations ---
    messages: List["Message"] = Relationship(back_populates="user")

    messages_sent: List["Messageprive"] = Relationship(
        back_populates="sender",
        sa_relationship_kwargs={
            "cascade": "all, delete",
            "foreign_keys": "[Messageprive.sender_id]"
        }
    )

    messages_received: List["Messageprive"] = Relationship(
        back_populates="receiver",
        sa_relationship_kwargs={
            "cascade": "all, delete",
            "foreign_keys": "[Messageprive.receiver_id]"
        }
    )


class UserCreate(SQLModel):
    name: str
    email: str
    password: str


class UserRead(SQLModel):
    id: int
    name: str
    email: str


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    message: str = Field(sa_type=String(500))
    date_create: datetime = Field(sa_type=DateTime, default_factory=datetime.utcnow)
    user: Optional["User"] = Relationship(back_populates="messages")


class MessageCreate(SQLModel):
    user_id: int
    message: str
    date_create: Optional[datetime] = Field(default_factory=datetime.utcnow)


class MessageRead(SQLModel):
    id: int
    user_id: int
    message: str
    date_create: datetime


class Messageprive(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender_id: int = Field(foreign_key="user.id")
    receiver_id: int = Field(foreign_key="user.id")
    content: str
    timestamp: datetime = Field(sa_type=DateTime, default_factory=datetime.utcnow)
    is_read: bool = Field(default=False)

    sender: Optional[User] = Relationship(
        back_populates="messages_sent",
        sa_relationship_kwargs={"foreign_keys": "[Messageprive.sender_id]"}
    )
    receiver: Optional[User] = Relationship(
        back_populates="messages_received",
        sa_relationship_kwargs={"foreign_keys": "[Messageprive.receiver_id]"}
    )
