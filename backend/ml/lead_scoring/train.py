from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from backend.ml.lead_scoring.features import find_target_column, prepare_features


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = PROJECT_ROOT / "backend" / "data" / "crm_dataset.csv"
MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"


def main():
	try:
		dataframe = pd.read_csv(DATASET_PATH)
	except pd.errors.EmptyDataError as error:
		raise ValueError("The CRM dataset is empty and has no columns.") from error

	target_column = find_target_column(dataframe)
	features, target, preprocessor = prepare_features(dataframe, target_column)

	if target.nunique(dropna=True) < 2:
		raise ValueError("The lead conversion target must contain at least two classes.")

	x_train, x_test, y_train, y_test = train_test_split(
		features,
		target,
		test_size=0.2,
		random_state=42,
		stratify=target,
	)

	model = Pipeline(
		steps=[
			("preprocessor", preprocessor),
			("classifier", LogisticRegression(max_iter=1000)),
		]
	)
	model.fit(x_train, y_train)
	predictions = model.predict(x_test)

	print(f"Training dataset: {DATASET_PATH}")
	print(f"Target column: {target_column}")
	print(f"Training rows: {len(x_train)}")
	print(f"Testing rows: {len(x_test)}")
	print("Evaluation results:")
	print(f"Accuracy: {accuracy_score(y_test, predictions):.4f}")
	print(
		f"Precision: {precision_score(y_test, predictions, average='weighted', zero_division=0):.4f}"
	)
	print(
		f"Recall: {recall_score(y_test, predictions, average='weighted', zero_division=0):.4f}"
	)
	print(f"F1-score: {f1_score(y_test, predictions, average='weighted', zero_division=0):.4f}")

	MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
	joblib.dump(model, MODEL_PATH)
	print(f"Model saved to: {MODEL_PATH}")


if __name__ == "__main__":
	main()
