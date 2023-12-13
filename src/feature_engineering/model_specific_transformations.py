import numpy as np
import pandas as pd
from sklearn import preprocessing

from utils.ml_logging import get_logger, log_function_call

# Set up logging
logger = get_logger()


@log_function_call("Feature Engineering")
def log_transform_features(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Apply log transformation to specified features in the DataFrame.

    :param df: Input DataFrame.
    :param features: List of feature names to be log-transformed.
    :return: DataFrame with log-transformed features.
    """
    for feature in features:
        df[feature] = df[feature].apply(lambda x: np.log(x + 1))
    return df


@log_function_call("Feature Engineering")
def encode_categorical_features(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Encode categorical features using LabelEncoder.

    :param df: Input DataFrame.
    :param features: List of categorical feature names to be encoded.
    :return: DataFrame with encoded categorical features.
    """
    labelencoder = preprocessing.LabelEncoder()
    for feature in features:
        df[feature] = labelencoder.fit_transform(df[feature])
    return df


@log_function_call("Feature Engineering")
def apply_one_hot_encoding(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Apply one-hot encoding to specified columns in the DataFrame.

    :param df: Input DataFrame.
    :param columns: List of columns names to be one-hot encoded.
    :return: DataFrame with one-hot encoded columns.
    """
    return pd.get_dummies(df, columns=columns)


@log_function_call("Feature Engineering")
def replace_values(df: pd.DataFrame, replace_structure: dict) -> pd.DataFrame:
    """
    Replace values in the DataFrame based on a provided structure.

    :param df: Input DataFrame.
    :param replace_structure: Dictionary with structure {column: {old_value: new_value}}.
    :return: DataFrame with values replaced as per replace_structure.
    """
    return df.replace(replace_structure)
