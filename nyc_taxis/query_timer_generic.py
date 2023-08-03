import argparse
import random
import time
import requests
from datetime import datetime
from opensearchpy import OpenSearch
import matplotlib.pyplot as plt
import numpy as np

# Define a function to generate random data
def random_date(start, end):
    delta = end - start
    return start + delta * random.random()

# Expensive query to be used
def expensive_1(cache, **kwargs):
    start = datetime(2015, 1, 1)
    end = datetime(2015, 1, 1)

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
                                "gte": '2015-01-01 00:00:00',
                                "lte": '2015-01-03 00:00:00'
                            }
                        }
                    },
                    {
                        "range": {
                            "dropoff_datetime": {
                                "gte": '2015-01-01 00:00:00',
                                "lte": '2015-01-03 00:00:00'
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

# Function to send the query and measure the response time
def send_query_and_measure_time(hit_count, endpoint, username, password):

    # start_time = time.time()

    # Assuming you have the 'expensive_1' function declared in the same file
    query = expensive_1(True)

    # Connect to the OpenSearch domain using the provided endpoint and credentials
    os = OpenSearch(
        [endpoint],
        http_auth=(username, password),
        port=443,
        use_ssl=True,
    )

    # Send the query to the OpenSearch domain
    response = os.search(index=query['index'], body=query['body'], request_timeout=60, request_cache=True)
    took_time = response['took']

    # end_time = time.time()
    # response_time = end_time - start_time
    return took_time

def get_request_cache_stats(endpoint, username, password):
    url = f"{endpoint}/_nodes/stats/indices/request_cache"
    response = requests.get(url, auth=(username, password))

    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve request cache stats.")
        return None

def main():
    parser = argparse.ArgumentParser(description='OpenSearch Query Response Time Plotter')
    parser.add_argument('endpoint', help='OpenSearch domain endpoint (https://example.com)')
    parser.add_argument('username', help='Username for authentication')
    parser.add_argument('password', help='Password for authentication')
    args = parser.parse_args()

    url = f"{args.endpoint}/nyc_taxis/_cache/clear"
    response = requests.post(url, auth=(args.username, args.password))

    if response.status_code == 200:
        print("Request cache cleared successfully." + str(response))
    else:
        print("Failed to clear request cache." + str(response.status_code))

    data = get_request_cache_stats(args.endpoint, args.username, args.password)
    hit_count = data['nodes']['AdFlYDT8Q_GdaU04lXyB5A']['indices']['request_cache']['hit_count']

    # Number of times to execute the query and measure the response time
    num_queries = 50

    # List to store response times for each query
    response_times = []

    # Execute the query multiple times and measure the response time
    for x in range(1, num_queries + 1):
        response_time = send_query_and_measure_time(hit_count, args.endpoint, args.username, args.password)
        new_hits = get_request_cache_stats(args.endpoint, args.username, args.password)['nodes']['AdFlYDT8Q_GdaU04lXyB5A']['indices']['request_cache']['hit_count']
        
        if new_hits > hit_count:
            print(f"Hit. Took time: {response_time}")
            hit_count = new_hits
            isHit = True
        else:
            print(f"Miss. Took time: {response_time}")
            isHit = False

        # Append a tuple with response time and hit/miss status
        response_times.append((response_time, isHit))
        print(f"Response {x} received.")

    # Separate response times and hit/miss indicators for plotting
    hit_miss_colors = ['g' if isHit else 'r' for _, isHit in response_times]

    # Calculate the average response time
    response_times_only = [response[0] for response in response_times]
    average_response_time = sum(response_times_only[1:]) / (num_queries - 1)

    p99_latency = np.percentile(response_times_only[1:], 99)

    # Plot the response times on a graph
    plt.scatter(range(1, num_queries + 1), response_times_only, c=hit_miss_colors, label='Response Times')
    plt.axhline(y=average_response_time, color='r', linestyle='--', label='Average Response Time')

    # Find indices of highest hit and miss
    highest_hit_index = max([i for i, (_, isHit) in enumerate(response_times) if isHit])
    highest_miss_index = max([i for i, (_, isHit) in enumerate(response_times) if not isHit])

    # Draw lines at the highest hit and miss points
    plt.axvline(x=highest_hit_index + 1, color='g', linestyle=':', label='Highest Hit')
    plt.axvline(x=highest_miss_index + 1, color='r', linestyle=':', label='Highest Miss')

    plt.yscale('log')  # Set log scale on y-axis

    # Set x-axis ticks to prevent overlap
    step = max(1, num_queries // 10)  # Display every 10th tick label
    plt.xticks(range(1, num_queries + 1, step), rotation=45)

    # Add a text annotation for the average and p99 response times
    plt.text(num_queries + 0.5, average_response_time, f'Avg: {average_response_time:.2f} ms', color='r', va='center')
    # Add a text annotation for the p99 response time at the bottom right
    plt.text(num_queries + 0.5, p99_latency, f'p99: {p99_latency:.2f} ms', color='b', va='bottom')

    plt.tight_layout()  # Ensure labels and annotations fit within the figure

    plt.xlabel('Query Number')
    plt.ylabel('Response Time (milliseconds)')
    plt.title('OpenSearch Query Response Time')
    plt.legend()

    plt.tight_layout()  # Ensure labels and annotations fit within the figure

    plt.show()

if __name__ == '__main__':
    main()