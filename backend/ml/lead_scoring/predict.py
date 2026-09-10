from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd


MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"


def _load_model():
	try:
		return joblib.load(MODEL_PATH)
	except FileNotFoundError as error:
		raise RuntimeError(f"Lead scoring model not found: {MODEL_PATH}") from error
	except Exception as error:
		raise RuntimeError(
		f"Lead scoring model could not be loaded from {MODEL_PATH}: {error}"
	) from error


def predict_lead_score(features: Mapping[str, Any]) -> dict[str, Any]:
	if not isinstance(features, Mapping):
		raise ValueError("Lead scoring features must be provided as a mapping.")

	model = _load_model()
	model_features = getattr(model, "feature_names_in_", None)
	if model_features is not None:
		feature_row = {feature: features.get(feature) for feature in model_features}
	else:
		feature_row = dict(features)

	try:
		dataframe = pd.DataFrame([feature_row])
		prediction = int(model.predict(dataframe)[0])
		probabilities = model.predict_proba(dataframe)[0]
		classes = list(getattr(model, "classes_", []))
		positive_index = classes.index(1) if 1 in classes else int(prediction == 1)
		conversion_probability = float(probabilities[positive_index])
	except (TypeError, ValueError, KeyError, IndexError) as error:
		raise ValueError(f"Invalid lead scoring input: {error}") from error

	return {
		"prediction": prediction,
		"conversion_probability": conversion_probability,
		"lead_score": round(conversion_probability * 100),
	}
