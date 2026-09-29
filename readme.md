# InfluxDB Connection & Query Guide

## Connection Details

- **Host URL:** `http://128.40.193.25:8086`
- **Organization (`org`):** `UCL-CE`
- **API Token:** `<YOUR_INFLUXDB_API_TOKEN>`
- **Buckets:**
  - `ce_bms` (Main BMS time-series data)
  - `ce_bms_as`

---

## Schema & Tags

Data points in `ce_bms` (under measurement `mqtt_consumer`) are tagged with the following keys:

| Tag Key | Description | Example Values |
|---|---|---|
| `room` | Room identifier / number | `107`, `203`, `317`, `001` |
| `building` | Building code | `OPSEBO` (One Pool Street) |
| `sensortype` | Metric / sensor type | `TPS` (Temperature), `CDS` (CO2), `HMS` (Humidity), `LMS` (Light/Lux), `AVFS` (Air Flow), `FCV` (Valve) |
| `opsbms-topics` | Full MQTT topic path | `UCL/OPSEBO/107/Room/CDS/Value` |
| `location` | Sensor location description | `OPSEBO` |
| `org` | Organization tag | `ce-data` |
| `host` | Ingest host identifier | `OPSEBO` |

### Available Rooms (30 total)

```
000, 001, 004, 007, 009, 012, 013, 015, 016, 018, 019, 020, 0C1,
101, 102, 104, 105, 106, 107, 109, 110, 111, 119, 1C2,
201, 203, 206, 301, 313, 317
```

---

## Python Usage

### 1. Installation

```bash
pip install influxdb-client pandas
```

### 2. Setting API Token

You can either export it in your environment:

```bash
export INFLUXDB_TOKEN="<YOUR_INFLUXDB_API_TOKEN>"
```

or replace `"YOUR_INFLUXDB_API_TOKEN"` directly inside the Python scripts.

### 3. Querying Data (`query_influx.py`)

```python
import os
from influxdb_client import InfluxDBClient
import pandas as pd

URL = "http://128.40.193.25:8086"
TOKEN = os.environ.get("INFLUXDB_TOKEN", "YOUR_INFLUXDB_API_TOKEN")
ORG = "UCL-CE"
BUCKET = "ce_bms"

with InfluxDBClient(url=URL, token=TOKEN, org=ORG) as client:
    query_api = client.query_api()

    # Query temperature in Room 107 over the last 24 hours
    flux_query = f'''
    from(bucket: "{BUCKET}")
      |> range(start: -24h)
      |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
      |> filter(fn: (r) => r["room"] == "107")
      |> filter(fn: (r) => r["sensortype"] == "TPS")
      |> limit(n: 50)
    '''

    df = query_api.query_data_frame(org=ORG, query=flux_query)
    if isinstance(df, list):
        df = pd.concat(df)

    print(df[["_time", "room", "sensortype", "_value"]].head())
```

### 4. Listing Unique Tags / Rooms (`list_tags.py`)

```python
import os
from influxdb_client import InfluxDBClient

URL = "http://128.40.193.25:8086"
TOKEN = os.environ.get("INFLUXDB_TOKEN", "YOUR_INFLUXDB_API_TOKEN")
ORG = "UCL-CE"
BUCKET = "ce_bms"

with InfluxDBClient(url=URL, token=TOKEN, org=ORG) as client:
    query_api = client.query_api()
    
    # Query all unique room tags
    flux_query = f'''
    import "influxdata/influxdb/schema"
    schema.tagValues(bucket: "{BUCKET}", tag: "room")
    '''
    
    tables = query_api.query(org=ORG, query=flux_query)
    rooms = [record.get_value() for table in tables for record in table.records]
    print("Rooms:", sorted(rooms))
```

---

## Flux Queries & Terminal (cURL) Examples

### Query Unique Topics Matching `UCL/OPSEBO/...`

```bash
curl --request POST "http://128.40.193.25:8086/api/v2/query?org=UCL-CE" \
  --header "Authorization: Token <YOUR_INFLUXDB_API_TOKEN>" \
  --header "Accept: application/csv" \
  --header "Content-type: application/vnd.flux" \
  --data '
import "influxdata/influxdb/schema"
schema.tagValues(
  bucket: "ce_bms",
  tag: "opsbms-topics",
  predicate: (r) => r["opsbms-topics"] =~ /^UCL\/OPSEBO/
)'
```

### Query Sensor Readings by Room and Metric

```bash
curl --request POST "http://128.40.193.25:8086/api/v2/query?org=UCL-CE" \
  --header "Authorization: Token <YOUR_INFLUXDB_API_TOKEN>" \
  --header "Accept: application/csv" \
  --header "Content-type: application/vnd.flux" \
  --data '
from(bucket: "ce_bms")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
  |> filter(fn: (r) => r["room"] == "107")
  |> filter(fn: (r) => r["sensortype"] == "TPS")
  |> limit(n: 10)'
```