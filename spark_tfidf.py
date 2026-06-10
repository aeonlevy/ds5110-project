import time
from pyspark.sql import SparkSession
from pyspark.ml.feature import Tokenizer, HashingTF, IDF, StopWordsRemover

spark = SparkSession.builder \
    .appName("TF_IDF") \
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
    df = spark.read.csv("/home/ec2-user/Amazon_Reviews.csv",
                        header=True, inferSchema=True)
    df = df.filter(df["Review Text"].isNotNull())
    df = df.select("Review Text").withColumnRenamed("Review Text", "text")
    print(f"  Reviews: {df.count()}")
    return df

@timed
def compute_tfidf(df):
    tokenizer = Tokenizer(inputCol="text", outputCol="words")
    df_words = tokenizer.transform(df)
    remover = StopWordsRemover(inputCol="words", outputCol="filtered")
    df_filtered = remover.transform(df_words)
    hashingTF = HashingTF(inputCol="filtered", outputCol="rawFeatures",
                          numFeatures=10000)
    df_tf = hashingTF.transform(df_filtered)
    idf = IDF(inputCol="rawFeatures", outputCol="features")
    idf_model = idf.fit(df_tf)
    df_tfidf = idf_model.transform(df_tf)
    print("  TF-IDF computation complete")
    print(f"  Feature vector size: 10000")
    return df_tfidf

@timed
def show_results(df_tfidf):
    print("\nSample TF-IDF results (first 5 rows):")
    df_tfidf.select("text", "features").show(5, truncate=50)

df = load_data()
df_tfidf = compute_tfidf(df)
show_results(df_tfidf)
spark.stop()
