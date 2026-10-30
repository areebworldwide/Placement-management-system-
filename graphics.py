"""Hand-made graphics drawn with plain Tkinter (no image files, no extra packages).

* colour helpers      - mix / tint colours
* draw_rounded        - smooth, anti-aliased rounded rectangles (buttons, pills, circles)
* draw_icon / glyph   - small line icons used in the sidebar, cards and dialogs
* make_logo           - the application logo / window icon
"""
import tkinter as tk

import config

_images = {}  # keeps PhotoImages alive (Tkinter forgets images that are not referenced)
SAMPLES = 4   # anti-aliasing: 4 x 4 samples per pixel


# ====================================================================== colours
def to_hex(color):
    if isinstance(color, str) and color.startswith("#") and len(color) == 7:
        return color.lower()
    red, green, blue = tk._default_root.winfo_rgb(color)  # also understands names like "white"
    return "#%02x%02x%02x" % (red >> 8, green >> 8, blue >> 8)


def to_rgb(color):
    value = to_hex(color)
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def _blend(first, second, amount):
    """Mix two RGB tuples; amount=0 gives first, amount=1 gives second."""
    return "#%02x%02x%02x" % tuple(
        int(round(first[i] + (second[i] - first[i]) * amount)) for i in range(3))


def mix(color_a, color_b, amount):
    return _blend(to_rgb(color_a), to_rgb(color_b), amount)


def tint(color, amount=0.12, base="#FFFFFF"):
    """A very light version of a colour (used for icon circles and soft backgrounds)."""
    return mix(base, color, amount)


