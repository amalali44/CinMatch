"""Streaming MovieLens rating validation; no dataset download on import."""

import csv
import math
from dataclasses import dataclass
from typing import TextIO

REQUIRED_COLUMNS = ("userId", "movieId", "rating", "timestamp")
MAX_SPARK_ID = 2**31 - 1
MAX_TIMESTAMP = 2**63 - 1


@dataclass(frozen=True)
class Rating:
    user_id: int
    movie_id: int
    rating: float
    timestamp: int


def parse_rating(row: dict, line: int) -> Rating:
    """Validate MovieLens values and preserve IDs suitable for Spark ALS."""
    try:
        user_id = int(row["userId"])
        movie_id = int(row["movieId"])
        rating = float(row["rating"])
        timestamp = int(row["timestamp"])
        if not (0 < user_id <= MAX_SPARK_ID and 0 < movie_id <= MAX_SPARK_ID):
            raise ValueError("IDs must be positive signed 32-bit integers")
        if not math.isfinite(rating) or not (0.5 <= rating <= 5.0):
            raise ValueError("rating must be finite and between 0.5 and 5.0")
        if not (rating * 2).is_integer():
            raise ValueError("rating must use half-star increments")
        if not 0 <= timestamp <= MAX_TIMESTAMP:
            raise ValueError("timestamp must be a nonnegative signed 64-bit integer")
        return Rating(user_id, movie_id, rating, timestamp)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid rating at CSV line {line}: {exc}") from exc


def profile_ratings(stream: TextIO) -> dict:
    """Return basic quality statistics with constant working memory."""
    reader = csv.DictReader(stream, strict=True)
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)):
        raise ValueError("CSV contains duplicate column names")
    missing = sorted(set(REQUIRED_COLUMNS) - set(fields))
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(missing)}")
    count = 0
    total = 0.0
    minimum, maximum = math.inf, -math.inf
    earliest, latest = MAX_TIMESTAMP, 0
    try:
        for row in reader:
            if None in row:
                raise ValueError(f"Extra CSV values at line {reader.line_num}")
            value = parse_rating(row, reader.line_num)
            count += 1
            total += value.rating
            minimum, maximum = min(minimum, value.rating), max(maximum, value.rating)
            earliest, latest = min(earliest, value.timestamp), max(latest, value.timestamp)
    except csv.Error as exc:
        raise ValueError(f"Malformed CSV at line {reader.line_num}: {exc}") from exc
    if count == 0:
        raise ValueError("CSV contains no rating records")
    return {
        "schema_version": 1,
        "interactions": count,
        "rating": {"min": minimum, "max": maximum, "mean": total / count},
        "timestamp": {"min": earliest, "max": latest},
    }
