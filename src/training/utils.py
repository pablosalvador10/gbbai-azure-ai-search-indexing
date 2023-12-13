import os
from datetime import datetime
from typing import Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn import metrics

from utils.ml_logging import get_logger, log_function_call

# Set up logging
logger = get_logger()


@log_function_call("Training - evaluation")
def make_confusion_matrix(model, X_test, y_actual, labels=[1, 0]):
    """
    Generate confusion matrix for the fitted model.

    Parameters:
    model (Model): Classifier to predict values of X_test.
    X_test (array): Test set.
    y_actual (array): Ground truth.
    labels (list): List of labels to create confusion matrix.

    Returns:
    None
    """
    y_predict = model.predict(X_test)
    cm = metrics.confusion_matrix(y_actual, y_predict, labels=labels)
    df_cm = pd.DataFrame(
        cm,
        index=[f"Actual - {label}" for label in labels],
        columns=[f"Predicted - {label}" for label in labels],
    )
    group_counts = ["{0:0.0f}".format(value) for value in cm.flatten()]
    group_percentages = ["{0:.2%}".format(value) for value in cm.flatten() / np.sum(cm)]
    labels = [f"{v1}\n{v2}" for v1, v2 in zip(group_counts, group_percentages)]
    labels = np.asarray(labels).reshape(2, 2)
    plt.figure(figsize=(10, 7))
    sns.heatmap(df_cm, annot=labels, fmt="")
    plt.ylabel("True label")
    plt.xlabel("Predicted label")


@log_function_call("Training - evaluation")
def get_metrics_score(model, X_train, y_train, X_test, y_test, log_scores=True):
    """
    Calculate different metric scores of the model - Accuracy, Recall, and Precision.

    Parameters:
    model (Model): Classifier to predict values of X.
    X_train (array): Training set.
    y_train (array): Training set labels.
    X_test (array): Test set.
    y_test (array): Test set labels.
    log_scores (bool): Flag to log the scores. Default is True.

    Returns:
    list: List containing metric scores.
    """
    # defining an empty list to store train and test results
    score_list = []

    # Predictions
    pred_train = model.predict(X_train)
    pred_test = model.predict(X_test)

    # Accuracy
    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test)

    # Recall
    train_recall = metrics.recall_score(y_train, pred_train)
    test_recall = metrics.recall_score(y_test, pred_test)

    # Precision
    train_precision = metrics.precision_score(y_train, pred_train)
    test_precision = metrics.precision_score(y_test, pred_test)

    score_list.extend(
        (
            train_acc,
            test_acc,
            train_recall,
            test_recall,
            train_precision,
            test_precision,
        )
    )

    if log_scores:
        logger.info(f"Accuracy on training set : {train_acc}")
        logger.info(f"Accuracy on test set : {test_acc}")
        logger.info(f"Recall on training set : {train_recall}")
        logger.info(f"Recall on test set : {test_recall}")
        logger.info(f"Precision on training set : {train_precision}")
        logger.info(f"Precision on test set : {test_precision}")

    return score_list


def load_datasets(
    directory: str, date: Optional[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load X_train, X_test, y_train, and y_test from CSV files.

    Parameters:
    directory (str): Directory to load the CSV files from.
    date (str, optional): Date string. Defaults to today's date in format 'day_month_year'.

    Returns:
    tuple: Tuple containing DataFrames (X_train, X_test, y_train, y_test).
    """

    # Set default date to today if not provided
    if date is None:
        date = datetime.today().strftime("%d_%m_%Y")

    # Define file paths
    x_train_path = os.path.join(directory, f"X_train_{date}.csv")
    x_test_path = os.path.join(directory, f"X_test_{date}.csv")
    y_train_path = os.path.join(directory, f"y_train_{date}.csv")
    y_test_path = os.path.join(directory, f"y_test_{date}.csv")

    # Check if files exist
    if not all(
        os.path.exists(path)
        for path in [x_train_path, x_test_path, y_train_path, y_test_path]
    ):
        logger.error(
            f"One or more files not found in directory: {directory} for date: {date}"
        )
        raise FileNotFoundError("One or more dataset files not found.")

    # Load datasets
    X_train = pd.read_csv(x_train_path)
    X_test = pd.read_csv(x_test_path)
    y_train = pd.read_csv(y_train_path)
    y_test = pd.read_csv(y_test_path)

    logger.info(f"Datasets loaded from directory: {directory} for date: {date}")

    return X_train, X_test, y_train, y_test


@log_function_call("Training - utils")
def save_datasets(
    X_train: Union[pd.DataFrame, pd.Series],
    X_test: Union[pd.DataFrame, pd.Series],
    y_train: Union[pd.DataFrame, pd.Series],
    y_test: Union[pd.DataFrame, pd.Series],
    directory: str,
    date: Optional[str] = None,
) -> None:
    """
    Save X_train, X_test, y_train, and y_test as CSV files.

    Parameters:
    X_train (DataFrame/Series): Training data features.
    X_test (DataFrame/Series): Test data features.
    y_train (DataFrame/Series): Training data target.
    y_test (DataFrame/Series): Test data target.
    directory (str): Directory to save the CSV files.
    date (str, optional): Date string. Defaults to today's date in format 'day_month_year'.
    """

    # Set default date to today if not provided
    if date is None:
        date = datetime.today().strftime("%d_%m_%Y")

    # Create directory if it does not exist
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

    # Convert data to DataFrame if they are Series
    if isinstance(X_train, (pd.Series, np.ndarray)):
        X_train = pd.DataFrame(X_train)
    if isinstance(X_test, (pd.Series, np.ndarray)):
        X_test = pd.DataFrame(X_test)
    if isinstance(y_train, (pd.Series, np.ndarray)):
        y_train = pd.DataFrame(y_train)
    if isinstance(y_test, (pd.Series, np.ndarray)):
        y_test = pd.DataFrame(y_test)

    # Save datasets as CSV files
    X_train.to_csv(os.path.join(directory, f"X_train_{date}.csv"), index=False)
    logger.info(f"X_train saved at {os.path.join(directory, f'X_train_{date}.csv')}")

    X_test.to_csv(os.path.join(directory, f"X_test_{date}.csv"), index=False)
    logger.info(f"X_test saved at {os.path.join(directory, f'X_test_{date}.csv')}")

    y_train.to_csv(os.path.join(directory, f"y_train_{date}.csv"), index=False)
    logger.info(f"y_train saved at {os.path.join(directory, f'y_train_{date}.csv')}")

    y_test.to_csv(os.path.join(directory, f"y_test_{date}.csv"), index=False)
    logger.info(f"y_test saved at {os.path.join(directory, f'y_test_{date}.csv')}")
