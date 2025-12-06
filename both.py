import argparse
import cv2
import numpy as np
from ultralytics import YOLO
from moviepy.editor import VideoFileClip, ImageSequenceClip, AudioFileClip
import tempfile
import os
import time
import threading
import sounddevice as sd
import soundfile as sf

# ----------------------------------------------------------
# Arguments
# ----------------------------------------------------------
ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--source", default="0")
ap.add_argument("--resolution", default=None)
ap.add_argument("--record_audio", action="store_true")
args = ap.parse_args()

is_webcam = args.source.isdigit() or args.source == "0"

# ----------------------------------------------------------
# Load YOLO
# ----------------------------------------------------------
model = YOLO(args.model)

# ----------------------------------------------------------
# Open source
# ----------------------------------------------------------
cap = cv2.VideoCapture(int(args.source) if is_webcam else args.source)
ret, frame = cap.read()
if not ret:
    raise SystemExit("Cannot open source")

# ----------------------------------------------------------
# Resolution setup
# ----------------------------------------------------------
if args.resolution:
    w, h = map(int, args.resolution.split("x"))
else:
    h, w = frame.shape[:2]

cv2.namedWindow("YOLO")
cv2.resizeWindow("YOLO", w, h)

# ----------------------------------------------------------
# Temps
# ----------------------------------------------------------
temp_dir = tempfile.mkdtemp()
frame_files = []
timestamps = []

# ----------------------------------------------------------
# Webcam audio recording
# ----------------------------------------------------------
audio_path = os.path.join(temp_dir, "webcam_audio.wav")
audio_data = []

if is_webcam and args.record_audio:
    def audio_thread_fn(stop_evt, fs=44100):
        with sd.InputStream(samplerate=fs, channels=2,
            callback=lambda indata, frames, time_info, status: audio_data.append(indata.copy())):
            stop_evt.wait()
        if audio_data:
            sf.write(audio_path, np.concatenate(audio_data, axis=0), fs)

    stop_evt = threading.Event()
    audio_thread = threading.Thread(target=audio_thread_fn, args=(stop_evt,))
    audio_thread.start()

# ----------------------------------------------------------
# For video: load original clip (KEEP OPEN)
# ----------------------------------------------------------
if not is_webcam:
    original_clip = VideoFileClip(args.source)
    original_fps = original_clip.fps

# ----------------------------------------------------------
# Frame processing loop
# ----------------------------------------------------------
start_time = time.time()
frame_idx = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, verbose=False)
    im = results[0].plot()

    if (im.shape[1], im.shape[0]) != (w, h):
        im = cv2.resize(im, (w, h))

    path = os.path.join(temp_dir, f"{frame_idx:06d}.png")
    cv2.imwrite(path, im)
    frame_files.append(path)

    timestamps.append(time.time() - start_time)

    cv2.imshow("YOLO", im)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    frame_idx += 1

cap.release()
cv2.destroyAllWindows()

if is_webcam and args.record_audio:
    stop_evt.set()
    audio_thread.join()

# ----------------------------------------------------------
# Determine FPS
# ----------------------------------------------------------
if is_webcam:
    if len(timestamps) > 1:
        fps = 1 / np.mean(np.diff(timestamps))
    else:
        fps = 30
else:
    fps = original_fps

# ----------------------------------------------------------
# Build video ONLY from frames
# ----------------------------------------------------------
clip = ImageSequenceClip(frame_files, fps=fps)

# ----------------------------------------------------------
# Add audio (video mode uses source audio)
# ----------------------------------------------------------
if not is_webcam:
    if original_clip.audio:
        trimmed_audio = original_clip.audio.subclip(0, clip.duration)
        clip = clip.set_audio(trimmed_audio)

else:
    if args.record_audio and os.path.exists(audio_path):
        mic_audio = AudioFileClip(audio_path).subclip(0, clip.duration)
        clip = clip.set_audio(mic_audio)

# ----------------------------------------------------------
# Export final video
# ----------------------------------------------------------
clip.write_videofile("output.mp4", codec="libx264", audio_codec="aac")

# ----------------------------------------------------------
# Cleanup
# ----------------------------------------------------------
clip.close()
if not is_webcam:
    original_clip.close()

for f in frame_files:
    os.remove(f)

if os.path.exists(audio_path):
    os.remove(audio_path)

os.rmdir(temp_dir)

print("Saved: output.mp4")
