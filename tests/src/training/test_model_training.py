import pandas as pd
import pytest

from src.training.models_training import ModelTrainer


# Sample data for testing
@pytest.fixture
def mock_df():
    return pd.DataFrame(
        {
            "feature_1": [1, 2, 3, 4, 5, 6, 7, 8],
            "feature_2": [2, 3, 4, 5, 6, 7, 8, 9],
            "target": [1, 0, 0, 1, 0, 1, 1, 0],
        }
    )


@pytest.fixture
def trainer(mock_df):
    trainer_instance = ModelTrainer(features_path=None, estimator=None)
    trainer_instance.df = mock_df
    return trainer_instance


def test_split_data(trainer):
    X_train, X_test, y_train, y_test = trainer.split_data(target_column="target")

    # Check that data is split into training and testing sets
    assert len(X_train) > 0
    assert len(X_test) > 0
    assert len(y_train) > 0
    assert len(y_test) > 0

    # Check that the number of rows match for X and y
    assert len(X_train) == len(y_train)
    assert len(X_test) == len(y_test)


def test_perform_upsampling(trainer):
    X_res, y_res = trainer.perform_upsampling(target_column="target")

    # Check that the number of rows match for X and y
    assert len(X_res) == len(y_res)

    # Validate upsampling. After upsampling, number of 1s and 0s should be equal
    assert sum(y_res == 1) == sum(y_res == 0)
