import random
from datetime import datetime, timedelta
from opensearchpy import OpenSearch
import time
import matplotlib.pyplot as plt

endpoint = 'https://
port = 443
auth = ('admin', 'admin')

client = OpenSearch([{'host': host, 'port': port}])

def random_date(start, end):
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds())),
    )


def expensive_1(workload, params, cache, **kwargs):
    start = datetime(2015, 1, 1)
    end = datetime(2016, 12, 31)

    pickup_gte = random_date(start, end)
    pickup_lte = random_date(pickup_gte, end)
    dropoff_gte = random_date(start, end)
    dropoff_lte = random_date(dropoff_gte, end)

    pickup_gte_str = pickup_gte.strftime("%Y-%m-%d %H:%M:%S")
    pickup_lte_str = pickup_lte.strftime("%Y-%m-%d %H:%M:%S")
    dropoff_gte_str = dropoff_gte.strftime("%Y-%m-%d %H:%M:%S")
    dropoff_lte_str = dropoff_lte.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "body": {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                    {
                        "range": {
                            "pickup_datetime": {
                                "gte": pickup_gte_str,
                                "lte": pickup_lte_str
                            }
                        }
                    },
                    {
                        "range": {
                            "dropoff_datetime": {
                                "gte": dropoff_gte_str,
                                "lte": dropoff_lte_str
                            }
                        }
                    }
                ],
                "must_not": [
                    {
                        "term": {
                            "vendor_id": "Vendor XYZ"
                        }
                    }
                ]
            }
        },
        "aggs": {
            "avg_surcharge": {
                "avg": {
                    "field": "surcharge"
                }
            },
            "sum_total_amount": {
                "sum": {
                    "field": "total_amount"
                }
            },
            "vendor_id_terms": {
                "terms": {
                    "field": "vendor_id",
                    "size": 100
                },
                "aggs": {
                    "avg_tip_per_vendor": {
                        "avg": {
                            "field": "tip_amount"
                        }
                    }
                }
            },
            "pickup_location_grid": {
                "geohash_grid": {
                    "field": "pickup_location",
                    "precision": 5
                },
                "aggs": {
                    "avg_tip_per_location": {
                        "avg": {
                            "field": "tip_amount"
                        }
                    }
                }
            }
        }
      },
        "index": 'nyc_taxis',
        "request-cache" : cache,
        "request-timeout": 60
    }

def send_query_and_measure_time():
    start_time = time.time()

    # Assuming you have the 'expensive_1' function declared in the same file
    query = expensive_1(workload, params, cache, **kwargs)

    # Connect to the locally running OpenSearch domain
    os = OpenSearch([{'host': endpoint, 'port': 443, 'use_ssl': True}])

    # Send the query to the OpenSearch domain
    response = os.search(index=query['index'], body=query['body'])

    end_time = time.time()
    response_time = end_time - start_time

    return response_time

# Number of times to execute the query and measure the response time
num_queries = 100

# List to store response times for each query
response_times = []

# Execute the query multiple times and measure the response time
for _ in range(num_queries):
    response_time = send_query_and_measure_time()
    response_times.append(response_time)

average_response_time = sum(response_times) / num_queries

# Plot the response times on a graph
plt.plot(response_times)
plt.axhline(y=average_response_time, color='r', linestyle='--', label='Average Response Time')
plt.xlabel('Query Number')
plt.ylabel('Response Time (seconds)')
plt.title('OpenSearch Query Response Time')
plt.legend()
plt.show()