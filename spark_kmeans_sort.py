import time
from pyspark.sql import SparkSession
from pyspark.ml.clustering import KMeans
from pyspark.ml.feature import VectorAssembler

spark = SparkSession.builder \
    .appName("KMeans_Sort") \
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
    df = spark.read.csv("/home/ec2-user/gas_prives.csv",
                        header=True, inferSchema=True)
    df = df.dropna()
    print(f"  Rows: {df.count()}")
    print(f"  Columns: {df.columns}")
    return df

@timed
def run_kmeans(df):
    value_col = df.columns[1]
    assembler = VectorAssembler(inputCols=[value_col], outputCol="features")
    df_vec = assembler.transform(df)
    kmeans = KMeans(k=3, seed=42, featuresCol="features", predictionCol="cluster")
    model = kmeans.fit(df_vec)
    predictions = model.transform(df_vec)
    centers = model.clusterCenters()
    print(f"  Cluster centers: {[round(c[0], 4) for c in centers]}")
    print("\nCluster summary:")
    predictions.groupBy("cluster").count().orderBy("cluster").show()
    return predictions

@timed
def sort_by_value_asc(predictions):
    value_col = predictions.columns[1]
    sorted_df = predictions.orderBy(value_col)
    print("Top 5 by value (asc):")
    sorted_df.select(predictions.columns[0], value_col, "cluster").show(5)
    return sorted_df

@timed
def sort_by_value_desc(predictions):
    value_col = predictions.columns[1]
    sorted_df = predictions.orderBy(value_col, ascending=False)
    print("Top 5 by value (desc):")
    sorted_df.select(predictions.columns[0], value_col, "cluster").show(5)
    return sorted_df

@timed
def sort_by_date(predictions):
    date_col = predictions.columns[0]
    sorted_df = predictions.orderBy(date_col)
    print("Top 5 by date:")
    sorted_df.select(date_col, predictions.columns[1], "cluster").show(5)
    return sorted_df

df = load_data()
predictions = run_kmeans(df)
sort_by_value_asc(predictions)
sort_by_value_desc(predictions)
sort_by_date(predictions)
spark.stop()
