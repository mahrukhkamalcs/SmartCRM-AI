from typing import Tuple

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


TARGET_CANDIDATES = (
	"converted",
	"conversion",
	"is_converted",
	"conversion_status",
	"lead_converted",
)


def find_target_column(dataframe: pd.DataFrame) -> str:
	normalized_columns = {
		str(column).strip().lower(): column for column in dataframe.columns
	}
	for candidate in TARGET_CANDIDATES:
		if candidate in normalized_columns:
			return normalized_columns[candidate]

	raise ValueError(
		"Could not identify a lead conversion target column. "
		f"Expected one of: {', '.join(TARGET_CANDIDATES)}."
	)


def prepare_features(
	dataframe: pd.DataFrame, target_column: str
) -> Tuple[pd.DataFrame, pd.Series, ColumnTransformer]:
	if dataframe.empty:
		raise ValueError("The CRM dataset is empty.")

	features = dataframe.drop(columns=[target_column])
	target = dataframe[target_column]
	if features.shape[1] == 0:
		raise ValueError("The CRM dataset has no feature columns.")

	numeric_features = features.select_dtypes(include=["number"]).columns.tolist()
	categorical_features = features.select_dtypes(
		exclude=["number"]
	).columns.tolist()

	transformers = []
	if numeric_features:
		numeric_pipeline = Pipeline(
			steps=[
				("imputer", SimpleImputer(strategy="median")),
				("scaler", StandardScaler()),
			]
		)
		transformers.append(("numeric", numeric_pipeline, numeric_features))
	if categorical_features:
		categorical_pipeline = Pipeline(
			steps=[
				("imputer", SimpleImputer(strategy="most_frequent")),
				("onehot", OneHotEncoder(handle_unknown="ignore")),
			]
		)
		transformers.append(
			("categorical", categorical_pipeline, categorical_features)
		)

	preprocessor = ColumnTransformer(transformers=transformers)
	return features, target, preprocessor
