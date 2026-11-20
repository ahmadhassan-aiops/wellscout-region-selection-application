"""A surveyed point: the three measurements, within the range seen in exploration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Site(BaseModel):
    region: int = Field(ge=0, le=2)
    f0: float = Field(ge=-35, le=35)
    f1: float = Field(ge=-35, le=35)
    f2: float = Field(ge=-30, le=30)

    def row(self) -> dict:
        return {"f0": self.f0, "f1": self.f1, "f2": self.f2}
