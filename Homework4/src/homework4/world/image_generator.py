from PIL import Image, ImageDraw

# Map parameters
width_px = 200   # 10 m / 0.05
height_px = 120  # 6 m / 0.05
wall_thickness = 5  # pixels (~0.25 m)

# ── rect_map ──────────────────────────────────────────────
img = Image.new("L", (width_px, height_px), 255)
draw = ImageDraw.Draw(img)

draw.rectangle([0, 0, width_px, wall_thickness], fill=0)
draw.rectangle([0, height_px - wall_thickness, width_px, height_px], fill=0)
draw.rectangle([0, 0, wall_thickness, height_px], fill=0)
draw.rectangle([width_px - wall_thickness, 0, width_px, height_px], fill=0)

img.save("rect_map.png")

# ── x_map ─────────────────────────────────────────────────
# Obstacles are at pixel columns x=60 and x=140.
# X arms span [cx±arm] = [68, 132], staying clear of obstacle columns.
img = Image.new("L", (width_px, height_px), 255)
draw = ImageDraw.Draw(img)

draw.rectangle([0, 0, width_px, wall_thickness], fill=0)
draw.rectangle([0, height_px - wall_thickness, width_px, height_px], fill=0)
draw.rectangle([0, 0, wall_thickness, height_px], fill=0)
draw.rectangle([width_px - wall_thickness, 0, width_px, height_px], fill=0)

cx, cy = width_px // 2, height_px // 2  # (100, 60)
arm = 22    # half-length in pixels (~1.1 m)
thickness = 8  # wall thickness in pixels (~0.4 m)

draw.line([(cx - arm, cy - arm), (cx + arm, cy + arm)], fill=0, width=thickness)
draw.line([(cx + arm, cy - arm), (cx - arm, cy + arm)], fill=0, width=thickness)

img.save("x_map.png")

# ── hard_map ──────────────────────────────────────────────
# Cross-shaped internal walls divide the map into 4 rooms.
# All rooms connect through a single 24 px (1.2 m) central corridor.
# One obstacle per room: O2(60,30) O4(140,30) O1(60,90) O3(140,90)
img = Image.new("L", (width_px, height_px), 255)
draw = ImageDraw.Draw(img)

draw.rectangle([0, 0, width_px, wall_thickness], fill=0)
draw.rectangle([0, height_px - wall_thickness, width_px, height_px], fill=0)
draw.rectangle([0, 0, wall_thickness, height_px], fill=0)
draw.rectangle([width_px - wall_thickness, 0, width_px, height_px], fill=0)

# Horizontal wall at y=57-63, gap at x=[75, 125]  →  50 px (2.5 m)
draw.rectangle([5,   57, 75,  63], fill=0)   # left segment
draw.rectangle([125, 57, 195, 63], fill=0)   # right segment

# Vertical wall at x=97-103, gap at y=[45, 75]  →  30 px (1.5 m)
draw.rectangle([97, 5,   103, 44],  fill=0)  # top segment
draw.rectangle([97, 76,  103, 115], fill=0)  # bottom segment

img.save("hard_map.png")
