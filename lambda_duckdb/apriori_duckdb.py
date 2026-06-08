import time
import duckdb

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
        CREATE TABLE order_products AS
        SELECT * FROM read_csv(
            '/home/ubuntu/project/instacart/order_products__train.csv',
            header = TRUE,
            columns = {'order_id': 'INTEGER', 'product_id': 'INTEGER',
                       'add_to_cart_order': 'INTEGER', 'reordered': 'INTEGER'},
            delim = ','
        )
    """)
    con.execute("""
        CREATE TABLE products AS
        SELECT * FROM read_csv(
            '/home/ubuntu/project/instacart/products.csv',
            header = TRUE,
            columns = {'product_id': 'INTEGER', 'product_name': 'VARCHAR',
                       'aisle_id': 'INTEGER', 'department_id': 'INTEGER'},
            delim = ','
        )
    """)
    n_orders = con.execute("SELECT COUNT(DISTINCT order_id) FROM order_products").fetchone()[0]
    n_rows = con.execute("SELECT COUNT(*) FROM order_products").fetchone()[0]
    print(f"  Orders: {n_orders}, Rows: {n_rows}")
    return n_orders


@timed
def freq_1_itemsets(n_orders, min_sup):
    con.execute(f"""
        CREATE TABLE freq1 AS
        SELECT op.product_id, p.product_name,
               COUNT(DISTINCT op.order_id) AS sup,
               CAST(COUNT(DISTINCT op.order_id) AS DOUBLE) / {n_orders} AS support
        FROM order_products op
        JOIN products p ON op.product_id = p.product_id
        GROUP BY op.product_id, p.product_name
        HAVING COUNT(DISTINCT op.order_id) >= {min_sup}
    """)
    k = con.execute("SELECT COUNT(*) FROM freq1").fetchone()[0]
    print(f"  Frequent 1-itemsets: {k}")
    return k


@timed
def freq_2_itemsets(n_orders, min_sup):
    con.execute(f"""
        CREATE TABLE freq2 AS
        SELECT a.product_id AS p1, b.product_id AS p2,
               pa.product_name AS name1, pb.product_name AS name2,
               COUNT(DISTINCT a.order_id) AS sup,
               CAST(COUNT(DISTINCT a.order_id) AS DOUBLE) / {n_orders} AS support
        FROM order_products a
        JOIN order_products b ON a.order_id = b.order_id AND a.product_id < b.product_id
        JOIN products pa ON a.product_id = pa.product_id
        JOIN products pb ON b.product_id = pb.product_id
        GROUP BY a.product_id, b.product_id, pa.product_name, pb.product_name
        HAVING COUNT(DISTINCT a.order_id) >= {min_sup}
    """)
    k = con.execute("SELECT COUNT(*) FROM freq2").fetchone()[0]
    print(f"  Frequent 2-itemsets: {k}")
    return k


@timed
def show_results():
    print("\nTop 10 frequent 1-itemsets (products):")
    res = con.execute("""
        SELECT product_name, sup, ROUND(support, 4) AS support
        FROM freq1 ORDER BY support DESC LIMIT 10
    """).fetchall()
    for r in res:
        print(f"  {r[0]}: sup={r[1]}, support={r[2]}")

    print("\nTop 10 frequent 2-itemsets (pairs):")
    res = con.execute("""
        SELECT name1, name2, sup, ROUND(support, 4) AS support
        FROM freq2 ORDER BY support DESC LIMIT 10
    """).fetchall()
    for r in res:
        print(f"  {r[0]}, {r[1]}: sup={r[2]}, support={r[3]}")


n_orders = load_data()
freq_1_itemsets(n_orders, min_sup=500)
freq_2_itemsets(n_orders, min_sup=500)
show_results()
