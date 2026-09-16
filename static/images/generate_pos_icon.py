"""
Script to generate NexGen POS application icon with modern flat-style design
This script creates a clean, minimal, professional, and futuristic icon with:
- Rounded square background
- Shades of blue and green (tech + finance theme)
- Cash register / shopping cart / receipt + digital screen combination
- No text inside the icon
- High resolution (1024x1024)
- Exports as .ico and .png formats
"""

from PIL import Image, ImageDraw
import os

def create_modern_pos_icon():
    # Create a new 1024x1024 image with a transparent background
    size = 1024
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Define colors - shades of blue and green for tech + finance theme
    deep_blue = (27, 58, 87, 255)      # #1b3a57 - Deep navy blue
    medium_blue = (43, 120, 200, 255)  # #2b78c8 - Vibrant blue
    teal_green = (32, 201, 151, 255)   # #20c997 - Teal green
    light_teal = (100, 220, 180, 255)  # #64dcb4 - Light teal
    white = (255, 255, 255, 255)       # White
    light_gray = (240, 245, 250, 255)  # Light gray for highlights
    
    # Draw rounded square background
    corner_radius = 180  # Increased radius for more modern look
    draw.rounded_rectangle(
        [(0, 0), (size, size)], 
        radius=corner_radius, 
        fill=deep_blue
    )
    
    # Draw a subtle inner highlight for depth
    highlight_radius = corner_radius - 20
    draw.rounded_rectangle(
        [(20, 20), (size-20, size-20)], 
        radius=highlight_radius, 
        fill=None,
        outline=light_gray,
        width=5
    )
    
    # Draw digital screen (representing modern POS interface)
    screen_width = 600
    screen_height = 400
    screen_x = (size - screen_width) // 2
    screen_y = 200
    
    # Screen background with gradient effect
    draw.rounded_rectangle(
        [(screen_x, screen_y), (screen_x + screen_width, screen_y + screen_height)],
        radius=30,
        fill=white
    )
    
    # Screen content - abstract representation of data
    # Horizontal lines representing data
    line_y_start = screen_y + 60
    line_spacing = 50
    line_width = screen_width - 120
    
    for i in range(5):
        y_pos = line_y_start + i * line_spacing
        # Varying line lengths for visual interest
        width_factor = 0.7 + (i * 0.05)  # Lines get progressively longer
        actual_width = int(line_width * width_factor)
        x_start = screen_x + (screen_width - actual_width) // 2
        
        # Color coding for different data types
        if i == 0:
            line_color = medium_blue
        elif i == 1:
            line_color = teal_green
        elif i == 2:
            line_color = deep_blue
        else:
            line_color = light_teal
            
        draw.rounded_rectangle(
            [(x_start, y_pos), (x_start + actual_width, y_pos + 20)],
            radius=10,
            fill=line_color
        )
    
    # Draw cash register base (simplified, modern design)
    register_height = 200
    register_width = 700
    register_x = (size - register_width) // 2
    register_y = size - register_height - 150
    
    # Main register body
    draw.rounded_rectangle(
        [(register_x, register_y), (register_x + register_width, register_y + register_height)],
        radius=30,
        fill=medium_blue
    )
    
    # Cash drawer
    drawer_height = 100
    drawer_width = register_width - 100
    drawer_x = register_x + 50
    drawer_y = register_y + register_height - 30
    
    draw.rounded_rectangle(
        [(drawer_x, drawer_y), (drawer_x + drawer_width, drawer_y + drawer_height)],
        radius=20,
        fill=teal_green
    )
    
    # Drawer handle
    handle_width = 120
    handle_height = 20
    handle_x = drawer_x + (drawer_width - handle_width) // 2
    handle_y = drawer_y + (drawer_height - handle_height) // 2
    
    draw.rounded_rectangle(
        [(handle_x, handle_y), (handle_x + handle_width, handle_y + handle_height)],
        radius=10,
        fill=white
    )
    
    # Draw shopping cart element (integrated with register)
    # Cart base
    cart_width = 180
    cart_height = 120
    cart_x = register_x + 100
    cart_y = register_y - cart_height + 40
    
    # Cart body
    draw.rounded_rectangle(
        [(cart_x, cart_y), (cart_x + cart_width, cart_y + cart_height)],
        radius=20,
        fill=light_teal
    )
    
    # Cart wheels
    wheel_radius = 15
    wheel_y = cart_y + cart_height - 10
    
    # Front wheel
    draw.ellipse(
        [(cart_x + 30 - wheel_radius, wheel_y - wheel_radius), 
         (cart_x + 30 + wheel_radius, wheel_y + wheel_radius)],
        fill=white
    )
    
    # Back wheel
    draw.ellipse(
        [(cart_x + cart_width - 30 - wheel_radius, wheel_y - wheel_radius), 
         (cart_x + cart_width - 30 + wheel_radius, wheel_y + wheel_radius)],
        fill=white
    )
    
    # Cart handle
    handle_height = 80
    handle_x_start = cart_x + cart_width - 30
    handle_y_start = cart_y + 20
    handle_x_end = handle_x_start + 40
    handle_y_end = handle_y_start - handle_height
    
    # Main handle bar
    draw.line(
        [(handle_x_start, handle_y_start), (handle_x_end, handle_y_end)],
        fill=white,
        width=15
    )
    
    # Handle grip
    draw.ellipse(
        [(handle_x_end - 15, handle_y_end - 15), 
         (handle_x_end + 15, handle_y_end + 15)],
        fill=white
    )
    
    # Draw receipt element (emerging from printer)
    receipt_width = 180
    receipt_height = 200
    receipt_x = register_x + register_width - 200
    receipt_y = register_y - receipt_height + 80
    
    # Receipt background with subtle texture
    draw.rounded_rectangle(
        [(receipt_x, receipt_y), (receipt_x + receipt_width, receipt_y + receipt_height)],
        radius=15,
        fill=white
    )
    
    # Receipt lines (representing printed content)
    receipt_line_y_start = receipt_y + 30
    receipt_line_spacing = 25
    receipt_line_width = receipt_width - 40
    receipt_line_x = receipt_x + 20
    
    for i in range(6):
        y_pos = receipt_line_y_start + i * receipt_line_spacing
        line_length = receipt_line_width if i < 5 else int(receipt_line_width * 0.7)
        line_color = deep_blue if i % 2 == 0 else teal_green
        
        draw.rounded_rectangle(
            [(receipt_line_x, y_pos), (receipt_line_x + line_length, y_pos + 10)],
            radius=5,
            fill=line_color
        )
    
    # Receipt perforation (dashed line)
    perforation_y = receipt_y + receipt_height - 40
    dash_length = 10
    gap_length = 10
    dash_x = receipt_x
    
    while dash_x < receipt_x + receipt_width:
        draw.rounded_rectangle(
            [(dash_x, perforation_y), (dash_x + dash_length, perforation_y + 3)],
            radius=2,
            fill=deep_blue
        )
        dash_x += dash_length + gap_length
    
    # Save as high-resolution PNG
    img.save('nexgen_pos_icon_1024.png', 'PNG')
    print("Generated nexgen_pos_icon_1024.png")
    
    # Create different sizes for various uses
    sizes = [512, 256, 128, 64, 32, 16]
    for s in sizes:
        img_resized = img.resize((s, s), Image.Resampling.LANCZOS)
        img_resized.save(f'nexgen_pos_icon_{s}.png', 'PNG')
        print(f"Generated nexgen_pos_icon_{s}.png")
    
    # Create ICO file with multiple resolutions
    img.save('nexgen_pos_icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Generated nexgen_pos_icon.ico")
    
    print("Modern POS icon generation complete!")

if __name__ == "__main__":
    create_modern_pos_icon()