from datetime import datetime
from typing import Optional
from enum import Enum

from sqlmodel import Field, SQLModel
from pydantic import BaseModel


class WorkListRole(str, Enum):
    DENY = 0
    READ = 1
    WRITE = 2
    ADMIN = 3


class User(SQLModel, table=True):
    """
    Represents a user in the system.

    Attributes:
        id (int | None): The ID of the user. Defaults to None.
        username (str): The username of the user.
        email (str): The email address of the user.
        password (str): The password of the user.
        created_at (datetime | None): The creation date and time of the user. Defaults to the current datetime.
    """

    id: int | None = Field(default=None, primary_key=True)
    username: str
    email: str
    password: str
    # created_at: datetime | None = Field(default=datetime.today())


class UserSecure(BaseModel):
    id: int
    username: str
    email: str


class WorkList(SQLModel, table=True):
    """
    Represents a work list.

    Attributes:
        id (int | None): The ID of the work list. Defaults to None.
        name (str): The name of the work list.
        description (str | None): The description of the work list. Defaults to None.
        created_by (int): The ID of the user who created the work list.
        created_at (datetime | None): The timestamp when the work list was created. Defaults to the current datetime.
        updated_at (datetime | None): The timestamp when the work list was last updated. Defaults to the current datetime.
        updated_by (int): The ID of the user who last updated the work list.
        orders (list["Order"]): The list of orders associated with the work list.
    """

    class Config:
        validate_assignment = True

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(title="Name of work list")
    description: str | None = Field(default=None, title="Description")
    created_at: datetime | None = Field(default=datetime.now())
    created_by: int = Field(foreign_key="user.id")
    # updated_at: datetime | None = Field(default=datetime.now())
    # updated_by: int = Field(foreign_key="user.id")


class UserWorkList(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    worklist_id: int = Field(foreign_key="worklist.id")
    role: Optional[WorkListRole] = Field(default=WorkListRole.READ)


class OrderWorkList(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    order_id: int
    worklist_id: int = Field(foreign_key="worklist.id")


# engine: Engine = create_engine(url="sqlite:///restrack.db")


def create_db_and_tables(engine):
    SQLModel.metadata.create_all(bind=engine)
