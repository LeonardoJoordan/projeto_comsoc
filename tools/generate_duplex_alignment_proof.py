"""Gera uma prova A4 frente/verso para validar alinhamento em impressão duplex."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QMarginsF, QRect, QSizeF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPageSize, QPainter, QPdfWriter, QPen
from PySide6.QtWidgets import QApplication

from features.generator.imposition import SheetAssembler
from features.generator.production_plan import build_imposition_plan


def _card(label: str, face: str) -> QImage:
    image = QImage(600, 840, QImage.Format_ARGB32)
    image.fill(QColor("#ffffff"))
    painter = QPainter(image)
    painter.setPen(QPen(QColor("#111111"), 8))
    painter.drawRect(4, 4, image.width() - 8, image.height() - 8)
    painter.setFont(QFont("Noto Sans", 96, QFont.Weight.Bold))
    painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, label)
    painter.setFont(QFont("Noto Sans", 28))
    painter.drawText(QRect(0, 24, image.width(), 60), Qt.AlignmentFlag.AlignCenter, face)
    painter.drawText(QRect(0, image.height() - 84, image.width(), 60), Qt.AlignmentFlag.AlignCenter, "BASE")
    painter.end()
    return image


def main() -> int:
    app = QApplication.instance() or QApplication([])
    output_dir = ROOT / ".validation" / "duplex_alignment_proof"
    output_dir.mkdir(parents=True, exist_ok=True)
    settings = {
        "target_w_mm": 90.0, "target_h_mm": 130.0,
        "sheet_w_mm": 210.0, "sheet_h_mm": 297.0,
        "crop_marks": True, "bleed_margin": False, "duplex": True,
    }
    plan = build_imposition_plan(["A", "B", "C"], settings)
    sheet = plan.sheets[0]
    assembler: SheetAssembler = plan.assembler
    front = assembler.render_sheet(
        [_card(value, "FRENTE") if value else None for value in sheet.front],
        preserve_slots=True,
    )
    back = assembler.render_sheet(
        [_card(value, "VERSO") if value else None for value in sheet.back],
        preserve_slots=True,
    )
    front.save(str(output_dir / "prova_frente.png"), "PNG")
    back.save(str(output_dir / "prova_verso.png"), "PNG")

    pdf_path = output_dir / "prova_duplex_a4.pdf"
    writer = QPdfWriter(str(pdf_path))
    writer.setPageSize(QPageSize(QSizeF(210, 297), QPageSize.Unit.Millimeter))
    layout = writer.pageLayout()
    layout.setMargins(QMarginsF(0, 0, 0, 0))
    writer.setPageLayout(layout)
    painter = QPainter(writer)
    painter.drawImage(layout.paintRectPixels(writer.resolution()), front)
    writer.newPage()
    painter.drawImage(layout.paintRectPixels(writer.resolution()), back)
    painter.end()
    print(pdf_path)
    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
