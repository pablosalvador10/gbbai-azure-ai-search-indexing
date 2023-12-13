import pickle
from typing import Any

from src.feature_engineering.etl import load_data
from src.feature_engineering.model_specific_transformations import (
    apply_one_hot_encoding,
    encode_categorical_features,
    log_transform_features,
    replace_values,
)
from src.utils import save_dataframe
from utils.ml_logging import get_logger

# Set up logging
logger = get_logger()

YAML_PATH = "/Users/salv91/Desktop/open-source/ml-project-template/pipelines/configs/churn_prediction/scoring.yaml"


class ModelInference:
    """
    Class for running inference with saved models.

    Attributes:
        model_name (str): The name of the model to be loaded.
        model (Any): The loaded model.
        input_data (Any): Input data for prediction.
    """

    def __init__(self, model_name: str, input_data: Any):
        """
        Initialize with the model name and input data.

        Parameters:
            model_name (str): The name of the model to be loaded.
            input_data (Any): Input data for prediction.
        """
        self.model_name = model_name
        self.input_data = input_data
        self.scoring_features = None

    def load_model_from_pickle(self, model_path: str) -> None:
        """
        Load the model from a specified file using Pickle.

        Parameters:
            model_path (str): The path to the file where the model is saved.
        """
        try:
            logger.info(f"Loading model from {model_path}.")
            with open(model_path, "rb") as file:
                self.model = pickle.load(file)  # nosec
            logger.info(f"Model loaded successfully from {model_path}.")

        except Exception as e:
            logger.error(f"Error occurred while loading model from {model_path}: {e}")
            raise e

    def prepare_input_data(self, output_path: str) -> None:
        """
        Prepare the input data for prediction.
        Implement the necessary preprocessing steps that your data requires.
        """
        try:
            logger.info("Preparing input data for prediction.")
            # Load and preprocess data
            df = load_data(self.input_data)
            transform_log_features = [
                "Credit_Limit",
                "Avg_Open_To_Buy",
                "Total_Amt_Chng_Q4_Q1",
                "Total_Trans_Amt",
                "Total_Ct_Chng_Q4_Q1",
                "Avg_Utilization_Ratio",
            ]
            df = log_transform_features(df, transform_log_features)

            transform_categorical_features = ["Gender", "Attrition_Flag"]
            df = encode_categorical_features(df, transform_categorical_features)

            transform_one_hot_encoding_features = ["Card_Category", "Marital_Status"]
            df = apply_one_hot_encoding(df, transform_one_hot_encoding_features)

            replace_struct = {
                "Attrition_Flag": {"Existing Customer": 0, "Attrited Customer": 1},
                "Education_Level": {
                    "Doctorate": 5,
                    "Post-Graduate": 4,
                    "Graduate": 3,
                    "College": 2,
                    "High School": 1,
                    "Unknown": 0,
                    "Uneducated": -1,
                },
                "Income_Category": {
                    "$120K +": 4,
                    "$80K - $120K": 3,
                    "$60K - $80K": 2,
                    "$40K - $60K": 1,
                    "Unknown": 0,
                    "Less than $40K": -1,
                },
            }
            df = replace_values(df, replace_struct)

            self.scoring_features = df

            save_dataframe(df, path=output_path)

            logger.info(
                "Input data prepared successfully and saved in location {output_path}."
            )

        except Exception as e:
            logger.error(f"Error occurred while preparing input data: {e}")
            raise e

    def run_inference(self, output_path: str) -> Any:
        """
        Run model inference on the prepared input data.

        Returns:
            The model's predictions on the input data.
        """
        try:
            if not self.model:
                logger.error("Model not loaded. Cannot run inference.")
                return None

            logger.info(f"Running inference with model {self.model_name}.")
            predictions = self.model.predict(self.scoring_features)
            save_dataframe(predictions, output_path)
            logger.info(f"Inference completed successfully and saved in {output_path}.")
            return

        except Exception as e:
            logger.error(
                f"Error occurred during inference with model {self.model_name}: {e}"
            )
            raise e
