from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import os


class EURUSDDownloader:
    def __init__(self):
        self.tv = TvDatafeed()
        self.output_path = "data/raw/eurusd_raw.csv"

    def download(self, interval=Interval.in_5_minute, bars=10000):
        df = self.tv.get_hist(
            symbol="EURUSD",
            exchange="PEPPERSTONE",
            interval=interval,
            n_bars=bars
        )

        if df is None or len(df) == 0:
            raise ValueError("tvDatafeed no devolvió datos para EURUSD.")

        df = df.reset_index()

        # Normalizar datetime si existe
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

        # Ordenar y limpiar
        if "datetime" in df.columns:
            df = df.dropna(subset=["datetime"])
            df = df.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last")

        df = df.reset_index(drop=True)

        return df

    def save(self, df):
        os.makedirs("data/raw", exist_ok=True)

        df.to_csv(self.output_path, index=False)

        print(f"Archivo guardado en {self.output_path}")

        if "datetime" in df.columns and len(df) > 0:
            print(f"Primera vela: {df['datetime'].iloc[0]}")
            print(f"Última vela: {df['datetime'].iloc[-1]}")
            print(f"Total velas: {len(df)}")

    def run(self, interval=Interval.in_5_minute, bars=50000):
        print("Descargando EURUSD desde TradingView...")
        df = self.download(interval=interval, bars=bars)
        self.save(df)
        print("Descarga finalizada correctamente.")


# ----------------------
# EJECUTAR DESCARGA
# ----------------------
if __name__ == "__main__":
    downloader = EURUSDDownloader()
    downloader.run()