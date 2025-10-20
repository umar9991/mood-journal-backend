from pymongo.collection import Collection


def ensure_indexes(moods: Collection) -> None:
    """Create indexes for performant queries.

    - date descending for recent-first listing
    - mood text index for simple search
    """
    moods.create_index([("date", -1)])
    moods.create_index([("mood", "text"), ("note", "text")], name="mood_note_text")


