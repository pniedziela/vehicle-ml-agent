"""Tests for the vehicle image classifier."""

import ast
import inspect
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

from app.classifier.service import VehicleClassifier, ClassificationResult, VEHICLE_CLASS_MAP
import app.classifier.service as classifier_module


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a sample test image."""
    img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    path = tmp_path / "test_car.jpg"
    img.save(str(path))
    return path


@pytest.fixture
def classifier_instance() -> VehicleClassifier:
    """Create a classifier instance (model will be loaded on first use)."""
    return VehicleClassifier()


class TestVehicleClassifier:
    """Tests for VehicleClassifier."""

    def test_classify_returns_result(self, classifier_instance: VehicleClassifier, sample_image: Path):
        """Classifier should return a ClassificationResult for any image."""
        result = classifier_instance.classify(sample_image)
        assert isinstance(result, ClassificationResult)
        assert isinstance(result.predicted_class, str)
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.imagenet_label, str)
        assert isinstance(result.imagenet_class_id, int)

    def test_classify_top_k(self, classifier_instance: VehicleClassifier, sample_image: Path):
        """Top-k should return k results."""
        results = classifier_instance.classify_top_k(sample_image, k=5)
        assert len(results) == 5
        # Confidences should be sorted descending
        for i in range(len(results) - 1):
            assert results[i].confidence >= results[i + 1].confidence

    def test_vehicle_class_map_has_entries(self):
        """The vehicle class mapping should contain real entries."""
        assert len(VEHICLE_CLASS_MAP) > 10
        categories = set(VEHICLE_CLASS_MAP.values())
        assert "samochód osobowy" in categories
        assert "motocykl" in categories
        assert "ciężarówka / TIR" in categories

    def test_model_loaded_once(self, classifier_instance: VehicleClassifier, sample_image: Path):
        """Model should only be loaded once (lazy singleton)."""
        classifier_instance.classify(sample_image)
        assert classifier_instance._model is not None
        model_ref = classifier_instance._model
        # Second call should not reload
        classifier_instance.load()
        assert classifier_instance._model is model_ref

    def test_classify_invalid_path(self, classifier_instance: VehicleClassifier):
        """Classifier should raise an error for non-existent files."""
        with pytest.raises(FileNotFoundError):
            classifier_instance.classify("/nonexistent/path.jpg")

    def test_no_duplicate_keys_in_class_map(self):
        """VEHICLE_CLASS_MAP must not have duplicate keys (regression test).

        Python dicts silently overwrite duplicate keys, so we parse the
        source file with AST to verify all keys are unique.
        """
        source_file = Path(inspect.getfile(classifier_module))
        tree = ast.parse(source_file.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            # Handle both plain assignment (VEHICLE_CLASS_MAP = {...})
            # and annotated assignment (VEHICLE_CLASS_MAP: dict[...] = {...})
            if isinstance(node, ast.AnnAssign):
                target = node.target
                value = node.value
            elif isinstance(node, ast.Assign):
                if len(node.targets) != 1:
                    continue
                target = node.targets[0]
                value = node.value
            else:
                continue

            if isinstance(target, ast.Name) and target.id == "VEHICLE_CLASS_MAP":
                assert isinstance(value, ast.Dict)
                keys = [
                    k.value for k in value.keys  # type: ignore
                    if isinstance(k, ast.Constant)
                ]
                duplicates = [k for k in keys if keys.count(k) > 1]
                assert len(duplicates) == 0, (
                    f"Duplicate keys found in VEHICLE_CLASS_MAP: {set(duplicates)}"
                )
                return

        pytest.fail("VEHICLE_CLASS_MAP assignment not found in source file")
