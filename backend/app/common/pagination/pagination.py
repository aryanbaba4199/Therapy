"""Reusable pagination parameter and metadata models."""

import math
from collections.abc import Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    page: int = Field(default=1, ge=1, description="1-indexed page number")
    limit: int = Field(default=10, ge=1, le=100, description="Items per page")

    @property
    def skip(self) -> int:
        """Compute database offset."""
        return (self.page - 1) * self.limit


class PaginationMeta(BaseModel):
    """Standard pagination metadata block."""

    page: int = Field(description="Current page number")
    limit: int = Field(description="Number of items requested per page")
    total_items: int = Field(description="Total count of matching items")
    total_pages: int = Field(description="Calculated total pages")
    has_next: bool = Field(description="True if another page is available")
    has_prev: bool = Field(description="True if a previous page exists")

    @classmethod
    def create(cls, page: int, limit: int, total_items: int) -> "PaginationMeta":
        """Factory method to calculate pagination metadata."""
        total_pages = math.ceil(total_items / limit) if limit > 0 else 1
        return cls(
            page=page,
            limit=limit,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


class PaginatedData(BaseModel, Generic[T]):
    """Container for paginated items and metadata."""

    items: Sequence[T] = Field(description="List of records for the current page")
    pagination: PaginationMeta = Field(description="Pagination indicators")
