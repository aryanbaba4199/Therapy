"""Review and Feedback domain constants and enumerations."""

from enum import StrEnum


class ReviewStatus(StrEnum):
    """Operational publication and moderation state of a review."""

    PUBLISHED = "published"
    HIDDEN = "hidden"
    FLAGGED = "flagged"
