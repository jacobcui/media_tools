"""Extract subtitles from MP4/MP3 files with support for Mandarin and other languages"""

import os
from pathlib import Path
from typing import Optional

import typer
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip
from rich.console import Console
from tqdm import tqdm

app = typer.Typer()
console = Console()

def extract_audio(file_path: str, output_path: str):
    """Extract audio from video file to WAV format"""
    try:
        # For MP4, extract audio from video
        video = VideoFileClip(file_path)
        audio = video.audio

        # Use tqdm to show progress during audio extraction
        with tqdm(total=100, desc="Extracting audio", unit="%") as pbar:
            def progress_callback(t):
                pbar.n = int(t * 100)
                pbar.refresh()

            audio.write_audiofile(output_path, verbose=False, logger=None, progress_callback=progress_callback)

        audio.close()
        video.close()
        return True
    except Exception as e:
        console.print(f"[red]Error extracting audio: {str(e)}[/red]")
        return False

def generate_subtitles(audio_path: str, output_path: str, model_name: str = "medium"):
    """Generate subtitles using Whisper"""
    try:
        # Show progress for model loading
        with tqdm(total=1, desc="Loading Whisper model") as pbar:
            model = whisper.load_model(model_name)
            pbar.update(1)

        # Show indeterminate progress bar for transcription
        with tqdm(desc="Transcribing audio", bar_format='{desc}: |{bar}| {elapsed} elapsed') as pbar:
            result = model.transcribe(audio_path)
            pbar.update(1)  # Complete the progress bar when done

        # Show progress for writing subtitles
        total_segments = len(result["segments"])
        with tqdm(total=total_segments, desc="Writing subtitles") as pbar:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(result["segments"], start=1):
                    # Convert time to SRT format
                    start = format_timestamp(segment["start"])
                    end = format_timestamp(segment["end"])
                    text = segment["text"].strip()

                    f.write(f"{i}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")

                    pbar.update(1)

        return True
    except Exception as e:
        console.print(f"[red]Error generating subtitles: {str(e)}[/red]")
        return False

def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def convert_srt_to_text(srt_path: str, output_path: str) -> bool:
    """Convert SRT file to plain text, extracting only the subtitle content"""
    try:
        with open(srt_path, 'r', encoding='utf-8') as srt_file:
            lines = srt_file.readlines()

        text_lines = []
        # Show progress for processing lines
        with tqdm(total=len(lines), desc="Converting SRT to text") as pbar:
            for line in lines:
                # Skip empty lines, timestamp lines (contains '-->'), and numeric lines
                line = line.strip()
                if (line and
                    '-->' not in line and
                    not line.isdigit()):
                    text_lines.append(line)
                pbar.update(1)

        # Write to output file
        with open(output_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write('\n'.join(text_lines))

        return True
    except Exception as e:
        console.print(f"[red]Error converting SRT to text: {str(e)}[/red]")
        return False

@app.command()
def extract(
    file_path: str = typer.Argument(..., help="Path to the MP4/MP3 file"),
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", "-o", help="Output directory for subtitles"
    ),
    model: str = typer.Option(
        "medium", "--model", "-m",
        help="Whisper model size (tiny, base, small, medium, large)"
    ),
):
    """Extract subtitles from an MP4/MP3 file with support for multiple languages including Mandarin"""

    # Validate file path and type
    if not os.path.exists(file_path):
        console.print(f"[red]Error: File '{file_path}' not found[/red]")
        raise typer.Exit(1)

    # Check if file is MP4 or MP3
    if not file_path.lower().endswith(('.mp4', '.mp3')):
        console.print(f"[red]Error: File must be an MP4 or MP3 file. Got: {file_path}[/red]")
        raise typer.Exit(1)

    # Set up output directory
    if output_dir is None:
        output_dir = os.path.dirname(file_path)
    os.makedirs(output_dir, exist_ok=True)

    file_path = Path(file_path)
    base_name = file_path.stem
    srt_path = os.path.join(output_dir, f"{base_name}.srt")

    # Process the file
    if file_path.suffix.lower() == '.mp4':
        # For MP4, we need to extract audio first
        audio_path = os.path.join(output_dir, f"{base_name}_temp.wav")
        if not extract_audio(str(file_path), audio_path):
            console.print("[red]Failed to extract audio[/red]")
            raise typer.Exit(1)
    else:
        # For MP3, use it directly
        audio_path = str(file_path)

    # Generate subtitles
    if not generate_subtitles(audio_path, srt_path, model):
        console.print("[red]Failed to generate subtitles[/red]")
        raise typer.Exit(1)

    # Clean up temporary audio file if it was created
    if file_path.suffix.lower() == '.mp4':
        try:
            os.remove(audio_path)
        except:
            pass

    console.print(f"[green]Successfully generated subtitles: {srt_path}[/green]")

@app.command()
def srt_to_text(
    srt_path: str = typer.Option(..., "--from-srt", help="Input SRT file path"),
    output_path: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output text file path (default: same name as SRT with .txt extension)"
    ),
):
    """Convert SRT subtitle file to plain text, extracting only the subtitle content"""

    # Validate SRT path
    if not os.path.exists(srt_path):
        console.print(f"[red]Error: SRT file '{srt_path}' not found[/red]")
        raise typer.Exit(1)

    # Set up output path if not provided
    if output_path is None:
        output_path = str(Path(srt_path).with_suffix('.txt'))

    if convert_srt_to_text(srt_path, output_path):
        console.print(f"[green]Successfully converted to text: {output_path}[/green]")
    else:
        console.print("[red]Failed to convert SRT to text[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
