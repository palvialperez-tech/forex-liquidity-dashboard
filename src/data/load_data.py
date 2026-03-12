import pandas as pd


def load_eurusd():

    path = "data/raw/eurusd_raw.csv"

    df = pd.read_csv(path)

    # convertir datetime
    df["datetime"] = pd.to_datetime(df["datetime"])

    # ordenar por fecha
    df = df.sort_values("datetime")

    df = df.reset_index(drop=True)

    return df