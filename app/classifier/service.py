"""Vehicle image classifier using a pretrained EfficientNet-B0 model.

EfficientNet-B0 pretrained on ImageNet (~5.3M parameters, ~20 MB weights).
ImageNet class indices are mapped to simplified vehicle categories.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image
from torchvision import models

logger = logging.getLogger(__name__)

# ImageNet class index → vehicle category
# Reference: https://gist.github.com/yrevar/942d3a0ac09ec9e5eb3a
VEHICLE_CLASS_MAP: dict[int, str] = {
    # samochód osobowy
    407: "samochód osobowy",   # sports car
    436: "samochód osobowy",   # beach wagon
    511: "samochód osobowy",   # convertible
    609: "samochód osobowy",   # jeep
    627: "samochód osobowy",   # limousine
    656: "samochód osobowy",   # minivan
    661: "samochód osobowy",   # Model T
    817: "samochód osobowy",   # sports car (alt)
    # taxi
    468: "taxi",               # cab
    # SUV / terenowy
    734: "SUV / terenowy",     # police van
    # ciężarówka / TIR
    555: "ciężarówka / TIR",   # fire engine
    569: "ciężarówka / TIR",   # garbage truck
    671: "ciężarówka / TIR",   # moving van
    675: "ciężarówka / TIR",   # pickup truck
    717: "ciężarówka / TIR",   # pickup truck (alt)
    757: "ciężarówka / TIR",   # recreational vehicle
    864: "ciężarówka / TIR",   # tow truck
    867: "ciężarówka / TIR",   # trailer truck / TIR
    # motocykl
    665: "motocykl",           # moped
    670: "motocykl",           # motor scooter
    # autobus
    779: "autobus",            # school bus
    874: "autobus",            # trolleybus
    # van / minivan
    654: "van / minivan",      # minibus
}


@dataclass
class ClassificationResult:
    """Result of classifying a single image."""

    predicted_class: str
    confidence: float
    imagenet_label: str
    imagenet_class_id: int


class VehicleClassifier:
    """Wraps EfficientNet-B0 pretrained on ImageNet for vehicle classification."""

    def __init__(self) -> None:
        self._model = None
        self._transform = None
        self._labels: list[str] = []

    def load(self) -> None:
        if self._model is not None:
            return

        logger.info("Loading EfficientNet-B0 pretrained model …")
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
        self._model = models.efficientnet_b0(weights=weights)
        self._model.eval()
        self._transform = weights.transforms()
        self._labels = weights.meta["categories"]
        logger.info("Model loaded (%d classes).", len(self._labels))

    def classify(self, image_path: str | Path) -> ClassificationResult:
        self.load()

        print(image_path)
        img = Image.open(image_path).convert("RGB")
        tensor = self._transform(img).unsqueeze(0)

        with torch.no_grad():
            logits = self._model(tensor)
            probs = torch.nn.functional.softmax(logits, dim=1)
            confidence, class_id = probs.topk(1, dim=1)

        class_idx = class_id.item()
        conf = round(confidence.item(), 4)

        return ClassificationResult(
            predicted_class=VEHICLE_CLASS_MAP.get(class_idx, "inne"),
            confidence=conf,
            imagenet_label=self._labels[class_idx],
            imagenet_class_id=class_idx,
        )

    def classify_top_k(self, image_path: str | Path, k: int = 5) -> list[ClassificationResult]:
        self.load()

        img = Image.open(image_path).convert("RGB")
        tensor = self._transform(img).unsqueeze(0)

        with torch.no_grad():
            logits = self._model(tensor)
            probs = torch.nn.functional.softmax(logits, dim=1)
            confidences, class_ids = probs.topk(k, dim=1)

        return [
            ClassificationResult(
                predicted_class=VEHICLE_CLASS_MAP.get(class_ids[0][i].item(), "inne"),
                confidence=round(confidences[0][i].item(), 4),
                imagenet_label=self._labels[class_ids[0][i].item()],
                imagenet_class_id=class_ids[0][i].item(),
            )
            for i in range(k)
        ]


# Singleton
classifier = VehicleClassifier()
