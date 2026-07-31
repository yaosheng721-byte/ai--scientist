from dataclasses import dataclass, field


@dataclass
class DatasetProfilingOutput:

    dataset_scan: dict = field(default_factory=dict)

    coco_profile: dict = field(default_factory=dict)

    image_quality: dict = field(default_factory=dict)

    sample: dict = field(default_factory=dict)

    defect: dict = field(default_factory=dict)