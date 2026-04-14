"""Generate SMS Sender app icon."""
from PIL import Image, ImageDraw, ImageFont
import os


def generate_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background: rounded blue square
        margin = max(1, size // 16)
        bg_rect = [margin, margin, size - margin - 1, size - margin - 1]
        radius = size // 5
        draw.rounded_rectangle(bg_rect, radius=radius, fill="#2563EB")

        # Chat bubble (white)
        bx1 = size * 0.18
        by1 = size * 0.22
        bx2 = size * 0.82
        by2 = size * 0.62
        bubble_radius = size // 8
        draw.rounded_rectangle(
            [bx1, by1, bx2, by2],
            radius=bubble_radius,
            fill="white",
        )

        # Bubble tail (small triangle at bottom-left)
        tail_x = size * 0.28
        tail_y = by2 - 1
        tail_size = size * 0.10
        draw.polygon([
            (tail_x, tail_y),
            (tail_x - tail_size * 0.5, tail_y + tail_size),
            (tail_x + tail_size, tail_y),
        ], fill="white")

        # Three dots in bubble (typing indicator)
        dot_r = max(2, size // 20)
        dot_y = (by1 + by2) / 2
        dot_spacing = (bx2 - bx1) / 4
        for i in range(3):
            cx = bx1 + dot_spacing * (i + 1)
            draw.ellipse(
                [cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r],
                fill="#2563EB",
            )

        images.append(img)

    # Save as .ico with multiple sizes
    out_path = os.path.join(os.path.dirname(__file__), "..", "installer", "icon.ico")
    images[0].save(
        out_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"Icon saved: {os.path.abspath(out_path)}")

    # Also save PNG for use in app
    png_path = os.path.join(os.path.dirname(__file__), "..", "gui", "resources", "icon.png")
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    images[0].save(png_path, format="PNG")
    print(f"PNG saved: {os.path.abspath(png_path)}")


if __name__ == "__main__":
    generate_icon()
