from sqlalchemy import text


ACTIVITY_PER_CHANNEL_PER_DAY = text(
    """
    SELECT
        c.channel_id,
        c.channel_name,
        c.server_id,
        cds.date,
        cds.message_count,
        cds.active_users
    FROM channel_daily_stats AS cds
    JOIN channels AS c
        ON c.channel_id = cds.channel_id
    WHERE (
        CAST(:server_id AS TEXT) IS NULL
        OR cds.server_id = CAST(:server_id AS TEXT)
    )
    AND (
        CAST(:start_date AS DATE) IS NULL
        OR cds.date >= CAST(:start_date AS DATE)
    )
    AND (
        CAST(:end_date AS DATE) IS NULL
        OR cds.date <= CAST(:end_date AS DATE)
    )
    ORDER BY cds.date, c.server_id, c.channel_id
    LIMIT :limit
    OFFSET :offset
    """
)
