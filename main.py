import asyncio
from src.data_fetcher import DataFetcher

async def main():
    data_fetcher = DataFetcher()
    try:
        await data_fetcher.setup_connection("trades", "ESZ4")
        while True:
            await data_fetcher.fetch_data()
            await asyncio.sleep(60)
    finally:
        await data_fetcher.close_connection()
if __name__ == "__main__":
    asyncio.run(main())