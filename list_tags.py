"""
Query available tag keys and unique tag values from InfluxDB
"""

import os
from influxdb_client import InfluxDBClient

URL = "http://128.40.193.25:8086"
# Set your token here or set the INFLUXDB_TOKEN environment variable
TOKEN = os.environ.get("INFLUXDB_TOKEN", "YOUR_INFLUXDB_API_TOKEN")
ORG = "UCL-CE"
BUCKET = "ce_bms"

def get_tag_keys(client, exclude_system_tags=True):
    """Fetch all tag keys present in the bucket."""
    query_api = client.query_api()
    flux_query = f'''
    import "influxdata/influxdb/schema"
    schema.tagKeys(bucket: "{BUCKET}")
    '''
    tables = query_api.query(org=ORG, query=flux_query)
    keys = []
    for table in tables:
        for record in table.records:
            val = record.get_value()
            if exclude_system_tags and val.startswith("_"):
                continue
            keys.append(val)
    return sorted(list(set(keys)))

def get_tag_values(client, tag_name):
    """Fetch all unique values for a given tag key."""
    query_api = client.query_api()
    flux_query = f'''
    import "influxdata/influxdb/schema"
    schema.tagValues(bucket: "{BUCKET}", tag: "{tag_name}")
    '''
    tables = query_api.query(org=ORG, query=flux_query)
    values = []
    for table in tables:
        for record in table.records:
            values.append(record.get_value())
    return sorted(list(set(values)))

def main():
    if TOKEN == "YOUR_INFLUXDB_API_TOKEN":
        print("Please replace 'YOUR_INFLUXDB_API_TOKEN' with your actual InfluxDB API token or set INFLUXDB_TOKEN env var.")
        return

    with InfluxDBClient(url=URL, token=TOKEN, org=ORG) as client:
        # 1. List all available Tag Keys
        tag_keys = get_tag_keys(client)
        print("=" * 50)
        print(f"AVAILABLE TAG KEYS in '{BUCKET}' ({len(tag_keys)}):")
        print("=" * 50)
        for k in tag_keys:
            print(f" - {k}")

        # 2. List values for specific summary tags
        print("\n" + "=" * 50)
        for tag in ["room", "sensortype", "building"]:
            if tag in tag_keys:
                vals = get_tag_values(client, tag)
                print(f"Values for '{tag}' ({len(vals)} found):")
                print("  " + ", ".join(vals))
                print("-" * 50)

        # 3. List all topics
        if "opsbms-topics" in tag_keys:
            topics = get_tag_values(client, "opsbms-topics")
            print(f"\nUnique 'opsbms-topics' ({len(topics)} found):")
            for topic in topics:
                print(f" - {topic}")

if __name__ == "__main__":
    main()
