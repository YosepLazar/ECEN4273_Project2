import argparse
import cv2
import numpy as np
from ultralytics import YOLO
from moviepy.editor import VideoFileClip
import tempfile
import os

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--resolution", default=None)
    args = ap.parse_args()

    model = YOLO(args.model)
    cap = cv2.VideoCapture(args.source)

    video_clip = VideoFileClip(args.source)
    fps = video_clip.fps  # use MoviePy FPS to match source
    frame_count = int(video_clip.reader.nframes)

    ret, frame = cap.read()
    if not ret:
        raise SystemExit("Source failure")

    if args.resolution:
        w, h = map(int, args.resolution.split("x"))
    else:
        h, w = frame.shape[:2]

    win_name = "YOLO"
    cv2.namedWindow(win_name)
    cv2.resizeWindow(win_name, w, h)

    temp_video_path = os.path.join(tempfile.gettempdir(), "output_with_audio.mp4")
    out = cv2.VideoWriter(temp_video_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame, verbose=False)
        im = results[0].plot()
        if (im.shape[1], im.shape[0]) != (w, h):
            im = cv2.resize(im, (w, h))
        cv2.imshow(win_name, im)
        out.write(im)
        frame_idx += 1
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    # trim audio to match processed video length
    duration = frame_idx / fps
    audio_clip = video_clip.audio.subclip(0, duration) if video_clip.audio else None
    processed_clip = VideoFileClip(temp_video_path)
    final_clip = processed_clip.set_audio(audio_clip)
    final_clip.write_videofile("output.mp4", codec="libx264", audio_codec="aac")

    os.remove(temp_video_path)
