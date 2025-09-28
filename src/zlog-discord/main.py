"""Entry point for the Discord push notification bot."""

from __future__ import annotations

import logging
import os
from typing import Final

import discord
from dotenv import load_dotenv

from .discord_bot import (
    PushQueueDiscordClient,
    create_session_factory,
    parse_channel_map,
)


def _configure_logging() -> None:
    """Configure structured logging for the bot."""

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _read_int_env(var_name: str) -> int:
    """Read an integer environment variable, raising if missing or invalid."""

    value = os.getenv(var_name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {var_name}")
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {var_name} must be an integer") from exc


def main() -> None:
    """Run the Discord bot that forwards push notifications."""

    load_dotenv()
    _configure_logging()

    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing required environment variable: DISCORD_BOT_TOKEN")

    default_channel_id: Final[int] = _read_int_env("DISCORD_DEFAULT_CHANNEL_ID")
    poll_interval_env = os.getenv("PUSH_POLL_INTERVAL", "5")
    try:
        poll_interval = float(poll_interval_env)
    except ValueError as exc:
        raise RuntimeError("PUSH_POLL_INTERVAL must be a number") from exc
    if poll_interval <= 0:
        raise RuntimeError("PUSH_POLL_INTERVAL must be greater than zero")

    session_factory = create_session_factory()
    channel_map = parse_channel_map(os.getenv("DISCORD_CHANNEL_MAP"))

    intents = discord.Intents.default()
    client = PushQueueDiscordClient(
        session_factory=session_factory,
        channel_map=channel_map,
        default_channel_id=default_channel_id,
        poll_interval=poll_interval,
        intents=intents,
    )

    client.run(token)


if __name__ == "__main__":
    main()
