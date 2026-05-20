"""
Optional training scripts for the lightweight video and audio detectors.

These are NOT required to run the system (by default the server loads
pretrained detectors from the HuggingFace Hub), but they let you fine-tune
or retrain from scratch on your own datasets (FaceForensics++, DFDC,
Celeb-DF, ASVspoof, WaveFake, Fake-or-Real) — useful for the FYP report.

See train_video.py and train_audio.py for CLI usage.
"""
