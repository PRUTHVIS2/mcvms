# 05 Identity (Multi-Target Multi-Camera tracking)

Terminology for the report: person re-identification (Re-ID) + MTMC tracking. Detector classes are fixed; identities are an **embedding gallery**, not new YOLO classes.

## Pipeline
```
per camera: YOLO -> ByteTrack (local id e.g. cam2-T41)
   every 1-2 s per track: crop -> quality filter -> OSNet embedding (512-d, L2-normalised)
   track-level fingerprint = mean of embeddings of accepted crops
Identity Manager (central): compare to gallery -> match% / tentative / new
```

## Quality filter (skip a crop if any is true)
box height < 96 px or width < 32 px; Laplacian variance < threshold (blur); partially occluded (IoU with another track box > 0.3); touching frame border (>=2 px cut-off); detector conf < 0.6. Thresholds in `config/app.yaml`, tuned on own footage.

## Diversity rule ("what counts as 20 good frames")
Accepted crops must be spread out: at least 0.5 s apart AND cosine similarity to the previous accepted crop < 0.97 (skip near-duplicates). A track becomes eligible for identity confirmation after **>= 20 accepted diverse crops** (config `min_crops_confirm`).

## Matching rules
1. Match tracks, not single frames (need >= 5 accepted crops before showing any match; show "collecting evidence...").
2. Score = cosine similarity of track fingerprint vs each identity's stored embeddings (max of mean-of-top-3). Keep last 10-20 diverse embeddings per identity (cap, oldest-lowest-quality evicted).
3. **Same-camera conflict**: two simultaneous tracks in one camera can never be the same identity.
4. **Ambiguity margin**: if best - second_best < margin (default 0.05), do not assign; keep the track tentative.
5. **Travel-time table** (`config/travel_times.yaml`, min seconds between camera pairs): reject a match that would need impossible travel. Demo default: all pairs 0 (disabled) since demo cameras are simulated.
6. **Hungarian assignment** when several tracks/identities resolve at once (scipy `linear_sum_assignment`).
7. Threshold: `match_threshold` tuned on own footage; do NOT copy a paper's number.
8. New unmatched track -> create **tentative** identity. Tentative identities that never reach confirmation expire after 24 h. Confirmed after min_crops_confirm diverse crops.
9. Gallery reset policy: config `gallery_policy: persistent | daily` (default persistent for demo; report the limit that body Re-ID is reliable for hours to about a day).

## Match percentage
Cosine similarity is not a probability. Implement `Calibrator` interface:
- Default until data exists: tiers High (>= t_high) / Medium / Low, labelled "match score".
- After collecting labelled same/different pairs from own test footage (`scripts/calibrate_identity.py`): isotonic regression (fallback Platt scaling) mapping similarity -> P(same). UI then shows "Person #17: 91%".
- Always store and show the **top 3 candidates**, and "collecting evidence..." until enough crops.
- Registered-action identity filter "specific person >= 80%" uses the track-level calibrated score.

## Face module (OPTIONAL, OFF)
InsightFace/ArcFace, only when face width >= 70 px and roughly frontal; fused score = w_body*body + w_face*face. Disabled by default (`face.enabled: false`) - biometric data, needs department sign-off. Implement the interface stub only; do not enable.

## Vehicles (Step 14, after person identity passes)
Plate DETECTION needs a trained model: the human downloads an Indian licence-plate dataset (Roboflow Universe/Kaggle, licence checked) into `dataset/plates/`; the agent writes the training script (`yolo detect train data=... model=yolo11s.pt epochs=50 imgsz=640 device=0`, one class `plate`) and keeps the better of trained vs any pretrained alternative on the same validation set. Plate READING uses a pretrained OCR (PaddleOCR/EasyOCR), no training.

Design notes:
Plate detector (YOLO fine-tuned on Indian plates) + OCR (PaddleOCR/EasyOCR). Match % = OCR confidence x string similarity (allow 1-char mismatch); fallback appearance embedding at night/bad angle. Same Identity Manager, different encoder.

## Admin tools
Merge two identities, split identity (reassign sightings), rename label, delete identity (and embeddings) - all audit-logged.

## Persisted per sighting
identity_id, camera, track, start/end, score, top3. Incident grouping: same identity on multiple cameras within `incident_window_s` (default 900) -> one incident.

## Limitations to state in the report
Clothing-based; same uniform confusable; IR/night grayscale removes colour cues; identities hold hours to ~1 day; lookalikes; needs own-footage threshold tuning.

## Metrics (see 08)
Re-ID Rank-1 and mAP on the reid_walk clips (test_data/); cross-camera IDF1 and ID switches.
