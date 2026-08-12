from __future__ import annotations

import csv
import os
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = (
    PROJECT_ROOT
    / "data"
    / "discord"
    / "discord_analytics_dataset"
)

raw_db_url = os.getenv(
    "DATABASE_URL",
    "postgresql://exaqube:exaqube_dev@localhost:5432/exaqube",
)
DATABASE_URL = raw_db_url.replace("postgresql+asyncpg://", "postgresql://")



def read_csv(filename: str) -> list[dict[str, str]]:
    path = DATA_ROOT / filename

    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def clean(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    return value.strip()


def as_bool(value: str | None) -> bool | None:
    value = clean(value)

    if value is None:
        return None

    return value.lower() == "true"


def as_int(value: str | None) -> int | None:
    value = clean(value)

    if value is None:
        return None

    return int(float(value))


def load_servers(cur) -> None:
    rows = read_csv("servers.csv")

    values = [
        (
            r["server_id"],
            r["server_name"],
            clean(r["owner_id"]),
            r["creation_date"],
            r["region"],
            int(r["verification_level"]),
            int(r["default_message_notifications"]),
            int(r["explicit_content_filter"]),
            clean(r["system_channel_id"]),
            clean(r["afk_channel_id"]),
            as_int(r["afk_timeout"]),
            as_bool(r["widget_enabled"]),
            int(r["premium_tier"]),
            int(r["premium_subscription_count"]),
            int(r["approximate_member_count"]),
            int(r["approximate_presence_count"]),
        )
        for r in rows
    ]

    execute_values(
        cur,
        """
        INSERT INTO servers (
            server_id,
            server_name,
            owner_id,
            creation_date,
            region,
            verification_level,
            default_message_notifications,
            explicit_content_filter,
            system_channel_id,
            afk_channel_id,
            afk_timeout,
            widget_enabled,
            premium_tier,
            premium_subscription_count,
            approximate_member_count,
            approximate_presence_count
        )
        VALUES %s
        ON CONFLICT (server_id) DO UPDATE SET
            server_name = EXCLUDED.server_name,
            owner_id = EXCLUDED.owner_id,
            creation_date = EXCLUDED.creation_date,
            region = EXCLUDED.region,
            verification_level = EXCLUDED.verification_level,
            default_message_notifications =
                EXCLUDED.default_message_notifications,
            explicit_content_filter = EXCLUDED.explicit_content_filter,
            system_channel_id = EXCLUDED.system_channel_id,
            afk_channel_id = EXCLUDED.afk_channel_id,
            afk_timeout = EXCLUDED.afk_timeout,
            widget_enabled = EXCLUDED.widget_enabled,
            premium_tier = EXCLUDED.premium_tier,
            premium_subscription_count =
                EXCLUDED.premium_subscription_count,
            approximate_member_count =
                EXCLUDED.approximate_member_count,
            approximate_presence_count =
                EXCLUDED.approximate_presence_count
        """,
        values,
    )

    print(f"servers: {len(rows)}")


def load_channels(cur) -> None:
    rows = read_csv("channels.csv")

    values = [
        (
            r["channel_id"],
            r["server_id"],
            r["channel_name"],
            r["channel_type"],
            clean(r["topic"]),
            as_bool(r["nsfw"]),
            int(r["rate_limit_per_user"]),
            int(r["position"]),
        )
        for r in rows
    ]

    execute_values(
        cur,
        """
        INSERT INTO channels (
            channel_id,
            server_id,
            channel_name,
            channel_type,
            topic,
            nsfw,
            rate_limit_per_user,
            position
        )
        VALUES %s
        ON CONFLICT (channel_id) DO UPDATE SET
            server_id = EXCLUDED.server_id,
            channel_name = EXCLUDED.channel_name,
            channel_type = EXCLUDED.channel_type,
            topic = EXCLUDED.topic,
            nsfw = EXCLUDED.nsfw,
            rate_limit_per_user = EXCLUDED.rate_limit_per_user,
            position = EXCLUDED.position
        """,
        values,
    )

    print(f"channels: {len(rows)}")


def load_members(cur) -> None:
    source_rows = read_csv("members.csv")
    
    deduplicated: dict[tuple[str, str], dict[str, str]] = {}

    for row in source_rows:
        key = (row["server_id"], row["user_id"])
        deduplicated[key] = row
    
    rows = list(deduplicated.values())
    
    print(
        f"members: source={len(source_rows)}, "
        f"deduplicated={len(rows)}, "
        f"removed={len(source_rows) - len(rows)}"
    )

    values = [
        (
            r["user_id"],
            r["server_id"],
            r["username"],
            r["display_name"],
            clean(r["discriminator"]),
            clean(r["avatar_hash"]),
            as_bool(r["is_bot"]),
            r["join_date"],
            clean(r["last_active"]),
            clean(r["roles"]),
            int(r["messages_sent"]),
            int(r["voice_minutes"]),
            as_bool(r["is_owner"]),
        )
        for r in rows
    ]

    execute_values(
        cur,
        """
        INSERT INTO members (
            user_id,
            server_id,
            username,
            display_name,
            discriminator,
            avatar_hash,
            is_bot,
            join_date,
            last_active,
            roles,
            messages_sent,
            voice_minutes,
            is_owner
        )
        VALUES %s
        ON CONFLICT (server_id, user_id) DO UPDATE SET
            username = EXCLUDED.username,
            display_name = EXCLUDED.display_name,
            discriminator = EXCLUDED.discriminator,
            avatar_hash = EXCLUDED.avatar_hash,
            is_bot = EXCLUDED.is_bot,
            join_date = EXCLUDED.join_date,
            last_active = EXCLUDED.last_active,
            roles = EXCLUDED.roles,
            messages_sent = EXCLUDED.messages_sent,
            voice_minutes = EXCLUDED.voice_minutes,
            is_owner = EXCLUDED.is_owner
        """,
        values,
        page_size=1000,
    )

    print(f"members: {len(rows)}")


def load_daily_stats(cur) -> None:
    rows = read_csv("daily_stats.csv")

    values = [
        (
            r["server_id"],
            r["date"],
            int(r["total_messages"]),
            int(r["new_members"]),
            int(r["active_members"]),
            int(r["total_members"]),
            int(r["day_of_week"]),
            int(r["is_weekend"]),
        )
        for r in rows
    ]

    execute_values(
        cur,
        """
        INSERT INTO daily_stats (
            server_id,
            date,
            total_messages,
            new_members,
            active_members,
            total_members,
            day_of_week,
            is_weekend
        )
        VALUES %s
        ON CONFLICT (server_id, date) DO UPDATE SET
            total_messages = EXCLUDED.total_messages,
            new_members = EXCLUDED.new_members,
            active_members = EXCLUDED.active_members,
            total_members = EXCLUDED.total_members,
            day_of_week = EXCLUDED.day_of_week,
            is_weekend = EXCLUDED.is_weekend
        """,
        values,
        page_size=1000,
    )

    print(f"daily_stats: {len(rows)}")


def load_channel_daily_stats(cur) -> None:
    rows = read_csv("channel_daily_stats.csv")

    values = [
        (
            r["channel_id"],
            r["server_id"],
            r["date"],
            int(r["message_count"]),
            int(r["active_users"]),
        )
        for r in rows
    ]

    execute_values(
        cur,
        """
        INSERT INTO channel_daily_stats (
            channel_id,
            server_id,
            date,
            message_count,
            active_users
        )
        VALUES %s
        ON CONFLICT (channel_id, date) DO UPDATE SET
            server_id = EXCLUDED.server_id,
            message_count = EXCLUDED.message_count,
            active_users = EXCLUDED.active_users
        """,
        values,
        page_size=1000,
    )

    print(f"channel_daily_stats: {len(rows)}")


def load_messages(cur) -> None:
    rows = read_csv("messages_sample.csv")

    values = [
        (
            r["message_id"],
            r["server_id"],
            r["channel_id"],
            r["user_id"],
            r["timestamp"],
            r["content"],
            as_bool(r["has_attachment"]),
            as_bool(r["has_embed"]),
            int(r["reaction_count"]),
            as_bool(r["is_pinned"]),
            int(r["length"]),
        )
        for r in rows
    ]

    execute_values(
        cur,
        """
        INSERT INTO messages (
            message_id,
            server_id,
            channel_id,
            user_id,
            timestamp,
            content,
            has_attachment,
            has_embed,
            reaction_count,
            is_pinned,
            length
        )
        VALUES %s
        ON CONFLICT (message_id) DO UPDATE SET
            server_id = EXCLUDED.server_id,
            channel_id = EXCLUDED.channel_id,
            user_id = EXCLUDED.user_id,
            timestamp = EXCLUDED.timestamp,
            content = EXCLUDED.content,
            has_attachment = EXCLUDED.has_attachment,
            has_embed = EXCLUDED.has_embed,
            reaction_count = EXCLUDED.reaction_count,
            is_pinned = EXCLUDED.is_pinned,
            length = EXCLUDED.length
        """,
        values,
        page_size=1000,
    )

    print(f"messages: {len(rows)}")


def ensure_schema_created(cur) -> None:
    schema_path = PROJECT_ROOT / "db" / "schema.sql"
    if schema_path.exists():
        sql = schema_path.read_text(encoding="utf-8")
        cur.execute(sql)


def main() -> None:
    with psycopg2.connect(DATABASE_URL) as connection:
        with connection.cursor() as cur:
            ensure_schema_created(cur)
            load_servers(cur)
            load_channels(cur)
            load_members(cur)
            load_daily_stats(cur)
            load_channel_daily_stats(cur)
            load_messages(cur)

        connection.commit()

    print("Dataset load complete.")



if __name__ == "__main__":
    main()
