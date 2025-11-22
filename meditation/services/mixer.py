import logging
from pydub import AudioSegment
from pathlib import Path
from django.conf import settings

def mix_background(voice_path: str, bg_name: str, session_num: int) -> str:
    """
    Mixes a voice track with a background track if bg_name is provided.
    Saves the final file as session{num}.mp3 in media/audio/.
    If no background is selected, simply copies the voice track as session{num}.mp3.
    """
    # Load voice audio
    voice = AudioSegment.from_file(voice_path).apply_gain(+3)
    logging.info("Voice track length: %.2f sec", len(voice) / 1000.0)
    
    if bg_name:  # background selected
        bg_path = Path(settings.MEDIA_ROOT) / "backgrounds" / f"{bg_name}.mp3"
        if not bg_path.exists():
            raise FileNotFoundError(f"Background file not found: {bg_path.resolve()}")

        logging.info(f"Mixing voice: {voice_path} with background: {bg_path}")

        background = AudioSegment.from_file(bg_path).apply_gain(-10)

        # Loop background to match voice duration
        if len(background) < len(voice):
            loops = (len(voice) // len(background)) + 1
            background *= loops

        mixed = background[:len(voice)].overlay(voice)


        # Trim background and overlay voice
        mixed = background[:len(voice)].overlay(voice)
    else:  # no background selected
        logging.info(f"No background selected. Using raw voice: {voice_path}")
        mixed = voice

    # Save final audio in media/audio/
    output_dir = Path(settings.MEDIA_ROOT) / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)

    final_path = output_dir / f"session{session_num}.mp3"
    mixed.export(str(final_path), format="mp3", bitrate="192k")

    logging.info(f"Final audio saved to: {final_path}")
    return str(final_path)
