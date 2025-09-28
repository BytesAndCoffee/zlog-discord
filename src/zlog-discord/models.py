from sqlalchemy import BigInteger, Column, DateTime, Index, Integer, JSON, String, Text, text
from sqlalchemy.dialects.mysql import TEXT, VARCHAR
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class EventLog(Base):
    __tablename__ = 'event_log'
    __table_args__ = (
        Index('user', 'user'),
    )

    id = mapped_column(Integer, primary_key=True)
    network = mapped_column(String(128), nullable=False)
    window = mapped_column(VARCHAR(255), nullable=False)
    type = mapped_column(VARCHAR(32), nullable=False)
    user = mapped_column(VARCHAR(128))
    nick = mapped_column(VARCHAR(128))
    message = mapped_column(TEXT)
    recipient = mapped_column(String(64), server_default=text("'self'"))


class Inbound(Base):
    __tablename__ = 'inbound'
    __table_args__ = (
        Index('inbound_tg_id_uindex', 'tg_id', unique=True),
    )

    id = mapped_column(Integer, primary_key=True)
    user = mapped_column(String(128), nullable=False)
    network = mapped_column(String(128), nullable=False)
    window = mapped_column(String(255), nullable=False)
    type = mapped_column(String(32), nullable=False)
    nick = mapped_column(String(128), nullable=False)
    message = mapped_column(Text, nullable=False)
    tg_id = mapped_column(Integer, nullable=False)


class InboundLog(Base):
    __tablename__ = 'inbound_log'

    id = mapped_column(Integer, primary_key=True)
    user = mapped_column(String(128), nullable=False)
    network = mapped_column(String(128), nullable=False)
    window = mapped_column(String(255), nullable=False)
    type = mapped_column(String(32), nullable=False)
    nick = mapped_column(String(128), nullable=False)
    message = mapped_column(Text, nullable=False)
    tg_id = mapped_column(Integer, nullable=False)


class Lastread(Base):
    __tablename__ = 'lastread'
    __table_args__ = (
        Index('lastread_table_uindex', 'table', unique=True),
    )

    table = mapped_column(String(32), primary_key=True)
    id = mapped_column(Integer)


class Logs(Base):
    __tablename__ = 'logs'
    __table_args__ = (
        Index('analytics_idx', 'window', 'created_at', 'nick'),
        Index('created_at', 'created_at'),
        Index('network', 'network'),
        Index('nick_idx', 'nick'),
        Index('type_idx', 'type'),
        Index('user', 'user'),
        Index('window_idx', 'window'),
        Index('window_nick_idx', 'window', 'nick')
    )

    id = mapped_column(Integer, primary_key=True)
    created_at = mapped_column(DateTime, nullable=False)
    window = mapped_column(VARCHAR(255), nullable=False)
    type = mapped_column(VARCHAR(32), nullable=False)
    user = mapped_column(VARCHAR(128))
    network = mapped_column(VARCHAR(128))
    nick = mapped_column(VARCHAR(128))
    message = mapped_column(TEXT)


class LogsIdTrack(Base):
    __tablename__ = 'logs_id_track'

    id = mapped_column(Integer, primary_key=True)
    tid = mapped_column(Integer, nullable=False)


class LogsQueue(Base):
    __tablename__ = 'logs_queue'
    __table_args__ = (
        Index('created_at', 'created_at'),
        Index('network', 'network'),
        Index('nick_idx', 'nick'),
        Index('type_idx', 'type'),
        Index('user', 'user'),
        Index('window_idx', 'window'),
        Index('window_nick_idx', 'window', 'nick')
    )

    id = mapped_column(Integer, primary_key=True)
    created_at = mapped_column(DateTime, nullable=False)
    window = mapped_column(VARCHAR(255), nullable=False)
    type = mapped_column(VARCHAR(32), nullable=False)
    user = mapped_column(VARCHAR(128))
    network = mapped_column(VARCHAR(128))
    nick = mapped_column(VARCHAR(128))
    message = mapped_column(TEXT)


class PmTable(Base):
    __tablename__ = 'pm_table'
    __table_args__ = (
        Index('nick_idx', 'nick'),
        Index('window_idx', 'window')
    )

    id = mapped_column(Integer, primary_key=True)
    window = mapped_column(VARCHAR(255), nullable=False)
    nick = mapped_column(VARCHAR(128))


class Push(Base):
    __tablename__ = 'push'
    __table_args__ = (
        Index('user', 'user'),
    )

    id = mapped_column(Integer, primary_key=True)
    network = mapped_column(String(128), nullable=False)
    window = mapped_column(VARCHAR(255), nullable=False)
    type = mapped_column(VARCHAR(32), nullable=False)
    user = mapped_column(VARCHAR(128))
    nick = mapped_column(VARCHAR(128))
    message = mapped_column(TEXT)
    recipient = mapped_column(String(64), server_default=text("'self'"))


class Users(Base):
    __tablename__ = 'users'

    nickname = mapped_column(String(64), primary_key=True)
    telegram_chat_id = mapped_column(BigInteger)
    hotwords = mapped_column(JSON)


class XkcdNicks(Base):
    __tablename__ = 'xkcd_nicks'

    nick = mapped_column(VARCHAR(128), primary_key=True)
