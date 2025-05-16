from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker


db_connection_string="sqlite+aiosqlite:///database/notes.sqlite3"
engine = create_async_engine(db_connection_string, echo=True)
session_maker = sessionmaker(engine, autocommit=False, autoflush=False, expire_on_commit=False, class_=AsyncSession)


def create_session_async() -> sessionmaker[AsyncSession]:
    """
    Receive one async Database session to make transactions.
    Using is like:
    ```
    async with create_session_async() as session:
        session.add(some_object)
        session.commit()
    ```
    Must be used in only 1 task or thread.
    """
    return session_maker()
