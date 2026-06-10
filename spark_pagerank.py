import time
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("PageRank") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

def timed(func):
    def wrapper(*args, **kwargs):
        t0 = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - t0:.4f}s")
        return result
    return wrapper

@timed
def load_data():
    lines = spark.sparkContext.textFile("/home/ec2-user/web-Google.txt")
    edges = lines.filter(lambda x: not x.startswith("#")) \
                 .map(lambda x: x.strip().split("\t")) \
                 .filter(lambda x: len(x) == 2) \
                 .map(lambda x: (int(x[0]), int(x[1])))
    print(f"  Edges: {edges.count()}")
    return edges

@timed
def run_pagerank(edges, num_iterations=10, damping=0.85):
    links = edges.groupByKey().mapValues(list).cache()
    nodes = edges.flatMap(lambda x: [x[0], x[1]]).distinct()
    n = nodes.count()
    print(f"  Nodes: {n}")
    ranks = links.map(lambda x: (x[0], 1.0 / n))
    for i in range(num_iterations):
        t0 = time.time()
        contributions = links.join(ranks) \
            .flatMap(lambda x: [(dest, x[1][1] / len(x[1][0]))
                                for dest in x[1][0]])
        ranks = contributions.reduceByKey(lambda a, b: a + b) \
            .mapValues(lambda r: (1 - damping) / n + damping * r)
        print(f"  Iteration {i+1} took {time.time()-t0:.4f}s")
    return ranks, n

@timed
def show_results(ranks):
    top10 = ranks.takeOrdered(10, key=lambda x: -x[1])
    print("\nTop 10 PageRank nodes:")
    for node, rank in top10:
        print(f"  Node {node}: {rank:.6f}")

edges = load_data()
ranks, n = run_pagerank(edges, num_iterations=10)
show_results(ranks)
spark.stop()
