import time
import duckdb
import random

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
        CREATE TABLE gas_prices AS
        SELECT * FROM read_csv(
            '/home/ubuntu/project/gas_prices.csv',
            header = TRUE,
            columns = {'date': 'DATE', 'value': 'FLOAT'},
            delim = ',',
            dateformat = '%m/%d/%Y',
            ignore_errors = TRUE
        )
    """)
    print(f"  Rows: {con.execute('SELECT COUNT(*) FROM gas_prices').fetchone()[0]}")


@timed
def initialize_centroids(k):
    vals = con.execute("SELECT value FROM gas_prices WHERE value IS NOT NULL").fetchall()
    vals = [v[0] for v in vals]
    centroids = random.sample(vals, k)
    return sorted(centroids)


@timed
def assign_clusters(centroids):
    sql = "SELECT date, value,"
    cases = []
    for i, c in enumerate(centroids):
        cases.append(f"ABS(value - {c})")
    sql += " LEAST(" + ", ".join(cases) + ") AS dist,"
    cases2 = []
    for i, c in enumerate(centroids):
        cases2.append(f"CASE WHEN ABS(value - {c}) = LEAST({', '.join(cases)}) THEN {i} END")
    sql += " COALESCE(" + ", ".join(cases2) + ") AS cluster"
    sql += " FROM gas_prices WHERE value IS NOT NULL"
    con.execute(f"CREATE OR REPLACE TABLE assignments AS {sql}")
    changed = con.execute("""
        SELECT COUNT(*) FROM assignments a
        JOIN gas_prices_prev_cluster p ON a.date = p.date AND a.cluster != p.cluster
    """).fetchone()[0] if con.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'gas_prices_prev_cluster'").fetchone()[0] > 0 else 0
    con.execute("CREATE OR REPLACE TABLE gas_prices_prev_cluster AS SELECT date, cluster FROM assignments")
    return changed


@timed
def update_centroids(k):
    centroids = []
    for i in range(k):
        row = con.execute(f"""
            SELECT AVG(value) FROM assignments WHERE cluster = {i}
        """).fetchone()
        centroids.append(row[0] if row[0] is not None else 0.0)
    return centroids


@timed
def kmeans(k=3, max_iter=100):
    centroids = initialize_centroids(k)
    print(f"  Initial centroids: {[round(c, 4) for c in centroids]}")
    for it in range(max_iter):
        t0 = time.time()
        changed = assign_clusters(centroids)
        new_centroids = update_centroids(k)
        print(f"  Iteration {it + 1}: centroids={[round(c, 4) for c in new_centroids]}, changed={changed} ({time.time() - t0:.4f}s)")
        if centroids == new_centroids:
            print(f"  Converged after {it + 1} iterations")
            centroids = new_centroids
            break
        centroids = new_centroids
    return centroids


load_data()
kmeans(k=3, max_iter=100)

print("\nCluster summary:")
print(con.execute("""
    SELECT cluster, COUNT(*) AS count, ROUND(MIN(value), 4) AS min_val,
           ROUND(AVG(value), 4) AS avg_val, ROUND(MAX(value), 4) AS max_val
    FROM assignments GROUP BY cluster ORDER BY cluster
""").fetchdf())

@timed
def sort_by_value_asc():
    return con.execute("SELECT date, value, cluster FROM assignments ORDER BY value").fetchdf()

@timed
def sort_by_value_desc():
    return con.execute("SELECT date, value, cluster FROM assignments ORDER BY value DESC").fetchdf()

@timed
def sort_by_date():
    return con.execute("SELECT date, value, cluster FROM assignments ORDER BY date").fetchdf()

print("\nSorting demonstrations:")
asc = sort_by_value_asc()
print(f"  Top 5 by value (asc):\n{asc.head()}")
desc = sort_by_value_desc()
print(f"  Top 5 by value (desc):\n{desc.head()}")
dat = sort_by_date()
print(f"  Top 5 by date:\n{dat.head()}")
