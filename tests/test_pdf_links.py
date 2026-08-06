import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from features.generator.pdf_links import inject_pdf_links


class Rect:
    def __init__(self, x, y, width, height):
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    def x(self):
        return self._x

    def y(self):
        return self._y

    def width(self):
        return self._width

    def height(self):
        return self._height


class PdfLinksTest(unittest.TestCase):
    def test_injects_links_on_multiple_pages_and_inverts_vertical_axis(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "multipage.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=300)
            writer.add_blank_page(width=200, height=300)
            writer.write(pdf_path)

            inserted = inject_pdf_links(
                pdf_path,
                {
                    0: [
                        {
                            "rect": Rect(100, 100, 200, 300),
                            "url": "https://example.com/top",
                        }
                    ],
                    1: [
                        {
                            "rect": Rect(500, 600, 250, 200),
                            "url": "https://example.com/bottom",
                        }
                    ],
                },
                canvas_width=1000,
                canvas_height=1000,
            )

            self.assertEqual(inserted, 2)

            reader = PdfReader(pdf_path)
            self.assertEqual(len(reader.pages), 2)

            first_link = reader.pages[0]["/Annots"][0].get_object()
            self.assertEqual(first_link["/A"]["/URI"], "https://example.com/top")
            self.assertEqual(
                [float(value) for value in first_link["/Rect"]],
                [20.0, 180.0, 60.0, 270.0],
            )

            second_link = reader.pages[1]["/Annots"][0].get_object()
            self.assertEqual(second_link["/A"]["/URI"], "https://example.com/bottom")
            self.assertEqual(
                [float(value) for value in second_link["/Rect"]],
                [100.0, 60.0, 150.0, 120.0],
            )

    def test_ignores_empty_links_and_out_of_range_pages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "single.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=300)
            writer.write(pdf_path)

            inserted = inject_pdf_links(
                pdf_path,
                {
                    0: [{"rect": Rect(0, 0, 100, 100), "url": "  "}],
                    3: [{"rect": Rect(0, 0, 100, 100), "url": "https://example.com"}],
                },
                canvas_width=1000,
                canvas_height=1000,
            )

            self.assertEqual(inserted, 0)
            reader = PdfReader(pdf_path)
            self.assertNotIn("/Annots", reader.pages[0])


if __name__ == "__main__":
    unittest.main()
