import time
from pyspark.sql import SparkSession
from pyspark.ml.fpm import FPGrowth

spark = SparkSession.builder \
    .appName("Apriori") \
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
    orders = spark.read.csv("/home/ec2-user/order_products__train.csv",
                            header=True, inferSchema=True)
    products = spark.read.csv("/home/ec2-user/products.csv",
                              header=True, inferSchema=True)
    print(f"  Order rows: {orders.count()}")
    print(f"  Products: {products.count()}")
    return orders, products

@timed
def prepare_transactions(orders, products):
    joined = orders.join(products, "product_id")
    transactions = joined.groupBy("order_id") \
        .agg({"product_name": "collect_list"}) \
        .withColumnRenamed("collect_list(product_name)", "items")
    print(f"  Transactions: {transactions.count()}")
    return transactions

@timed
def run_fpgrowth(transactions):
    fp = FPGrowth(itemsCol="items", minSupport=0.01, minConfidence=0.1)
    model = fp.fit(transactions)
    freq_items = model.freqItemsets
    print(f"  Frequent itemsets: {freq_items.count()}")
    print("\nTop 10 frequent itemsets:")
    freq_items.orderBy("freq", ascending=False).show(10, truncate=50)
    print("\nTop 10 association rules:")
    model.associationRules.orderBy("confidence", ascending=False).show(10, truncate=50)
    return model

orders, products = load_data()
transactions = prepare_transactions(orders, products)
model = run_fpgrowth(transactions)
spark.stop()
