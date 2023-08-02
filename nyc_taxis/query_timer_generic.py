import random
from datetime import datetime, timedelta
from opensearchpy import OpenSearch
import time
import matplotlib.pyplot as plt

host = 'localhost'
port = 9200
auth = ('admin', 'admin')

def send_query_and_measure_time():
    start_time = time.time()

    # Assuming you have the 'expensive_1' function declared in the same file
    query = query(workload, params, **kwargs)

    # Connect to the locally running OpenSearch domain
    os = OpenSearch([{
                        'host': 'https://search-awskiran-cache20-1-a5kdfjbwk6rxqsna7cbznkserm.eu-west-1.es-staging.amazonaws.com',
                        'port': 443,
                        'use_ssl': True
                    }])

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