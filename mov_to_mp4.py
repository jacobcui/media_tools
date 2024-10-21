"""Convert MOV files to MP4 and rename them with the creation date as YYYYMMDD"""

import argparse
import os
from datetime import datetime
from pathlib import Path

import ffmpeg
from tqdm import tqdm


def convert_file(input_path: str, output_path: str):
    """Convert a single MOV file to MP4 and rename it with the creation date as YYYYMMDD"""

    try:
        # Convert .mov to .mp4 using ffmpeg
        probe = ffmpeg.probe(input_path)
        duration = float(probe["streams"][0]["duration"])

        # Run the ffmpeg command
        process = (
            ffmpeg.input(input_path)
            .output(output_path, vcodec="libx264", acodec="aac", crf=18, preset="slow")
            .global_args("-progress", "pipe:1")
            .overwrite_output()
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )

        # Initialize the progress bar
        pbar = tqdm(total=100, position=1, bar_format="{l_bar}{bar}", ncols=50)

        while True:
            line = process.stdout.readline().decode("utf-8")
            if not line:
                break

            # Update the progress bar
            parts = line.split("=")
            # Check if the line contains the progress information
            if len(parts) == 2 and parts[0] == "out_time_ms":
                time = float(parts[1]) / 1000000
                # Calculate the progress percentage
                progress = min(int(time / duration * 100), 100)
                pbar.n = progress
                pbar.refresh()

        pbar.close()
        process.wait()
        return output_path
    except ffmpeg.Error as e:
        print(f"Error converting {input_path}: {e.stderr.decode()}")
        return None


def get_file_creation_date(input_path: str):
    """Get the creation date of a file as YYYYMMDD"""

    return datetime.fromtimestamp(os.path.getmtime(input_path)).strftime("%Y%m%d")


def get_output_filepath(input_path: str):
    """Get the output filepath for a file"""

    file_dir = Path(input_path).parent
    file_name = Path(input_path).stem
    yyyymmdd = get_file_creation_date(input_path=input_path)

    return str(file_dir / f"{yyyymmdd}_{Path(file_name).with_suffix('.mp4')}")


def convert_and_rename_mov_files(input_directory):
    """Convert all .mov files in the input directory to .mp4 and rename them with the creation date as YYYYMMDD"""

    if not os.path.exists(input_directory):
        print(f"Error: Directory '{input_directory}' does not exist.")
        return

    # Iterate through all files in the input directory
    for filename in os.listdir(input_directory):
        if filename.lower().endswith(".mov"):
            input_path = os.path.join(input_directory, filename)
            output_path = get_output_filepath(input_path=input_path)
            converted_file = convert_file(
                input_path=input_path, output_path=output_path
            )
            if converted_file:
                print(
                    f"Successfully converted and renamed: {filename} -> {converted_file}"
                )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Convert MOV files to MP4.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dir", help="Directory containing MOV files to convert")
    group.add_argument("--file", help="Single MOV file to convert")
    args = parser.parse_args()

    if args.dir:
        convert_and_rename_mov_files(args.dir)
    elif args.file:
        if args.file.lower().endswith(".mov"):

            output_path = get_output_filepath(input_path=args.file)
            converted_file = convert_file(input_path=args.file, output_path=output_path)
            if converted_file:
                print(
                    f"Successfully converted and renamed: {args.file} -> {converted_file}"
                )

        else:
            print(f"Error: {args.file} is not a MOV file.")
