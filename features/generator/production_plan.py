"""Planejamento compartilhado entre a prévia e a geração de folhas."""

from dataclasses import dataclass
from typing import Any, Sequence

from .imposition import SheetAssembler


@dataclass(frozen=True)
class ImpositionPlan:
    assembler: SheetAssembler
    pages: tuple[tuple[Any, ...], ...]

    @property
    def capacity(self) -> int:
        return self.assembler.capacity


def build_imposition_plan(items: Sequence[Any], settings: dict) -> ImpositionPlan:
    """Divide uma sequência na mesma malha física usada para montar as folhas."""
    assembler = SheetAssembler(
        settings.get("target_w_mm", 100),
        settings.get("target_h_mm", 150),
        settings.get("sheet_w_mm", 210.0),
        settings.get("sheet_h_mm", 297.0),
        settings.get("crop_marks", True),
        settings.get("bleed_margin", False),
    )
    if assembler.capacity <= 0:
        return ImpositionPlan(assembler, ())

    pages = tuple(
        tuple(items[start:start + assembler.capacity])
        for start in range(0, len(items), assembler.capacity)
    )
    return ImpositionPlan(assembler, pages)
