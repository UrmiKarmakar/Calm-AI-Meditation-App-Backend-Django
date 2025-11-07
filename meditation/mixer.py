import logging
from pydub import AudioSegment
from pathlib import Path

def mix_background(voice_path: str, bg_name: str) -> str:
    # Convert voice path to Path object
    voice_path = Path(voice_path)

    # Resolve background path
    project_root = voice_path.parents[2]  # CalmAI/
    bg_path = project_root / "static" / "backgrounds" / f"{bg_name}.mp3"

    if not bg_path.exists():
        raise FileNotFoundError(f"Background file not found: {bg_path.resolve()}")

    logging.info(f"Mixing voice: {voice_path} with background: {bg_path}")

    # Load and adjust volumes
    voice = AudioSegment.from_file(voice_path).apply_gain(+3)
    background = AudioSegment.from_file(bg_path).apply_gain(-10)

    # Loop background to match voice duration
    if len(background) < len(voice):
        loops = (len(voice) // len(background)) + 1
        background *= loops

    # Trim and overlay
    mixed = background[:len(voice)].overlay(voice)

    # Save final mixed audio in meditation/output/
    output_dir = project_root / "meditation" / "output"
    output_dir.mkdir(exist_ok=True)

    final_path = output_dir / f"{voice_path.stem}_final.mp3"
    mixed.export(str(final_path), format="mp3", bitrate="192k")

    logging.info(f"Final mixed audio saved to: {final_path}")
    return str(final_path)
