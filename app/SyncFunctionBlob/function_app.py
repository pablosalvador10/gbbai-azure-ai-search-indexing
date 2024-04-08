import logging

import azure.functions as func
import pandas as pd

app = func.FunctionApp()


@app.blob_trigger(
    arg_name="myblob",
    path="testretrieval/Reviews_text.csv",
    connection="testeastusdev001_STORAGE",
)
def blob_sync(myblob: func.InputStream):
    logging.info(
        f"Python blob trigger function processed blob\n" f"Name: {myblob.name}\n"
    )

    # Load the CSV data into a pandas DataFrame
    df = pd.read_csv(myblob)

    # Print and log various statistics
    logging.info(f"Number of rows: {len(df)}")
    logging.info(f"Number of columns: {len(df.columns)}")
    logging.info(f"Column names: {df.columns.tolist()}")
    logging.info(f"Data types:\n{df.dtypes}")

    # Print and log descriptive statistics for each column
    for col in df.columns:
        logging.info(f"Statistics for column {col}:\n{df[col].describe()}")

    # Print and log the first 5 rows of the DataFrame
    logging.info(f"First 5 rows:\n{df.head()}")
