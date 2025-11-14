# file: data_extract_load/load_csv_data.py

import dlt
import pandas as pd
import os

# path to folder where your raw CSV files are stored
RAW_DATA_PATH = os.path.join(os.path.dirname(__file__), "../raw_data")


@dlt.resource(name="raw_data", write_disposition="replace")
def csv_resource():
    # list all CSV files in raw_data folder
    csv_files = [f for f in os.listdir(RAW_DATA_PATH) if f.endswith(".csv")]

    for file in csv_files:
        path = os.path.join(RAW_DATA_PATH, file)

        # read CSV with tolerant settings
        df = pd.read_csv(path, on_bad_lines="skip", engine="python")

        # normalize schema: convert all columns to string
        df = df.astype(str)

        # add filename for traceability
        df["source_file"] = file

        yield df


def run_pipeline():
    # initialize DLT pipeline
    pipeline = dlt.pipeline(
        pipeline_name="csv_ingestion_pipeline",
        destination="duckdb",
        dataset_name="staging_data",
        dev_mode=True,
    )

    # run pipeline with our CSV resource
    load_info = pipeline.run(csv_resource())
    print(load_info)


if __name__ == "__main__":
    run_pipeline()
    print("CSV data loaded successfully via DLT.")
