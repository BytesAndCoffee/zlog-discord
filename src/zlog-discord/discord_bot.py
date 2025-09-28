"""Discord bot for forwarding push queue notifications."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import discord
from discord.abc import Messageable
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import Engine, URL
from sqlalchemy.orm import Session, sessionmaker

from .models import Push

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PushNotification:
    """Container for data fetched from the ``push`` queue."""

    id: int
    network: str
    window: str
    type: str
    user: Optional[str]
    nick: Optional[str]
    message: Optional[str]
    recipient: Optional[str]

    def to_discord_message(self) -> str:
        """Format the notification for delivery to Discord."""

        header = f"[{self.network}] {self.window} ({self.type})"
        author = self.nick or self.user or "Unknown"
        body = self.message or ""
        content = f"{header}\n{author}: {body}".strip()
        if len(content) > 2000:
            truncated = content[:1997] + "..."
            LOGGER.warning("Push %s message truncated to fit Discord limits", self.id)
            return truncated
        return content


class PushQueueDiscordClient(discord.Client):
    """Discord client that forwards rows from the ``push`` queue."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        channel_map: Dict[str, int],
        default_channel_id: int,
        poll_interval: float,
        **kwargs: object,
    ) -> None:
        intents = kwargs.pop("intents", discord.Intents.default())
        super().__init__(intents=intents, **kwargs)
        self._session_factory = session_factory
        self._channel_map = channel_map
        self._default_channel_id = default_channel_id
        self._poll_interval = poll_interval
        self._forwarding_task: Optional[asyncio.Task[None]] = None
        self._channel_cache: Dict[int, Messageable] = {}

    async def setup_hook(self) -> None:  # type: ignore[override]
        """Start the background task after the bot logs in."""

        self._forwarding_task = asyncio.create_task(self._forward_notifications_loop())

    async def close(self) -> None:  # type: ignore[override]
        """Cancel the background task before closing the client."""

        if self._forwarding_task is not None:
            self._forwarding_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._forwarding_task
        await super().close()

    async def _forward_notifications_loop(self) -> None:
        """Continuously poll the database for pending notifications."""

        await self.wait_until_ready()
        while not self.is_closed():
            try:
                notifications = await asyncio.to_thread(self._fetch_pending_notifications)
                if notifications:
                    await self._deliver_notifications(notifications)
            except Exception:  # noqa: BLE001 - log unexpected errors
                LOGGER.exception("Unexpected error while forwarding notifications")
            await asyncio.sleep(self._poll_interval)

    def _fetch_pending_notifications(self) -> list[PushNotification]:
        """Retrieve pending push notifications from the database."""

        with self._session_factory() as session:
            rows = session.execute(select(Push).order_by(Push.id)).scalars().all()
        return [
            PushNotification(
                id=row.id,
                network=row.network,
                window=row.window,
                type=row.type,
                user=row.user,
                nick=row.nick,
                message=row.message,
                recipient=row.recipient,
            )
            for row in rows
        ]

    async def _deliver_notifications(self, notifications: Iterable[PushNotification]) -> None:
        """Send notifications to Discord and delete them once delivered."""

        for notification in notifications:
            channel_id = self._resolve_channel_id(notification.recipient)
            if channel_id is None:
                LOGGER.error(
                    "Skipping push %s because no channel mapping exists for recipient %s",
                    notification.id,
                    notification.recipient,
                )
                continue

            channel = await self._fetch_channel(channel_id)
            if channel is None:
                LOGGER.error(
                    "Skipping push %s because channel %s could not be fetched",
                    notification.id,
                    channel_id,
                )
                continue

            try:
                await channel.send(notification.to_discord_message())
            except Exception:  # noqa: BLE001 - log and retry next iteration
                LOGGER.exception("Failed to send push %s to Discord", notification.id)
                continue

            await asyncio.to_thread(self._delete_push_row, notification.id)

    def _delete_push_row(self, row_id: int) -> None:
        """Delete a processed push row from the queue."""

        with self._session_factory.begin() as session:
            session.execute(delete(Push).where(Push.id == row_id))

    def _resolve_channel_id(self, recipient: Optional[str]) -> Optional[int]:
        """Determine the Discord channel ID for the given recipient."""

        if recipient and recipient in self._channel_map:
            return self._channel_map[recipient]
        if recipient and recipient != "self":
            LOGGER.warning(
                "Recipient %s not in channel map; using default channel %s",
                recipient,
                self._default_channel_id,
            )
        return self._default_channel_id

    async def _fetch_channel(self, channel_id: int) -> Optional[Messageable]:
        """Fetch and cache a Discord channel by its ID."""

        if channel_id in self._channel_cache:
            return self._channel_cache[channel_id]

        channel = self.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.fetch_channel(channel_id)
            except Exception:  # noqa: BLE001 - log failure for visibility
                LOGGER.exception("Failed to fetch channel %s", channel_id)
                return None

        if isinstance(channel, Messageable):
            self._channel_cache[channel_id] = channel
            return channel

        LOGGER.error("Channel %s is not messageable", channel_id)
        return None


def create_session_factory() -> sessionmaker[Session]:
    """Create a SQLAlchemy session factory using environment variables."""

    username = os.getenv("DATABASE_USERNAME")
    password = os.getenv("DATABASE_PASSWORD")
    host = os.getenv("DATABASE_HOST")
    database = os.getenv("DATABASE")

    if not all([username, password, host, database]):
        raise RuntimeError(
            "Missing one or more database env vars: DATABASE_USERNAME, DATABASE_PASSWORD, "
            "DATABASE_HOST, DATABASE"
        )
    engine = _create_engine(username, password, host, database)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _create_engine(username: str, password: str, host: str, database: str) -> Engine:
    """Build the SQLAlchemy engine for the push queue database."""

    url = URL.create(
        "mysql+pymysql",
        username=username,
        password=password,
        host=host,
        database=database,
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


def parse_channel_map(raw_mapping: Optional[str]) -> Dict[str, int]:
    """Parse the ``DISCORD_CHANNEL_MAP`` configuration string."""

    mapping: Dict[str, int] = {}
    if not raw_mapping:
        return mapping

    for entry in raw_mapping.split(","):
        if not entry.strip():
            continue
        if "=" not in entry:
            LOGGER.warning("Ignoring malformed channel mapping entry: %s", entry)
            continue
        recipient, channel_id = (part.strip() for part in entry.split("=", 1))
        if not recipient or not channel_id:
            LOGGER.warning("Ignoring malformed channel mapping entry: %s", entry)
            continue
        try:
            mapping[recipient] = int(channel_id)
        except ValueError:
            LOGGER.warning(
                "Invalid channel ID '%s' for recipient '%s' in DISCORD_CHANNEL_MAP",
                channel_id,
                recipient,
            )
    return mapping
