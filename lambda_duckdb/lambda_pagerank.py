import time
from functools import reduce


def timed(func):
    def wrapper(*args, **kwargs):
        t0 = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - t0:.4f}s")
        return result
    return wrapper


@timed
def load_data():
    edges = []
    with open('/home/ubuntu/project/web-Stanford.txt') as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) == 2:
                edges.append((int(parts[0]), int(parts[1])))
    print(f"  Edges: {len(edges)}")
    return edges


@timed
def prepare_nodes(edges):
    all_nodes = set()
    for src, dst in edges:
        all_nodes.add(src)
        all_nodes.add(dst)
    nodes = sorted(all_nodes)
    n = len(nodes)
    node_id = {node: i for i, node in enumerate(nodes)}
    print(f"  Nodes: {n}")
    return nodes, node_id, n


@timed
def build_out_degree(edges):
    return reduce(lambda d, e: (d.update({e[0]: d.get(e[0], 0) + 1}) or d), edges, {})


@timed
def build_incoming(edges):
    incoming = {}
    for src, dst in edges:
        incoming.setdefault(dst, []).append(src)
    return incoming


@timed
def pagerank_iteration(ranks, incoming, out_degree, damping, n):
    new_ranks = {}
    dangling_sum = 0.0
    for node in range(n):
        if out_degree.get(node, 0) == 0:
            dangling_sum += ranks[node]
    damping_dangling = damping * dangling_sum / n
    for node in range(n):
        in_sum = 0.0
        if node in incoming:
            for src in incoming[node]:
                in_sum += ranks[src] / out_degree.get(src, 1)
        new_ranks[node] = (1.0 - damping) / n + damping * in_sum + damping_dangling
    diff = sum(abs(new_ranks[n] - ranks[n]) for n in ranks)
    return new_ranks, diff


@timed
def pagerank(edges, damping=0.85, max_iter=100, tol=1e-8):
    nodes, node_id, n = prepare_nodes(edges)
    edges_by_id = [(node_id[s], node_id[d]) for s, d in edges]
    out_degree = build_out_degree(edges_by_id)
    incoming = build_incoming(edges_by_id)
    rank = {i: 1.0 / n for i in range(n)}
    print(f"  Initialized {n} nodes with rank 1/{n}")
    for it in range(max_iter):
        t0 = time.time()
        rank, diff = pagerank_iteration(rank, incoming, out_degree, damping, n)
        top5 = sorted([(nodes[i], rank[i]) for i in range(n)], key=lambda x: -x[1])[:5]
        print(f"  Iter {it + 1}: diff={diff:.2e}, top={[(n, round(r, 6)) for n, r in top5]} ({time.time() - t0:.4f}s)")
        if diff < tol:
            print(f"  Converged after {it + 1} iterations")
            break
    return [(nodes[i], rank[i]) for i in sorted(rank, key=lambda x: -rank[x])[:10]]


edges = load_data()
top10 = pagerank(edges, damping=0.85, max_iter=100)
print("\nTop 10 PageRank nodes:")
for node, rank in top10:
    print(f"  Node {node}: {rank:.6f}")
