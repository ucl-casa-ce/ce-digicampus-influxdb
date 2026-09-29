"""
InfluxDB 2.x Connection and Query Example for UCL-CE BMS Data
"""

import os
import warnings
from influxdb_client import InfluxDBClient
from influxdb_client.client.warnings import MissingPivotFunction
import pandas as pd

# Suppress pivot warning for raw table reads
warnings.simplefilter("ignore", MissingPivotFunction)

# Connection parameters
URL = "http://128.40.193.25:8086"
# Set your token here or set the INFLUXDB_TOKEN environment variable
TOKEN = os.environ.get("INFLUXDB_TOKEN", "YOUR_INFLUXDB_API_TOKEN")
ORG = "UCL-CE"
BUCKET = "ce_bms"

def main():
    if TOKEN == "YOUR_INFLUXDB_API_TOKEN":
        print("Please replace 'YOUR_INFLUXDB_API_TOKEN' with your actual InfluxDB API token or set INFLUXDB_TOKEN env var.")
        return

    print(f"Connecting to InfluxDB at {URL} (Org: {ORG})...")
    
    with InfluxDBClient(url=URL, token=TOKEN, org=ORG) as client:
        # 1. Health check / Ping
        ready = client.ping()
        print(f"Server reachable: {ready}")

        # 2. List accessible buckets
        try:
            buckets_api = client.buckets_api()
            buckets = buckets_api.find_buckets().buckets
            print("\nAccessible buckets:")
            for b in buckets:
                print(f" - {b.name}")
        except Exception as e:
            print(f"\nCould not list buckets: {e}")

        # 3. Example Flux Query
        query_api = client.query_api()
        
        flux_query = f'''
        from(bucket: "{BUCKET}")
          |> range(start: -30d)
          |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
          |> limit(n: 5)
        '''

        print(f"\nExecuting query on bucket '{BUCKET}'...")
        try:
            # Query and convert directly to a Pandas DataFrame
            df = query_api.query_data_frame(org=ORG, query=flux_query)
            
            if isinstance(df, list):
                df = pd.concat(df) if df else pd.DataFrame()

            if not df.empty:
                print(f"\nResults preview (found {len(df)} rows):")
                cols_to_show = [c for c in ['_time', '_measurement', '_field', '_value', 'topic'] if c in df.columns]
                if cols_to_show:
                    print(df[cols_to_show].head())
                else:
                    print(df.head())
            else:
                print("Query returned no data (check bucket name, measurement name, or time range).")
                
        except Exception as e:
            print(f"Query error: {e}")

if __name__ == "__main__":
    main()
