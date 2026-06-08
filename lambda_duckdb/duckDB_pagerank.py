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
        CREATE TABLE web_graph AS
        SELECT * FROM read_csv(
            '/home/ubuntu/project/web-Stanford.txt',
            header = FALSE,
            columns = {'from_node': 'INTEGER', 'to_node': 'INTEGER'},
            delim = '\\t',
            comment = '#',
            ignore_errors = TRUE
        )
    """)
    count = con.execute("SELECT COUNT(*) FROM web_graph").fetchone()[0]
    print(f"  Edges: {count}")
    return count


@timed
def prepare_nodes():
    con.execute("CREATE TABLE nodes AS SELECT DISTINCT node FROM (SELECT from_node AS node FROM web_graph UNION SELECT to_node AS node FROM web_graph)")
    n_nodes = con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    print(f"  Nodes: {n_nodes}")
    con.execute("ALTER TABLE nodes ADD COLUMN rank DOUBLE DEFAULT 1.0 / {}".format(n_nodes))
    con.execute("ALTER TABLE nodes ADD COLUMN new_rank DOUBLE DEFAULT 0.0")
    return n_nodes


@timed
def compute_out_degree():
    con.execute("""
        CREATE TABLE out_degree AS
        SELECT from_node, COUNT(*) AS degree
        FROM web_graph GROUP BY from_node
    """)


@timed
def pagerank_iteration(damping, n_nodes):
    con.execute("""
        UPDATE nodes AS t SET new_rank = (
            SELECT {d} * SUM(s.rank / NULLIF(out_degree.degree, 0))
            FROM web_graph
            JOIN out_degree ON web_graph.from_node = out_degree.from_node
            JOIN nodes AS s ON web_graph.from_node = s.node
            WHERE web_graph.to_node = t.node
        ) + (1.0 - {d}) / {n}
    """.format(d=damping, n=n_nodes))
    diff = con.execute("SELECT SUM(ABS(new_rank - rank)) FROM nodes").fetchone()[0]
    con.execute("UPDATE nodes SET rank = new_rank")
    return diff if diff else 0.0


@timed
def pagerank(damping=0.85, max_iter=100, tol=1e-8):
    load_data()
    n_nodes = prepare_nodes()
    compute_out_degree()
    print(f"  Initialized {n_nodes} nodes with rank 1/{n_nodes}")
    for it in range(max_iter):
        t0 = time.time()
        diff = pagerank_iteration(damping, n_nodes)
        top5 = con.execute("SELECT node, ROUND(rank, 6) AS rank FROM nodes ORDER BY rank DESC LIMIT 5").fetchall()
        print(f"  Iter {it + 1}: diff={diff:.2e}, top={top5} ({time.time() - t0:.4f}s)")
        if diff < tol:
            print(f"  Converged after {it + 1} iterations")
            break
    return con.execute("SELECT node, rank FROM nodes ORDER BY rank DESC LIMIT 10").fetchall()


top10 = pagerank(damping=0.85, max_iter=100)
print("\nTop 10 PageRank nodes:")
for node, rank in top10:
    print(f"  Node {node}: {rank:.6f}")
