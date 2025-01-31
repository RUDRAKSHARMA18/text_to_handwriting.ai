"""
FULL CODE FOR HANDWRITING FONT WITH 5 VARIATIONS PER CHARACTER
Three steps: Create templates -> Process images -> Build font
"""

# -------------------------
# STEP 1: Template Creation
# -------------------------
from PIL import Image, ImageDraw, ImageFont
import os

def create_templates():
    os.makedirs('templates', exist_ok=True)
    
    characters = {
        'uppercase': "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        'lowercase': "abcdefghijklmnopqrstuvwxyz",
        'numbers': "0123456789",
        'symbols': "!@#$%^&*()+-=[]{};:'\",./<>?\\"
    }

    # Grid settings for 5 variations
    VARIANTS = 5
    COLS = 5  # 5 variants per character
    ROWS_PER_PAGE = 8
    BOX_SIZE = 150
    PADDING = 20
    
    for category, chars in characters.items():
        total_chars = len(chars)
        pages_needed = (total_chars * ROWS_PER_PAGE + (ROWS_PER_PAGE - 1)) // ROWS_PER_PAGE
        
        for page in range(pages_needed):
            img_width = COLS * (BOX_SIZE + PADDING) + PADDING
            img_height = ROWS_PER_PAGE * (BOX_SIZE + PADDING) + PADDING + 50  # +50 for labels
            
            img = Image.new('RGB', (img_width, img_height), 'white')
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("arial.ttf", 20)

            # Draw grid
            for col in range(COLS + 1):
                x = col * (BOX_SIZE + PADDING) + PADDING
                draw.line([(x, 50), (x, img_height - PADDING)], fill='black', width=2)
                
            for row in range(ROWS_PER_PAGE + 1):
                y = row * (BOX_SIZE + PADDING) + 50 + PADDING
                draw.line([(PADDING, y), (img_width - PADDING, y)], fill='black', width=2)

            # Add page labels
            draw.text((20, 20), f"{category} - Page {page+1}", fill='blue', font=font)

            # Add characters and variant labels
            start_idx = page * ROWS_PER_PAGE
            end_idx = min(start_idx + ROWS_PER_PAGE, total_chars)
            
            for idx in range(start_idx, end_idx):
                char = chars[idx]
                row = idx - start_idx
                
                for variant in range(VARIANTS):
                    col = variant
                    x = col * (BOX_SIZE + PADDING) + PADDING + 10
                    y = row * (BOX_SIZE + PADDING) + 50 + PADDING + 10
                    
                    # Character label
                    draw.text((x, y), char, fill='red', font=font)
                    # Variant label
                    draw.text((x + BOX_SIZE - 30, y), str(variant+1), fill='blue', font=font)

            img.save(f'templates/{category}_page{page+1}.png')

# -------------------------
# STEP 2: Image Processing
# -------------------------
import cv2
import numpy as np
import os

def process_variants():
    os.makedirs('processed_chars', exist_ok=True)
    categories = ['uppercase', 'lowercase', 'numbers', 'symbols']
    char_map = {
        'uppercase': "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        'lowercase': "abcdefghijklmnopqrstuvwxyz",
        'numbers': "0123456789",
        'symbols': "!@#$%^&*()+-=[]{};:'\",./<>?\\"
    }

    for category in categories:
        page = 1
        while True:
            img_path = f'templates/{category}_page{page}.png'
            if not os.path.exists(img_path):
                break
                
            img = cv2.imread(img_path)
            if img is None:
                break

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
            
            # Find contours (sorted top-to-bottom, left-to-right)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=lambda c: (cv2.boundingRect(c)[1], cv2.boundingRect(c)[0]))

            # Process each character variant
            chars = char_map[category]
            variants_per_char = 5
            chars_per_page = len(contours) // variants_per_char
            
            for char_idx in range(chars_per_page):
                if (page-1)*chars_per_page + char_idx >= len(chars):
                    break
                    
                char = chars[(page-1)*chars_per_page + char_idx]
                
                for variant in range(variants_per_char):
                    cnt_idx = char_idx * variants_per_char + variant
                    if cnt_idx >= len(contours):
                        break
                        
                    x, y, w, h = cv2.boundingRect(contours[cnt_idx])
                    roi = gray[y:y+h, x:x+w]
                    
                    # Center and resize
                    size = 200
                    result = np.zeros((size, size), np.uint8) + 255
                    start_x = (size - w) // 2
                    start_y = (size - h) // 2
                    result[start_y:start_y+h, start_x:start_x+w] = roi
                    
                    # Save with variant number
                    cv2.imwrite(f'processed_chars/{ord(char):04x}-{variant}.png', result)
            
            page += 1

# -------------------------
# STEP 3: Font Generation
# -------------------------
import fontforge
import os
import random

def create_font_with_variants():
    font = fontforge.font()
    font.fontname = "MyHandwritingVar"
    font.familyname = "My Handwriting Var"
    font.fullname = "My Handwriting Variable"
    font.version = "2.0"
    font.copyright = ""

    # Create feature for random substitution
    font.addLookup('random', 'gsub_random', None, [('rand', [('latn', ('dflt'))])])
    font.addLookupSubtable('random', 'random_subtable')

    processed_files = os.listdir('processed_chars')
    char_variants = {}

    # Group variants by character
    for filename in processed_files:
        if not filename.endswith('.png'):
            continue
            
        parts = filename.split('-')
        char_code = int(parts[0], 16)
        variant = int(parts[1].split('.')[0])
        
        if char_code not in char_variants:
            char_variants[char_code] = []
        char_variants[char_code].append(filename)

    # Create glyphs and features
    for char_code, variants in char_variants.items():
        # Create base glyph
        base_glyph = font.createChar(char_code)
        base_glyph.importOutlines(f'processed_chars/{variants[0]}')
        
        # Create alternate glyphs
        for i, variant in enumerate(variants[1:]):
            alt_name = f"uni{char_code:04x}.alt{i+1}"
            alt_glyph = font.createChar(-1, alt_name)
            alt_glyph.importOutlines(f'processed_chars/{variant}')
            
            # Add substitution
            base_glyph.addPosSub('random_subtable', alt_name)

        # Set glyph metrics
        base_glyph.left_side_bearing = 20
        base_glyph.right_side_bearing = 20
        base_glyph.width = 256

    # Enable OpenType random feature
    font.features = """\
feature rand {
    lookup random;
} rand;"""

    font.generate('my_handwriting_variable.ttf')

# -------------------------
# MAIN EXECUTION
# -------------------------
if __name__ == '__main__':
    # Step 1: Create templates
    create_templates()
    
    # Step 2: Process after scanning
    # (Manual step: Print, write, scan images to templates/ folder)
    # Then uncomment:
    # process_variants()
    
    # Step 3: Generate font
    # (Requires FontForge installed)
    # create_font_with_variants()