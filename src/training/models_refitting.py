import numpy as np
from omegaconf import OmegaConf
from sklearn.utils import all_estimators

from src.training.utils import load_datasets
from src.utils import save_model_to_pickle
from utils.ml_logging import get_logger, log_function_call

# Set up logging
logger = get_logger()


class ModelReffiter:
    def __init__(self, yaml_path: str = None):
        self.model = None
        if yaml_path:
            self.load_model_from_yaml_path(yaml_path)

    def load_model_from_yaml_path(self, yaml_path: str) -> None:
        """
        Load the model configuration from a YAML file using OmegaConf and construct the model object dynamically.

        Parameters:
            yaml_path (str): The path to the YAML configuration file.
        """
        config = OmegaConf.load(yaml_path)
        self.load_model_from_config(config)

    def load_model_from_config(self, model_config) -> None:
        """
        Load the model configuration from OmegaConf and construct the model object dynamically.

        Parameters:
            model_config (DictConfig): The configuration dictionary from OmegaConf.
        """
        model_name = model_config.model_type
        hyperparameters = {}

        # Dynamically get the model class from scikit-learn
        for name, ModelClass in all_estimators(type_filter="classifier"):
            if name == model_name:
                # If the model has a base estimator (like AdaBoost), handle it
                if "base_estimator" in model_config.hyperparameters:
                    base_estimator_name = (
                        model_config.hyperparameters.base_estimator.name
                    )

                    # Dynamically get the base estimator class
                    for base_name, BaseClass in all_estimators(
                        type_filter="classifier"
                    ):
                        if base_name == base_estimator_name:
                            base_estimator_params = (
                                model_config.hyperparameters.base_estimator.parameters
                            )
                            hyperparameters["base_estimator"] = BaseClass(
                                **base_estimator_params
                            )
                            break
                    else:
                        raise ValueError(
                            f"Unsupported base estimator: {base_estimator_name}"
                        )

                # Load other hyperparameters
                for key, value in model_config.hyperparameters.items():
                    if key != "base_estimator":
                        hyperparameters[key] = value

                # Instantiate the model
                self.model = ModelClass(**hyperparameters)
                logger.info(f"Model {model_name} constructed successfully.")
                break
        else:
            raise ValueError(f"Unsupported model: {model_name}")

    @log_function_call("refit - preparing data")
    def _prepare_data_for_refit(self, features_directory: str, date: str) -> None:
        """
        Combine training and test datasets for refitting the model.

        Parameters:
            features_directory (str): Directory containing the datasets.
            date (str): Date to filter/load the datasets.

        Returns:
            None
        """
        X_train, X_test, y_train, y_test = load_datasets(
            directory=features_directory, date=date
        )
        self.X = np.vstack((X_train, X_test))
        self.y = np.concatenate((y_train, y_test))

    def refit(self, save_path, features_directory: str, date: str):
        """
        Refit the model with the combined data and save it.

        Parameters:
            save_path (str): Path where the trained model should be saved.
            features_directory (str): Directory containing the datasets.
            date (str): Date to filter/load the datasets.
        """
        self._prepare_data_for_refit(features_directory, date)

        if self.model is None:
            raise ValueError("Model is not initialized.")

        self.model.fit(self.X, self.y)
        save_model_to_pickle(self.model, save_path)
        logger.info(f"Model refitted and saved at {save_path}")
