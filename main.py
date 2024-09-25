import asyncio
from data_fetcher import DataFetcher

async def main():
    data_fetcher = DataFetcher()
    try:
        await data_fetcher.setup_connection()
        while True:
            await data_fetcher.fetch_data()
            await asyncio.sleep(180)
    finally:
        await data_fetcher.close_connection()
if __name__ == "__main__":
    asyncio.run(main())