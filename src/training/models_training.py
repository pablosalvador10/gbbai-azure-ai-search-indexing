from typing import Any, List, Literal, Optional, Tuple, Union

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from sklearn import decomposition, metrics
from sklearn.base import ClassifierMixin
from sklearn.ensemble import AdaBoostClassifier, StackingClassifier
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline

from src.training.utils import get_metrics_score, make_confusion_matrix
from src.utils import load_dataframe_from_path
from utils.ml_logging import get_logger, log_function_call

# Set up logging
logger = get_logger()


class ModelTrainer:
    """
    Class for training ensemble classifiers using randomized search.

    Parameters:
        features_path (Optional[str]): Path to the file containing features and target labels.
                                      If None, X_train and y_train must be provided.
        estimator: AdaBoostClassifier or BaggingClassifier.
        random_state (int): Random seed for reproducibility (default=555).
        X_train (Optional[pd.DataFrame]): Training data features.
        y_train (Optional[pd.Series]): Training data target variable.
        X_test (Optional[pd.DataFrame]): Testing data features.
        y_test (Optional[pd.Series]): Testing data target variable.
    """

    ESTIMATOR_MAPPING = {
        "AdaBoostClassifier": AdaBoostClassifier,
        # 'AnotherClassifier': AnotherClassifierClass,  # Add more classifiers here as needed.
    }

    def __init__(
        self,
        estimator: str,
        features_path: Optional[str] = None,
        random_state: int = 555,
        X_train: Optional[pd.DataFrame] = None,
        y_train: Optional[pd.Series] = None,
        X_test: Optional[pd.DataFrame] = None,
        y_test: Optional[pd.Series] = None,
    ):
        self.features_path = features_path
        self.random_state = random_state
        if estimator in self.ESTIMATOR_MAPPING:
            self.estimator = self.ESTIMATOR_MAPPING[estimator](
                random_state=random_state
            )
        else:
            raise ValueError(f"Unsupported estimator type: {estimator}")
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test

        if self.features_path:
            self.df = load_dataframe_from_path(self.features_path)
            logger.info(
                f"ModelTrainer initialized with data from {self.features_path}."
            )
        elif (self.X_train is not None and self.y_train is not None) or (
            self.X_test is not None and self.y_test is not None
        ):
            logger.info("ModelTrainer initialized with provided data.")
        else:
            raise ValueError(
                "Either features_path or training and testing data must be provided."
            )

    def run_hyperparameter_opt(
        self,
        scorer: Literal["Recall"] = "Recall",
        parameters: dict = {},
        n_jobs: int = -1,
        n_iter_search: int = 500,
        apply_pca: Optional[bool] = None,
    ) -> Any:
        """
        Train a specified classifier with or without PCA.

        :param scorer: The scorer type. Currently only supports 'Recall'.
        :param parameters: Dictionary of parameters to be used for RandomizedSearchCV.
        :param n_jobs: Number of jobs to run in parallel.
        :param n_iter_search: Number of parameter settings that are sampled.
        :param apply_pca: Whether to apply PCA before training the classifier.
        :return: The estimator trained with the best found parameters.
        """

        if self.X_train is None or self.y_train is None:
            raise ValueError(
                "X_train and y_train cannot be None. Please provide valid training data."
            )

        try:
            logger.info(
                f"Starting training for {type(self.estimator).__name__} with scorer {scorer}."
            )

            if apply_pca:
                pca = decomposition.PCA()
                pipe = Pipeline(
                    steps=[
                        ("pca", pca),
                        (str(type(self.estimator).__name__), self.estimator),
                    ]
                )
                logger.info("PCA is applied before training.")
            else:
                pipe = Pipeline(
                    steps=[(str(type(self.estimator).__name__), self.estimator)]
                )

            grid_obj = self._perform_randomized_search(
                pipe, parameters, scorer, n_jobs, n_iter_search
            )
            tuned_estimator = grid_obj.best_estimator_
            tuned_estimator.fit(self.X_train, self.y_train)

            # Log the best parameters
            logger.info(f"Best parameters after search: {grid_obj.best_params_}")

            get_metrics_score(
                tuned_estimator, self.X_train, self.y_train, self.X_test, self.y_test
            )

            make_confusion_matrix(tuned_estimator, self.X_test, self.y_test)

            logger.info(f"Training successful for {type(self.estimator).__name__}.")

            return tuned_estimator

        except Exception as e:
            logger.error(
                f"Error occurred during training for {type(self.estimator).__name__}: {e}"
            )
            raise e

    @log_function_call("Training - Hyperparameter Opt")
    def _make_scoring(self, scorer_type: Literal["Recall"]) -> Any:
        """
        Create a scorer based on the provided type.

        Parameters:
            scorer_type: Type of scorer to be created.

        Returns:
            acc_scorer: Scorer function.
        """
        try:
            logger.info(f"Creating scorer of type {scorer_type}.")

            if scorer_type == "Recall":
                acc_scorer = metrics.make_scorer(metrics.recall_score)
                logger.info(f"Scorer of type {scorer_type} created successfully.")
                return acc_scorer

            else:
                logger.warning(
                    f"Scorer type {scorer_type} not recognized. Returning None."
                )
                return None

        except Exception as e:
            logger.error(
                f"Error occurred while creating scorer of type {scorer_type}: {e}"
            )
            raise e

    @log_function_call("Training - Hyperparameter Opt")
    def _perform_randomized_search(
        self,
        estimator: Any,
        parameters: dict,
        scorer: Literal["Recall"],
        n_jobs: int = -1,
        n_iter_search: int = 500,
        cv: int = 5,
    ) -> Any:
        """
        Perform randomized search for hyperparameter tuning.

        Parameters:
            estimator: Classifier to tune.
            parameters: Hyperparameters and their possible values.
            scorer: Scorer type to be used.
            n_jobs: Number of jobs to run in parallel.
            n_iter_search: Number of parameter settings that are sampled.
            cv: Number of folds in cross-validation.

        Returns:
            grid_obj: Trained RandomizedSearchCV object.
        """
        try:
            logger.info(f"Initiating Randomized Search for {estimator}.")
            acc_scorer = self._make_scoring(scorer)
            grid_obj = RandomizedSearchCV(
                estimator,
                n_iter=n_iter_search,
                param_distributions=parameters,
                scoring=acc_scorer,
                cv=cv,
                n_jobs=n_jobs,
            )
            grid_obj.fit(self.X_train, self.y_train)
            logger.info(
                f"Randomized Search successful for {estimator}. Best parameters: {grid_obj.best_params_}"
            )
            return grid_obj
        except Exception as e:
            logger.error(
                f"Error occurred during Randomized Search for {estimator}: {e}"
            )
            raise e

    @log_function_call("Training - Data Preparation")
    def split_data(
        self,
        target_column: Optional[str] = None,
        df: Optional[Union[pd.DataFrame, str]] = None,
        X: Optional[pd.DataFrame] = None,
        y: Optional[pd.Series] = None,
        test_size: float = 0.2,
    ) -> tuple:
        """
        Split data into training and testing sets and separate target variable.

        :param df: Input DataFrame. Default is None.
        :param target_column: The name of the target variable column. Default is None.
        :param X: Input features. Default is None.
        :param y: Target variable. Default is None.
        :param test_size: Proportion of the dataset included in the test split.
        :return: Tuple of (X_train, X_test, y_train, y_test).
        """
        if X is not None and y is not None:
            # If X and y are provided, directly split the data
            pass

        elif self.df is not None:
            X = self.df.drop(target_column, axis=1)
            y = self.df.pop(target_column)

        elif df is not None:
            if isinstance(df, str):
                df = load_dataframe_from_path(df)
            X = df.drop(target_column, axis=1)
            y = df.pop(target_column)

        else:
            raise ValueError("Either provide df and target_column or X and y.")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state, stratify=y
        )
        return X_train, X_test, y_train, y_test

    @log_function_call("Training - Upsampling")
    def perform_upsampling(
        self,
        target_column: str,
        data: Optional[Union[pd.DataFrame, str]] = None,
        strategy: float = 1,
        k_neighbors: int = 5,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Perform upsampling on the dataset to balance it.

        Parameters:
        data (Union[DataFrame, str]): The input data or the path to the CSV file.
        target_column (str): Name of the target variable column.
        strategy (float): The sampling strategy for SMOTE. Default is 1.
        k_neighbors (int): Number of nearest neighbours used to construct synthetic samples. Default is 5.

        Returns:
        X_train_res (DataFrame): The input features after resampling.
        y_train_res (Series): The target variable after resampling.
        """
        if self.df is not None:
            data = self.df.copy()
        elif data is not None:
            if isinstance(data, str):
                data = load_dataframe_from_path(data)

        X_train = data.drop(target_column, axis=1)
        y_train = data[target_column]

        logger.info(f"Before Upsampling, counts of label '1': {sum(y_train==1)}")
        logger.info(f"Before Upsampling, counts of label '0': {sum(y_train==0)}")

        sm = SMOTE(
            sampling_strategy=strategy,
            k_neighbors=k_neighbors,
            random_state=self.random_state,
        )
        X_train_res, y_train_res = sm.fit_resample(X_train, y_train.ravel())

        logger.info(f"After Upsampling, counts of label '1': {sum(y_train_res==1)}")
        logger.info(f"After Upsampling, counts of label '0': {sum(y_train_res==0)}")

        return X_train_res, y_train_res

    @log_function_call("Training - Downsampling")
    def perform_downsampling(
        self,
        target_column: str,
        data: Optional[Union[pd.DataFrame, str]] = None,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Perform downsampling on the dataset to balance it.

        Parameters:
        data (Union[DataFrame, str]): The input data or the path to the CSV file.
        target_column (str): Name of the target variable column.

        Returns:
        X_train_res (DataFrame): The input features after resampling.
        y_train_res (Series): The target variable after resampling.
        """
        if self.df is not None:
            data = self.df.copy()
        elif data is not None:
            if isinstance(data, str):
                data = load_dataframe_from_path(data)

        X_train = data.drop(target_column, axis=1)
        y_train = data[target_column]

        logger.info(f"Before Downsampling, counts of label '1': {sum(y_train==1)}")
        logger.info(f"Before Downsampling, counts of label '0': {sum(y_train==0)}")

        rus = RandomUnderSampler()
        X_train_res, y_train_res = rus.fit_resample(X_train, y_train)

        logger.info(f"After Downsampling, counts of label '1': {sum(y_train_res==1)}")
        logger.info(f"After Downsampling, counts of label '0': {sum(y_train_res==0)}")

        return X_train_res, y_train_res

    def stack_and_fit_models(
        self,
        base_models: List[Tuple[str, ClassifierMixin]],
        meta_model: ClassifierMixin,
        X_train: np.ndarray,
        y_train: np.ndarray,
        refit_base_models: bool = False,
    ) -> StackingClassifier:
        """
        Stack the given base models, fit the StackingClassifier on the training data, and return the fitted classifier.

        Parameters:
        base_models (List[Tuple[str, ClassifierMixin]]): List of (name, model) tuples.
        meta_model (ClassifierMixin): Meta-model for stacking.
        X_train (np.ndarray): Training data.
        y_train (np.ndarray): Training labels.
        refit_base_models (bool): Flag indicating whether to refit base models.

        Returns:
        StackingClassifier: Fitted StackingClassifier.
        """
        try:
            if refit_base_models:
                logger.info("Refitting base models.")
                # Extract parameters from base models, instantiate new copies
                new_base_models = [
                    (name, model.__class__(**model.get_params()))
                    for name, model in base_models
                ]
                base_models = new_base_models

            # Instantiate and fit StackingClassifier
            logger.info("Instantiating and fitting StackingClassifier.")
            stacking_model = StackingClassifier(
                estimators=base_models,
                final_estimator=meta_model,
                passthrough=True,
                cv=5,
                verbose=2,
            )
            stacking_model.fit(X_train, y_train)
            logger.info("StackingClassifier fitted successfully.")
            return stacking_model

        except Exception as e:
            logger.error(f"Error in stack_and_fit_models: {e}")
            raise e
