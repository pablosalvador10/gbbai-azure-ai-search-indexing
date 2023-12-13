from typing import Any, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn import metrics

from utils.ml_logging import get_logger

# Set up logging
logger = get_logger()


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


def get_metrics_score(
    model: Any,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    log_scores: bool = True,
) -> List[float]:
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
    score_list: List[float] = []

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


def generate_comparison_frame(
    models: List[Any],
    model_names: List[str],
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    log_scores: bool = True,
) -> pd.DataFrame:
    """
    Generate a comparison DataFrame for given models based on their metrics.

    Parameters:
    models (List[ClassifierMixin]): A list of trained sklearn models.
    model_names (List[str]): A list of names corresponding to the models.
    X_train (array): Training set.
    y_train (array): Training set labels.
    X_test (array): Test set.
    y_test (array): Test set labels.
    log_scores (bool): Flag to log the scores. Default is True.

    Returns:
    pd.DataFrame: A DataFrame with Train and Test Accuracy, Recall, and Precision for each model.
    """

    # Initializing empty lists to store metrics
    acc_train, acc_test = [], []
    recall_train, recall_test = [], []
    precision_train, precision_test = [], []

    # Loop through models, get metrics, and append to respective lists
    for model in models:
        (
            train_acc,
            test_acc,
            train_recall,
            test_recall,
            train_precision,
            test_precision,
        ) = get_metrics_score(
            model, X_train, y_train, X_test, y_test, log_scores=log_scores
        )
        acc_train.append(np.round(train_acc, 2))
        acc_test.append(np.round(test_acc, 2))
        recall_train.append(np.round(train_recall, 2))
        recall_test.append(np.round(test_recall, 2))
        precision_train.append(np.round(train_precision, 2))
        precision_test.append(np.round(test_precision, 2))

    # Create and return comparison DataFrame
    comparison_frame = pd.DataFrame(
        {
            "Model": model_names,
            "Train_Accuracy": acc_train,
            "Test_Accuracy": acc_test,
            "Train_Recall": recall_train,
            "Test_Recall": recall_test,
            "Train_Precision": precision_train,
            "Test_Precision": precision_test,
        }
    )

    return comparison_frame
