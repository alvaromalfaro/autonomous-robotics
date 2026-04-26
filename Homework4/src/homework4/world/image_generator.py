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

# ── two offset pillars ────────────────────────────────────
img = Image.new("L", (width_px, height_px), 255)
draw = ImageDraw.Draw(img)

draw.rectangle([0, 0, width_px, wall_thickness], fill=0)
draw.rectangle([0, height_px - wall_thickness, width_px, height_px], fill=0)
draw.rectangle([0, 0, wall_thickness, height_px], fill=0)
draw.rectangle([width_px - wall_thickness, 0, width_px, height_px], fill=0)

draw.rectangle([50, 36, 88, 54], fill=0)
draw.rectangle([112, 66, 150, 84], fill=0)

img.save("tp_map.png")

# ── line_map ──────────────────────────────────────────────
img = Image.new("L", (width_px, height_px), 255)
draw = ImageDraw.Draw(img)

draw.rectangle([0, 0, width_px, wall_thickness], fill=0)
draw.rectangle([0, height_px - wall_thickness, width_px, height_px], fill=0)
draw.rectangle([0, 0, wall_thickness, height_px], fill=0)
draw.rectangle([width_px - wall_thickness, 0, width_px, height_px], fill=0)

draw.rectangle([97, 40, 103, 80], fill=0)

img.save("line_map.png")
