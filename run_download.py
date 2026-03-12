from src.data.download_eurusd import EURUSDDownloader
from tvDatafeed import Interval

downloader = EURUSDDownloader()

df = downloader.download(
    interval=Interval.in_5_minute,
    bars=10000
)

downloader.save(df)