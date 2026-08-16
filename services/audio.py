import asyncio
import os
import math
import wave
import struct
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

# Pre-defined neural voice options
VOICE_OPTIONS = {
    "male_deep": "en-US-ChristopherNeural",
    "female_clear": "en-US-JennyNeural",
    "male_energetic": "en-US-GuyNeural",
    "female_expressive": "en-US-AriaNeural"
}

def generate_ambient_synth_music(output_path: Path, duration_seconds: int = 30, bpm: int = 90):
    """
    Procedurally generate a smooth, royalty-free ambient electronic chord progression.
    Works 100% offline with zero external audio assets required.
    """
    sample_rate = 44100
    total_samples = int(sample_rate * duration_seconds)
    
    # Chord frequencies (e.g. D minor -> Bb maj -> F maj -> C maj progression)
    chords = [
        [146.83, 220.00, 261.63, 349.23], # Dm7
        [116.54, 174.61, 233.08, 293.66], # Bbmaj7
        [174.61, 220.00, 261.63, 349.23], # Fmaj7
        [130.81, 196.00, 246.94, 293.66]  # C7
    ]
    chord_duration = 3.5 # seconds per chord
    
    with wave.open(str(output_path), 'w') as wav_file:
        wav_file.setnchannels(2) # Stereo
        wav_file.setsampwidth(2) # 16-bit
        wav_file.setframerate(sample_rate)
        
        frames = []
        for i in range(total_samples):
            t = i / sample_rate
            chord_idx = int((t / chord_duration) % len(chords))
            chord = chords[chord_idx]
            
            # Subtle low frequency pulse
            pulse = 0.5 + 0.5 * math.sin(2 * math.pi * (bpm / 60) * t)
            
            sample_val = 0.0
            for note_freq in chord:
                # Sine wave with gentle warm harmonics
                note_wave = math.sin(2 * math.pi * note_freq * t) + 0.3 * math.sin(4 * math.pi * note_freq * t)
                sample_val += note_wave * 0.18
                
            # LFO filter sweep effect
            lfo = 0.7 + 0.3 * math.sin(2 * math.pi * 0.25 * t)
            sample_val *= lfo * pulse * 0.4
            
            # Smooth fade in and fade out
            if t < 1.0:
                sample_val *= t
            elif t > duration_seconds - 1.0:
                sample_val *= (duration_seconds - t)
                
            int_sample = int(max(-32767, min(32767, sample_val * 32767)))
            frames.append(struct.pack('<hh', int_sample, int_sample))
            
        wav_file.writeframes(b''.join(frames))

async def _synthesize_edge_tts(text: str, voice: str, output_path: Path):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))

def generate_voiceover(
    text: str,
    output_path: Path,
    voice_key: str = "male_deep",
    api_key: Optional[str] = None
) -> bool:
    """
    Generate speech audio for given text.
    Tries edge-tts (neural voice) or OpenAI TTS if key is present.
    Returns True if audio was generated, False on graceful failure.
    """
    if not text or not text.strip():
        return False

    output_path.parent.mkdir(exist_ok=True)
    clean_text = text.strip()

    # 1. Try Edge-TTS (Free, high-quality neural voices)
    try:
        voice = VOICE_OPTIONS.get(voice_key, "en-US-ChristopherNeural")
        asyncio.run(_synthesize_edge_tts(clean_text, voice, output_path))
        if output_path.exists() and output_path.stat().st_size > 500:
            return True
    except Exception:
        pass

    # 2. Try OpenAI TTS if API key is configured
    openai_key = api_key or os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            oai_voice = "alloy" if "female" in voice_key else "echo"
            response = client.audio.speech.create(
                model="tts-1",
                voice=oai_voice,
                input=clean_text
            )
            response.stream_to_file(str(output_path))
            if output_path.exists() and output_path.stat().st_size > 500:
                return True
        except Exception:
            pass

    return False

def mix_audio_and_video(
    video_path: Path,
    voice_path: Optional[Path],
    music_path: Optional[Path],
    output_path: Path,
    ffmpeg_bin: str,
    music_volume: float = 0.12
):
    """
    Mixes voiceover narration and background music track into final MP4 video using FFmpeg.
    """
    has_voice = voice_path is not None and voice_path.exists() and voice_path.stat().st_size > 500
    has_music = music_path is not None and music_path.exists() and music_path.stat().st_size > 500

    if not has_voice and not has_music:
        # Just copy input video if no audio
        shutil.copy(video_path, output_path)
        return

    cmd = [ffmpeg_bin, "-y", "-i", str(video_path)]

    if has_voice and has_music:
        cmd.extend(["-i", str(voice_path), "-i", str(music_path)])
        filter_complex = (
            f"[2:a]volume={music_volume}[bg];"
            f"[1:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path)
        ])
    elif has_voice:
        cmd.extend([
            "-i", str(voice_path),
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path)
        ])
    elif has_music:
        cmd.extend([
            "-i", str(music_path),
            "-filter_complex", f"[1:a]volume={music_volume}[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path)
        ])

    subprocess.run(cmd, check=True, capture_output=True, text=True)
