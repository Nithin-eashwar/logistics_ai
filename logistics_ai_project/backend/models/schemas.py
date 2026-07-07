"""Pydantic models for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Order(BaseModel):
    """A single delivery order."""

    id: str = Field(min_length=1, max_length=32, description="Unique order identifier")
    lat: float = Field(ge=-90, le=90, description="Latitude in degrees")
    lng: float = Field(ge=-180, le=180, description="Longitude in degrees")
    weight: float = Field(gt=0, le=500, description="Weight of the order in kg")
    priority: int = Field(ge=1, le=10, description="Priority from 1 (low) to 10 (high)")
    deadline: Optional[datetime] = Field(
        default=None,
        description="Optional delivery deadline (ISO 8601). Earlier deadlines increase urgency.",
    )
    destination: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Optional destination label for display",
    )

    @field_validator("id")
    @classmethod
    def id_must_be_alphanumeric(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Order id must not be blank")
        return cleaned


class OptimizeRequest(BaseModel):
    """Input payload for the /optimize endpoint."""

    orders: list[Order] = Field(min_length=1, max_length=100)

    @field_validator("orders")
    @classmethod
    def orders_must_have_unique_ids(cls, v: list[Order]) -> list[Order]:
        ids = [o.id for o in v]
        if len(ids) != len(set(ids)):
            raise ValueError("All order ids must be unique")
        return v


class VanRoute(BaseModel):
    """Optimized route for a single van."""

    id: str
    route: list[str]
    distance: float
    total_weight: float = 0.0
    order_count: int = 0


class OptimizeResponse(BaseModel):
    """Output payload from the /optimize endpoint."""

    vans: list[VanRoute]
    total_orders: int = 0
    total_distance: float = 0.0
    elapsed_ms: float = Field(
        default=0.0,
        description="Pipeline execution time in milliseconds",
    )
