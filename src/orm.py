from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column


class _Base(DeclarativeBase):
    pass


class Installation(_Base):
    __tablename__ = 'installations'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[str] = mapped_column()
    bot_token: Mapped[str] = mapped_column()
    bot_token_expires_at: Mapped[int] = mapped_column(nullable=True)  # Unix timestamp in UTC
    bot_started: Mapped[bool] = mapped_column()
    state: Mapped[str] = mapped_column(nullable=True)


class ActiveAlerts(_Base):
    __tablename__ = 'active_alerts'

    id: Mapped[str] = mapped_column(primary_key=True)
    state: Mapped[str] = mapped_column()


def init_db(engine):
    _Base.metadata.create_all(engine)
