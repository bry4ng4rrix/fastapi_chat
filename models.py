from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from typing import Optional, List
from datetime import datetime


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    sender_id: int = Field(foreign_key="user.id")
    receiver_id: int = Field(foreign_key="user.id")

    sender: Mapped[Optional["User"]] = Relationship(
        back_populates="messages_sent",
        sa_relationship_kwargs={"foreign_keys": "[Message.sender_id]"}
    )
    receiver: Mapped[Optional["User"]] = Relationship(
        back_populates="messages_received",
        sa_relationship_kwargs={"foreign_keys": "[Message.receiver_id]"}
    )


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_type=String(50))
    email: str = Field(sa_type=String(100), unique=True)
    password: str = Field(sa_type=String(100))

    messages_sent: Mapped[List[Message]] = Relationship(
        back_populates="sender",
        sa_relationship_kwargs={"foreign_keys": "[Message.sender_id]"}
    )
    messages_received: Mapped[List[Message]] = Relationship(
        back_populates="receiver",
        sa_relationship_kwargs={"foreign_keys": "[Message.receiver_id]"}
    )

class UserCreate(SQLModel):
    name: str
    email: str
    password: str


class UserRead(SQLModel):
    id: int
    name: str
    email: str