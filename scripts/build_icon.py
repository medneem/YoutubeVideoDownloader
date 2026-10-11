"""Generate a multi-resolution ICO from the project's SVG icon."""
import os
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

def main():
    root = Path(__file__).resolve().parent.parent
    svg = root / "assets" / "app.svg"
    app = QGuiApplication.instance() or QGuiApplication([])
    renderer = QSvgRenderer(str(svg))
    if not renderer.isValid():
        raise RuntimeError("Invalid application SVG")
    image = QImage(1024, 1024, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    png = root / "assets" / "app.png"
    ico = root / "assets" / "app.ico"
    if not image.save(str(png), "PNG"):
        raise RuntimeError("Cannot write app.png")
    with Image.open(png) as artwork:
        artwork.convert("RGBA").save(ico, format="ICO",
            sizes=[(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)])
    if ico.stat().st_size == 0:
        raise RuntimeError("Empty application ICO")
    print(f"Icon generated: {ico}")

if __name__ == "__main__":
    main()
