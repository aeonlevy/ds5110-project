import time
import csv
import random
from functools import reduce

dist = lambda a, b: abs(a - b)
argmin = lambda v, cs: min(range(len(cs)), key=lambda i: dist(v, cs[i]))


def timed(func):
    def wrapper(*args, **kwargs):
        t0 = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - t0:.4f}s")
        return result
    return wrapper


@timed
def load_data():
    with open('/home/ubuntu/project/gas_prices.csv') as f:
        reader = csv.reader(f)
        next(reader)
        data = [(row[0], float(row[1])) for row in reader if row[1]]
    print(f"  Rows: {len(data)}")
    return data


@timed
def initialize_centroids(data, k):
    centroids = sorted(random.sample([v for _, v in data], k))
    print(f"  Initial centroids: {[round(c, 4) for c in centroids]}")
    return centroids


@timed
def assign_clusters(data, centroids, prev):
    assign = lambda point: (point[0], point[1], argmin(point[1], centroids))
    assignments = list(map(assign, data))
    key = lambda x: x[0]
    prev_dict = dict(map(lambda x: (x[0], x), prev)) if prev else {}
    new_dict = dict(map(lambda x: (x[0], x), assignments))
    changed = sum(1 for k, v in new_dict.items()
                  if k in prev_dict and prev_dict[k][2] != v[2])
    return assignments, changed


@timed
def update_centroids(assignments, k):
    group = lambda i: list(filter(lambda x: x[2] == i, assignments))
    avg = lambda pts: round(reduce(lambda s, x: s + x[1], pts, 0.0) / max(len(pts), 1), 4)
    return [avg(group(i)) for i in range(k)]


@timed
def kmeans(data, k=3, max_iter=100):
    centroids = initialize_centroids(data, k)
    prev = []
    for it in range(max_iter):
        t0 = time.time()
        assignments, changed = assign_clusters(data, centroids, prev)
        new_centroids = update_centroids(assignments, k)
        print(f"  Iteration {it + 1}: centroids={new_centroids}, changed={changed} ({time.time() - t0:.4f}s)")
        if centroids == new_centroids:
            print(f"  Converged after {it + 1} iterations")
            centroids = new_centroids
            break
        centroids = new_centroids
        prev = assignments
    return assignments, centroids


data = load_data()
assignments, centroids = kmeans(data, k=3, max_iter=100)

print("\nCluster summary:")
for c in range(3):
    vals = [v for _, v, cl in assignments if cl == c]
    if vals:
        print(f"  Cluster {c}: count={len(vals)}, min={round(min(vals), 4)}, avg={round(sum(vals)/len(vals), 4)}, max={round(max(vals), 4)}")

@timed
def sort_by_value_asc(data):
    return sorted(data, key=lambda x: x[1])

@timed
def sort_by_value_desc(data):
    return sorted(data, key=lambda x: x[1], reverse=True)

@timed
def sort_by_date(data):
    from datetime import datetime
    return sorted(data, key=lambda x: datetime.strptime(x[0], '%m/%d/%Y'))

print("\nSorting demonstrations:")
asc = sort_by_value_asc(data)
print(f"  Top 5 by value (asc): {asc[:5]}")
desc = sort_by_value_desc(data)
print(f"  Top 5 by value (desc): {desc[:5]}")
dat = sort_by_date(data)
print(f"  Top 5 by date: {dat[:5]}")
