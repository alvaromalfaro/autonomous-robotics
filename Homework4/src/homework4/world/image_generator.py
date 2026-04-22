from PIL import Image, ImageDraw

# Map parameters
width_px = 200   # 10 m / 0.05
height_px = 120  # 6 m / 0.05
wall_thickness = 5  # pixels (~0.25 m)

# Create white image (free space)
img = Image.new("L", (width_px, height_px), 255)
draw = ImageDraw.Draw(img)

# Draw outer walls (black = occupied)
# Top
draw.rectangle([0, 0, width_px, wall_thickness], fill=0)
# Bottom
draw.rectangle([0, height_px - wall_thickness, width_px, height_px], fill=0)
# Left
draw.rectangle([0, 0, wall_thickness, height_px], fill=0)
# Right
draw.rectangle([width_px - wall_thickness, 0, width_px, height_px], fill=0)

# Save image
img.save("rect_map.png")