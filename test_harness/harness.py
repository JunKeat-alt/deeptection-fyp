import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

sys.path.insert(0, str(BACKEND))

# ---------------- Backend imports ----------------
from inference.fusion import fuse_and_decide
from routes.analyze import _process_video_with_audio, _process_audio_only

# ---------------- Paths ----------------
MANIFEST_PATH = ROOT / "test_harness" / "manifest.json"

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    cases = json.load(f)

print(f"\nLoaded {len(cases)} test case(s)\n")

# ---------------- Metrics ----------------
total_cases = 0
passed_cases = 0
failed_cases = []
fusion_counter = Counter()

# ---------------- Run all cases ----------------
for case in cases:
    print("==================================================")
    print(f"Case ID: {case['id']}")
    print(f"Category: {case['category']}")
    print(f"Mode: {case.get('mode')}")
    print(f"Expected Verdict: {case['expected_verdict']}")
    print(f"Modality: {case.get('modality')}")
    print(f"Video Source: {case.get('video_source')}")
    print(f"Audio Source: {case.get('audio_source')}")

    file_path = ROOT / "test_harness" / case["file"]

    if not file_path.exists():
        print("[ERROR] File missing")
        failed_cases.append({
            "id": case["id"],
            "category": case["category"],
            "reason": "file_missing"
        })
        continue

    print("[OK] File found")

    total_cases += 1
    start = time.time()

    # ---------------- Run inference ----------------
    tmp_audio_path = ROOT / "test_harness" / "tmp_audio.wav"

    video_source = case.get("video_source")
    audio_source = case.get("audio_source")
    modality = case.get("modality")

    try:
        if modality == "audio":
            video_result, audio_result, elapsed_ms = _process_audio_only(
                file_path,
                audio_source=audio_source
            )
        else:
            video_result, audio_result, elapsed_ms = _process_video_with_audio(
                file_path,
                tmp_audio_path,
                video_source=video_source,
                audio_source=audio_source
            )

        fusion_result = fuse_and_decide(video_result, audio_result)

    except Exception as exc:
        print(f"[ERROR] Case failed during processing: {exc}")
        failed_cases.append({
            "id": case["id"],
            "category": case["category"],
            "reason": str(exc)
        })
        continue

    elapsed = round(time.time() - start, 2)

    predicted = fusion_result.get("verdict")
    expected = case["expected_verdict"]
    passed = predicted == expected

    if passed:
        passed_cases += 1
    else:
        failed_cases.append({
            "id": case["id"],
            "category": case["category"],
            "expected": expected,
            "predicted": predicted,
            "fusion_mode": fusion_result.get("fusion_mode"),
            "video_score": fusion_result.get("video_score"),
            "audio_score": fusion_result.get("audio_score")
        })

    fusion_mode = fusion_result.get("fusion_mode")
    if fusion_mode:
        fusion_counter[fusion_mode] += 1

    # ---------------- Print result ----------------
    print(f"\nPredicted: {predicted}")
    print(f"Expected : {expected}")

    print(f"\nFinal Score : {fusion_result.get('final_score')}")
    print(f"Confidence : {fusion_result.get('confidence')}")

    print(f"\nVideo Score : {fusion_result.get('video_score')}")
    print(f"Audio Score : {fusion_result.get('audio_score')}")

    print(f"\nVideo Raw Result: {video_result}")
    print(f"Audio Raw Result: {audio_result}")

    print(f"\nFusion Mode : {fusion_mode}")
    print(f"\nPASS: {passed}")
    print(f"\nProcessing Time: {elapsed}s")

# ---------------- Final summary ----------------
print("\n==================================================")
print("FINAL SUMMARY")
print("==================================================")

print(f"Total Cases : {total_cases}")
print(f"Passed      : {passed_cases}")

if total_cases > 0:
    accuracy = round((passed_cases / total_cases) * 100, 2)
    print(f"Accuracy    : {accuracy}%")

print("\n==================================================")
print("FAILED CASES")
print("==================================================")

if failed_cases:
    for item in failed_cases:
        print(item)
else:
    print("No failed cases.")

print("\n==================================================")
print("FUSION MODE DISTRIBUTION")
print("==================================================")

if fusion_counter:
    for mode, count in fusion_counter.items():
        print(f"{mode}: {count}")
else:
    print("No fusion modes recorded.")