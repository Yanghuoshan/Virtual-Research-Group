# Vision Split Integrity

Visual datasets leak through subjects, scenes and acquisition sessions, not only through duplicate files.

## Grouping Keys

| Data type | Group by | Why |
|---|---|---|
| Medical imaging | Patient, study, scanner | Multiple slices/images per patient are correlated |
| Video | Clip, scene, sequence | Adjacent frames are near-duplicates |
| Multi-view | Capture session, subject | Same object under different views |
| Web images | Source URL, near-duplicate cluster | Reposted images appear across splits |

## Checks

1. Exact duplicates: hash or byte comparison.
2. Near-duplicates: perceptual hash or embedding similarity with a declared threshold; record the threshold.
3. Subject/session overlap: verify the group identifier, not just the file name.
4. Temporal adjacency: video frames adjacent in time must not straddle splits when the claim is about unseen scenes.
5. Annotation consistency: label schema version, inter-annotator differences, ignored regions.
6. Preprocessing: resizing, normalization statistics and augmentation fitted on training data only.

## Preprocessing and Label Pitfalls

- Interpolation creating fractional class IDs in segmentation masks.
- Resizing that changes coordinate conventions for boxes or masks.
- Normalization statistics computed over the full dataset.
- Augmentations applied to evaluation data, or to held-out labels.
- Mismatched label spaces between prediction files and ground truth.

## Reporting

| Item | Content |
|---|---|
| Grouping key | What defines an independent unit |
| Duplicate/near-duplicate checks | Method, threshold, counts |
| Overlaps found | Location, affected claim, severity |
| Independent unit count | Groups, not images |
| Unresolved | What could not be verified from supplied manifests |

Report the number of independent subjects or scenes alongside image counts; image counts alone overstate sample size.
