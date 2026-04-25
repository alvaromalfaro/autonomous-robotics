from PIL import Image, ImageDraw

# Map parameters
width_px = 200
height_px = 120
wall_thickness = 5

# ── rect_map ──────────────────────────────────────────────
img = Image.new("L", (width_px, height_px), 255)
draw = ImageDraw.Draw(img)

draw.rectangle([0, 0, width_px, wall_thickness], fill=0)
draw.rectangle([0, height_px - wall_thickness, width_px, height_px], fill=0)
draw.rectangle([0, 0, wall_thickness, height_px], fill=0)
draw.rectangle([width_px - wall_thickness, 0, width_px, height_px], fill=0)

img.save("rect_map.png")

# ── plus_map ──────────────────────────────────────────────
img = Image.new("L", (width_px, height_px), 255)
draw = ImageDraw.Draw(img)

draw.rectangle([0, 0, width_px, wall_thickness], fill=0)
draw.rectangle([0, height_px - wall_thickness, width_px, height_px], fill=0)
draw.rectangle([0, 0, wall_thickness, height_px], fill=0)
draw.rectangle([width_px - wall_thickness, 0, width_px, height_px], fill=0)

cx, cy = width_px // 2, height_px // 2  # (100, 60)
arm = 25
thickness = 8
half_t = thickness // 2

draw.rectangle([cx - arm, cy - half_t, cx + arm, cy + half_t], fill=0)
draw.rectangle([cx - half_t, cy - arm, cx + half_t, cy + arm], fill=0)

img.save("plus_map.png")

# ── line_map ──────────────────────────────────────────────
img = Image.new("L", (width_px, height_px), 255)
draw = ImageDraw.Draw(img)

draw.rectangle([0, 0, width_px, wall_thickness], fill=0)
draw.rectangle([0, height_px - wall_thickness, width_px, height_px], fill=0)
draw.rectangle([0, 0, wall_thickness, height_px], fill=0)
draw.rectangle([width_px - wall_thickness, 0, width_px, height_px], fill=0)

draw.rectangle([97, 40, 103, 80], fill=0)

img.save("line_map.png")