# ====================================================================== rounded shapes
def _covered(x, y, width, height, radius):
    """Is the point inside a rounded rectangle at (0, 0) of the given size?"""
    cx = min(max(x, radius), width - radius)
    cy = min(max(y, radius), height - radius)
    return (0 <= x <= width and 0 <= y <= height
            and (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius)


def _coverage(x, y, width, height, radius, shift=0):
    hits = 0
    for i in range(SAMPLES):
        for j in range(SAMPLES):
            sx = x + (i + 0.5) / SAMPLES - shift
            sy = y + (j + 0.5) / SAMPLES - shift
            if _covered(sx, sy, width, height, radius):
                hits += 1
    return hits / (SAMPLES * SAMPLES)


def _cap_image(side, height, radius, fill, bg, border):
    """Left or right end of a rounded shape, smoothed against the background colour."""
    key = (tk._default_root, side, height, radius, fill, bg, border)
    if key in _images:
        return _images[key]
    fill_rgb, bg_rgb = to_rgb(fill), to_rgb(bg)
    border_rgb = to_rgb(border) if border else None
    big = radius * 4
    rows = []
    for y in range(height):
        row = []
        for x in range(radius):
            xx = x if side == "left" else radius - 1 - x
            if radius <= y < height - radius and xx >= 2:
                row.append(fill)  # solid interior: no maths needed
                continue
            outer = _coverage(xx, y, big, height, radius)
            if border_rgb:
                inner = _coverage(xx, y, big - 2, height - 2, max(radius - 1, 0), shift=1)
                colour = _blend(bg_rgb, border_rgb, outer)
                colour = _blend(to_rgb(colour), fill_rgb, inner)
            else:
                colour = _blend(bg_rgb, fill_rgb, outer)
            row.append(colour)
        rows.append("{" + " ".join(row) + "}")
    image = tk.PhotoImage(width=radius, height=height)
    image.put(" ".join(rows))
    _images[key] = image
    return image


def draw_rounded(canvas, x, y, width, height, radius, fill, bg, border=None, tag="shape"):
    """Draw an anti-aliased rounded rectangle (a circle when width == height == 2 * radius)."""
    width, height = int(width), int(height)
    radius = max(1, min(int(radius), height // 2, width // 2))
    left = _cap_image("left", height, radius, fill, bg, border)
    right = _cap_image("right", height, radius, fill, bg, border)
    if width > 2 * radius:
        canvas.create_rectangle(x + radius - 1, y, x + width - radius + 1, y + height,
                                fill=fill, outline="", tags=tag)
        if border:
            canvas.create_line(x + radius, y, x + width - radius, y, fill=border, tags=tag)
            canvas.create_line(x + radius, y + height - 1, x + width - radius, y + height - 1,
                               fill=border, tags=tag)
    canvas.create_image(x, y, image=left, anchor="nw", tags=tag)
    canvas.create_image(x + width - radius, y, image=right, anchor="nw", tags=tag)


# ====================================================================== icons
def draw_icon(canvas, name, cx, cy, size, color, tag="icon"):
    """Draw a simple line icon centred at (cx, cy). Designed on a 24 x 24 grid."""
    k = size / 24.0
    ox, oy = cx - size / 2, cy - size / 2
    width = max(1.5, 1.9 * k)

    def pts(*values):
        return [(ox + v * k) if i % 2 == 0 else (oy + v * k) for i, v in enumerate(values)]

    def line(*values):
        canvas.create_line(*pts(*values), fill=color, width=width, capstyle="round",
                           joinstyle="round", tags=tag)

    def box(x0, y0, x1, y1, filled=False):
        canvas.create_rectangle(*pts(x0, y0, x1, y1), outline=color, width=width, tags=tag,
                                fill=color if filled else "")

    def oval(x0, y0, x1, y1, filled=False):
        canvas.create_oval(*pts(x0, y0, x1, y1), outline=color, width=width, tags=tag,
                           fill=color if filled else "")

    if name == "dashboard":
        for x0, y0 in ((3, 3), (14, 3), (3, 14), (14, 14)):
            box(x0, y0, x0 + 7, y0 + 7, filled=True)
    elif name == "students":
        oval(8, 3, 16, 11)
        canvas.create_arc(*pts(4, 14, 20, 30), start=0, extent=180, style="arc",
                          outline=color, width=width, tags=tag)
    elif name == "companies":
        box(4, 3, 15, 21)
        box(15, 10, 21, 21)
        for x0, y0 in ((7, 7), (10.5, 7), (7, 12), (10.5, 12)):
            box(x0, y0, x0 + 1.5, y0 + 1.5, filled=True)
    elif name == "jobs":
        box(3, 8, 21, 20)
        line(9, 8, 9, 5, 15, 5, 15, 8)
        line(3, 13.5, 21, 13.5)
    elif name == "eligibility":
        oval(3, 3, 21, 21)
        line(7.5, 12.5, 10.5, 15.5, 16.5, 9)
    elif name == "applications":
        box(5, 3, 19, 21)
        line(8.5, 9, 15.5, 9)
        line(8.5, 13, 15.5, 13)
        line(8.5, 17, 12.5, 17)
    elif name == "lock":
        box(5, 11, 19, 21)
        canvas.create_arc(*pts(8, 3, 16, 15), start=0, extent=180, style="arc",
                          outline=color, width=width, tags=tag)
    elif name == "check":
        line(5, 12.5, 10, 17.5, 19, 7)
    elif name == "cross":
        line(6, 6, 18, 18)
        line(18, 6, 6, 18)
    elif name == "dash":
        line(6, 12, 18, 12)


def draw_glyph(canvas, glyph, cx, cy, size, color, tag="glyph"):
    """Symbols used inside dialog icons."""
    if glyph == "check":
        draw_icon(canvas, "check", cx, cy, size * 1.1, color, tag)
    elif glyph == "x":
        draw_icon(canvas, "cross", cx, cy, size * 1.1, color, tag)
    elif glyph == "!":
        width = max(2, size / 7)
        canvas.create_line(cx, cy - size * 0.42, cx, cy + size * 0.1, fill=color, width=width,
                           capstyle="round", tags=tag)
        radius = width * 0.7
        canvas.create_oval(cx - radius, cy + size * 0.32 - radius, cx + radius,
                           cy + size * 0.32 + radius, fill=color, outline=color, tags=tag)
    elif glyph == "?":
        canvas.create_text(cx, cy, text="?", fill=color, tags=tag,
                           font=(config.FONT_SEMI, -int(size * 1.15), "bold"))
    elif glyph == "lock":
        draw_icon(canvas, "lock", cx, cy, size * 1.1, color, tag)


# ====================================================================== logo
def _in_polygon(x, y, points):
    inside, j = False, len(points) - 1
    for i in range(len(points)):
        xi, yi = points[i]
        xj, yj = points[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


# Graduation cap, drawn in a 0..1 square
_CAP_SHAPES = [
    [(0.50, 0.26), (0.88, 0.44), (0.50, 0.62), (0.12, 0.44)],
    [(0.29, 0.60), (0.50, 0.70), (0.71, 0.60), (0.71, 0.72), (0.50, 0.82), (0.29, 0.72)],
    [(0.835, 0.47), (0.87, 0.47), (0.87, 0.66), (0.835, 0.66)],
]


def make_logo(size, bg):
    """Rounded green badge with a white graduation cap. ``bg`` is the colour behind it."""
    key = (tk._default_root, "logo", size, bg)
    if key in _images:
        return _images[key]
    top, bottom = to_rgb("#1FC08A"), to_rgb(config.GREEN_DARK)
    bg_rgb, white = to_rgb(bg), (255, 255, 255)
    radius = size * 0.26
    samples = 3
    rows = []
    for y in range(size):
        base = _blend(top, bottom, y / max(size - 1, 1))
        row = []
        for x in range(size):
            square = cap = 0
            for i in range(samples):
                for j in range(samples):
                    sx, sy = x + (i + 0.5) / samples, y + (j + 0.5) / samples
                    if _covered(sx, sy, size, size, radius):
                        square += 1
                    ux, uy = sx / size, sy / size
                    if any(_in_polygon(ux, uy, shape) for shape in _CAP_SHAPES):
                        cap += 1
            total = samples * samples
            colour = _blend(bg_rgb, to_rgb(base), square / total)
            colour = _blend(to_rgb(colour), white, cap / total)
            row.append(colour)
        rows.append("{" + " ".join(row) + "}")
    image = tk.PhotoImage(width=size, height=size)
    image.put(" ".join(rows))
    _images[key] = image
    return image
