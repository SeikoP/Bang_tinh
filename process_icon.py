#!/usr/bin/env python3
"""Process icon to add rounded corners for WMS application"""

from PIL import Image, ImageDraw
import os

def create_rounded_icon(input_path, output_path, radius=50):
    """
    Create a rounded rectangle icon from the original image.
    
    Args:
        input_path: Path to original icon
        output_path: Path to save processed icon
        radius: Radius of rounded corners in pixels
    """
    # Open original image
    img = Image.open(input_path).convert('RGBA')
    
    print(f"Original icon size: {img.size}, mode: {img.mode}")
    
    # Create a new image with transparent background
    output = Image.new('RGBA', img.size, (0, 0, 0, 0))
    
    # Create mask for rounded corners
    mask = Image.new('L', img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    
    # Draw a white rounded rectangle on the mask
    mask_draw.rounded_rectangle(
        [(0, 0), (img.size[0] - 1, img.size[1] - 1)],
        radius=radius,
        fill=255
    )
    
    # Apply mask to original image
    output.paste(img, (0, 0))
    output.putalpha(mask)
    
    # Save result
    output.save(output_path)
    print(f"✓ Rounded icon saved to {output_path}")
    print(f"  Icon size: {output.size}")

if __name__ == "__main__":
    icon_dir = os.path.join(os.path.dirname(__file__), 'assets')
    input_icon = os.path.join(icon_dir, 'icon.png')
    output_icon = os.path.join(icon_dir, 'icon.png')
    
    if os.path.exists(input_icon):
        # Create backup
        backup_path = os.path.join(icon_dir, 'icon_backup.png')
        if not os.path.exists(backup_path):
            Image.open(input_icon).save(backup_path)
            print(f"✓ Backup created at {backup_path}")
        
        # Process icon
        create_rounded_icon(input_icon, output_icon, radius=50)
        print("\n✓ Icon processing completed successfully!")
    else:
        print(f"Error: Icon not found at {input_icon}")
