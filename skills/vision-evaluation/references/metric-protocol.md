# Vision Metric Protocol

Vision metrics are families, not single numbers. Pin every threshold and convention before comparing.

## Detection

| Parameter | Must be declared |
|---|---|
| IoU threshold(s) | Single threshold or COCO-style range |
| Score/confidence handling | Score threshold applied, or all detections retained |
| Nonmaximum suppression | IoU threshold and class-wise vs global |
| Max detections per image | Cap value |
| Averaging | AP per class then mean, or mAP@[.5:.95] |

Do not compare AP at IoU=0.5 with mAP@[.5:.95] as one number.

## Segmentation

| Parameter | Must be declared |
|---|---|
| Class averaging | Macro vs micro |
| Background/void handling | Included or ignored |
| Absent classes | Skip, or count as zero |
| Aggregation | Per-image mean vs global intersection over union |

## Classification and Calibration

- Class balance and per-class support; macro vs micro averaging.
- Calibration claims: reliability, temperature or binning method, and the data used (never the test set).
- Threshold or checkpoint selection: validation only.

## Comparison Protocol

1. Match input resolution, preprocessing, evaluation transforms and pretraining exposure.
2. Match or declare the tuning budget and inference cost.
3. Pair by image/split and report the distribution of differences across images or folds.
4. Report subgroup performance (class, domain, resolution) instead of a single headline number.

## Reporting Table

| Metric | Parameters | Aggregation | Notes |
|---|---|---|---|
| mAP | IoU 0.5:0.95, NMS 0.5, max 100 det | Mean over classes | COCO-style implementation, version recorded |

Record metric library version and any custom code: implementations differ in tie handling and interpolation.
