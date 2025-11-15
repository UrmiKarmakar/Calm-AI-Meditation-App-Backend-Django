import logging
from pydub import AudioSegment
from pathlib import Path
from django.conf import settings

def mix_background(voice_path: str, bg_name: str, session_num: int) -> str:
    """
    Mixes a voice track with a background track.
    Saves the final file as session{num}_final.mp3 in media/audio/.
    """
    bg_path = Path(settings.BASE_DIR) / "static" / "backgrounds" / f"{bg_name}.mp3"
    if not bg_path.exists():
        raise FileNotFoundError(f"Background file not found: {bg_path.resolve()}")

    logging.info(f"Mixing voice: {voice_path} with background: {bg_path}")

    # Load audio and adjust volumes
    voice = AudioSegment.from_file(voice_path).apply_gain(+3)
    background = AudioSegment.from_file(bg_path).apply_gain(-10)

    # Loop background to match voice duration
    if len(background) < len(voice):
        loops = (len(voice) // len(background)) + 1
        background *= loops

    # Trim background and overlay voice
    mixed = background[:len(voice)].overlay(voice)

    # Save final mixed audio in media/audio/
    output_dir = Path(settings.MEDIA_ROOT) / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)

    final_path = output_dir / f"session{session_num}_final.mp3"
    mixed.export(str(final_path), format="mp3", bitrate="192k")

    logging.info(f"Final mixed audio saved to: {final_path}")
    return str(final_path)
