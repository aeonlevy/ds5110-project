import time
import duckdb
import string

con = duckdb.connect()


def timed(func):
    def wrapper(*args, **kwargs):
        t0 = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - t0:.4f}s")
        return result
    return wrapper


@timed
def load_data():
    con.execute("""
        CREATE TABLE reviews AS
        SELECT ROW_NUMBER() OVER () - 1 AS doc_id, *
        FROM read_csv(
            '/home/ubuntu/project/Amazon_Reviews.csv',
            header = TRUE,
            columns = {
                'Reviewer Name': 'VARCHAR',
                'Profile Link': 'VARCHAR',
                'Country': 'VARCHAR',
                'Review Count': 'VARCHAR',
                'Review Date': 'VARCHAR',
                'Rating': 'VARCHAR',
                'Review Title': 'VARCHAR',
                'Review Text': 'VARCHAR',
                'Date of Experience': 'VARCHAR'
            },
            delim = ',',
            strict_mode = false,
            ignore_errors = TRUE,
            auto_detect = FALSE
        )
    """)
    n = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    print(f"  Reviews: {n}")
    return n


@timed
def tokenize():
    con.execute("""
        CREATE TABLE tokens AS
        SELECT doc_id, LOWER(UNNEST(STRING_SPLIT(cleaned, ' '))) AS token
        FROM (
            SELECT doc_id, REGEXP_REPLACE("Review Text", '[^a-zA-Z0-9 ]+', ' ', 'g') AS cleaned
            FROM reviews
            WHERE "Review Text" IS NOT NULL
        ) sub
        WHERE cleaned != ''
    """)
    con.execute("DELETE FROM tokens WHERE token = ''")
    t = con.execute("SELECT COUNT(*) FROM tokens").fetchone()[0]
    print(f"  Tokens: {t}")


@timed
def compute_tf():
    con.execute("""
        CREATE TABLE tf AS
        SELECT doc_id, token,
               COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY doc_id) AS tf
        FROM tokens
        GROUP BY doc_id, token
    """)
    con.execute("CREATE INDEX tf_doc ON tf(doc_id)")


@timed
def compute_idf(n_docs):
    con.execute("""
        CREATE TABLE idf AS
        SELECT token,
               LN(CAST({n} AS DOUBLE) / COUNT(DISTINCT doc_id)) AS idf
        FROM tokens
        GROUP BY token
    """.format(n=n_docs))
    con.execute("CREATE INDEX idf_token ON idf(token)")


@timed
def compute_tfidf():
    con.execute("""
        CREATE TABLE tfidf AS
        SELECT tf.doc_id, tf.token, tf.tf, idf.idf, tf.tf * idf.idf AS tfidf
        FROM tf
        JOIN idf ON tf.token = idf.token
    """)


@timed
def show_top():
    res = con.execute("""
        SELECT token, ROUND(AVG(tfidf), 6) AS avg_tfidf,
               COUNT(DISTINCT doc_id) AS doc_freq
        FROM tfidf
        GROUP BY token
        ORDER BY avg_tfidf DESC
        LIMIT 20
    """).fetchdf()
    print(res)


n_docs = load_data()
tokenize()
compute_tf()
compute_idf(n_docs)
compute_tfidf()
show_top()
