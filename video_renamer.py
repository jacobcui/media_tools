"""Rename video files to YYYY-MM-DD_originalname.mp4 format based on creation date"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import ffmpeg
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer()
console = Console()

def is_already_dated(filename: str) -> bool:
    """Check if filename already starts with YYYY-MM-DD_"""
    return bool(Path(filename).stem[:10].replace('-', '').isdigit())

def get_video_creation_date(video_path: str) -> Optional[str]:
    """Get video creation date from metadata"""
    try:
        # Get video metadata using ffmpeg
        probe = ffmpeg.probe(video_path)

        # Try to get creation_time from metadata
        # Check multiple possible locations for the creation date
        creation_date = None

        # Check format tags
        if 'tags' in probe['format']:
            tags = probe['format']['tags']
            if 'creation_time' in tags:
                creation_date = tags['creation_time']

        # Check stream tags if not found in format tags
        if not creation_date:
            for stream in probe['streams']:
                if 'tags' in stream and 'creation_time' in stream['tags']:
                    creation_date = stream['tags']['creation_time']
                    break

        if creation_date:
            # Parse the date string (handles multiple formats)
            try:
                # Try ISO format (2023-12-31T12:34:56.000000Z)
                date_obj = datetime.strptime(creation_date.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                try:
                    # Try other common format (2023-12-31 12:34:56)
                    date_obj = datetime.strptime(creation_date.split('.')[0], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Fallback to file modification time if date parsing fails
                    date_obj = datetime.fromtimestamp(os.path.getmtime(video_path))

            return date_obj.strftime('%Y-%m-%d')

        # Fallback to file modification time if no creation date in metadata
        return datetime.fromtimestamp(os.path.getmtime(video_path)).strftime('%Y-%m-%d')

    except Exception as e:
        console.print(f"[yellow]Warning: Could not get creation date for {video_path}: {str(e)}[/yellow]")
        return None

def rename_videos(directory: str, recursive: bool = True):
    """Rename video files in the directory to YYYY-MM-DD_originalname.mp4 format"""

    # Get list of files to process
    files_to_process = []
    if recursive:
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith('.mp4'):
                    files_to_process.append((root, filename))
    else:
        for filename in os.listdir(directory):
            if filename.lower().endswith('.mp4'):
                files_to_process.append((directory, filename))

    if not files_to_process:
        console.print("[yellow]No MP4 files found in the specified directory[/yellow]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Processing videos...", total=len(files_to_process))

        for root, filename in files_to_process:
            progress.update(task, description=f"Processing {filename}")

            # Skip if already in correct format
            if is_already_dated(filename):
                console.print(f"[blue]Skipping {filename} - already in correct format[/blue]")
                progress.advance(task)
                continue

            file_path = os.path.join(root, filename)
            creation_date = get_video_creation_date(file_path)

            if creation_date:
                # Create new filename
                name = Path(filename).stem
                new_filename = f"{creation_date}_{name}.mp4"
                new_file_path = os.path.join(root, new_filename)

                # Rename file
                try:
                    os.rename(file_path, new_file_path)
                    console.print(f"[green]Renamed: {filename} -> {new_filename}[/green]")
                except Exception as e:
                    console.print(f"[red]Error renaming {filename}: {str(e)}[/red]")

            progress.advance(task)

@app.command()
def rename(
    directory: str = typer.Option(..., "--dir", help="Directory containing MP4 files to rename"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", help="Process subdirectories recursively"),
):
    """Rename MP4 files to YYYY-MM-DD_originalname.mp4 format based on creation date"""

    # Validate directory
    if not os.path.isdir(directory):
        console.print(f"[red]Error: Directory '{directory}' does not exist[/red]")
        raise typer.Exit(1)

    # Process videos
    with console.status("[bold green]Processing videos..."):
        rename_videos(directory, recursive)

if __name__ == "__main__":
    app()
