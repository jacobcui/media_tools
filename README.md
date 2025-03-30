# Media Tools

This project contains various tools for media file manipulation and management.

## Scripts

### mov_to_mp4.py

This script converts .mov files to .mp4 format using ffmpeg.

### image_renamer.py

This script renames image files based on the EXIF creation date.

## Setup

1. Ensure you have Python 3.x installed.
2. Ensure you have ffmpeg installed.
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To use the mov_to_mp4 converter:

```
python mov_to_mp4.py --dir <input_directory>
python mov_to_mp4.py --file <input_file>
```

Replace `<input_directory>` with the path to the directory containing your .mov files.

Replace `<input_file>` with the path to the .mov file you want to convert.


To use the image_renamer:

```
python image_renamer.py --dir <input_directory>
```



## Testing

Tests are written using pytest. To run the tests:

```
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
