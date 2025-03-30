import os
import argparse
import re
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

def is_already_dated(filename):
    # Check if filename matches the pattern YYYY-MM-DD_*.*
    pattern = r'^\d{4}-\d{2}-\d{2}_.*'
    return bool(re.match(pattern, filename))

def get_creation_date(image_path):
    try:
        # Open the image
        image = Image.open(image_path)

        # Get EXIF data
        exif = image._getexif()
        if not exif:
            return None

        # Look for DateTimeOriginal or DateTime tag
        for tag_id in exif:
            tag = TAGS.get(tag_id, tag_id)
            if tag in ['DateTimeOriginal', 'DateTime']:
                date_str = exif[tag_id]
                # Convert EXIF date format (YYYY:MM:DD HH:MM:SS) to datetime
                date_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                return date_obj.strftime('%Y-%m-%d')

        return None
    except Exception as e:
        print(f"Error reading EXIF data for {image_path}: {str(e)}")
        return None

def rename_images(directory):
    # Walk through directory and subdirectories
    for root, dirs, files in os.walk(directory):
        for filename in files:
            # Skip if file already follows the date pattern
            if is_already_dated(filename):
                print(f"Skipping {filename} - already in correct format")
                continue

            # Check if file is an image (basic check for common extensions)
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                file_path = os.path.join(root, filename)

                # Get creation date from EXIF
                creation_date = get_creation_date(file_path)

                if creation_date:
                    # Split filename and extension
                    name, ext = os.path.splitext(filename)

                    # Create new filename
                    new_filename = f"{creation_date}_{name}{ext}"
                    new_file_path = os.path.join(root, new_filename)

                    # Rename file
                    try:
                        os.rename(file_path, new_file_path)
                        print(f"Renamed: {filename} -> {new_filename}")
                    except Exception as e:
                        print(f"Error renaming {filename}: {str(e)}")
                else:
                    print(f"Skipping {filename} - no creation date found")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Rename image files based on EXIF creation date')
    parser.add_argument('--dir', required=True, help='Directory containing images to rename')

    # Parse arguments
    args = parser.parse_args()

    # Check if directory exists
    if not os.path.isdir(args.dir):
        print(f"Error: Directory '{args.dir}' does not exist")
        return

    # Process images
    rename_images(args.dir)

if __name__ == "__main__":
    main()
