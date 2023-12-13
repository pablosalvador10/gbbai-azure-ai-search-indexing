from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.feature_engineering.etl import _validate_missing_data, load_data

# Sample data for testing
valid_test_data = {
    "CLIENTNUM": [1, 2, 3, 4],
    "A": [1, 2, 3, 4],
    "B": [5, 6, 7, 8],
    "C": [9, 10, 11, 12],
}

invalid_test_data = {
    "CLIENTNUM": [1, 2, 3, 4],
    "A": [1, 2, np.nan, np.nan],
    "B": [5, 6, 7, 8],
    "C": [9, 10, 11, 12],
}


def test_load_data():
    test_file = "valid_test_data.csv"
    pd.DataFrame(valid_test_data).to_csv(test_file, index=False)

    with patch(
        "src.feature_engineering.etl.validate_missing_data", autospec=True
    ) as mock_validate:
        # Call the function with the test file
        df = load_data(test_file)

        # Check that 'CLIENTNUM' column is not in the DataFrame
        assert "CLIENTNUM" not in df.columns

        # Check if the validate_missing_data function was called once with the loaded DataFrame
        mock_validate.assert_called_once_with(df, threshold=20.0)

    # Clean up: remove the temporary test file
    import os

    os.remove(test_file)


def test_validate_missing_data():
    invalid_test_df = pd.DataFrame(invalid_test_data)

    # Expect a ValueError due to high percentage of missing values in column 'A'
    with pytest.raises(
        ValueError, match=r"Columns \['A'\] have more than 20.0% missing values."
    ):
        _validate_missing_data(invalid_test_df, threshold=20.0)
