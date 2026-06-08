import time
import csv
from collections import defaultdict
from functools import reduce
from itertools import combinations


def timed(func):
    def wrapper(*args, **kwargs):
        t0 = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - t0:.4f}s")
        return result
    return wrapper


@timed
def load_data():
    products = {}
    with open('/home/ubuntu/project/instacart/products.csv') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            products[int(row[0])] = row[1]

    transactions = defaultdict(set)
    with open('/home/ubuntu/project/instacart/order_products__train.csv') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            transactions[int(row[0])].add(int(row[1]))

    n_orders = len(transactions)
    print(f"  Orders: {n_orders}")
    return transactions, products, n_orders


@timed
def freq_1_itemsets(transactions, products, n_orders, min_sup):
    counts = defaultdict(int)
    for items in transactions.values():
        for pid in items:
            counts[pid] += 1

    freq1 = {pid: cnt for pid, cnt in counts.items() if cnt >= min_sup}
    items = sorted(freq1.keys())
    print(f"  Frequent 1-itemsets: {len(freq1)}")
    return freq1, items


@timed
def freq_2_itemsets(transactions, freq1, products, n_orders, min_sup):
    freq1_set = set(freq1.keys())
    trans_list = list(transactions.values())

    count_pairs = lambda t: {pair: 1 for pair in combinations(sorted(t & freq1_set), 2)}
    pair_counts = reduce(lambda d, c: (d.update({k: d.get(k, 0) + v for k, v in c.items()}) or d), map(count_pairs, trans_list), defaultdict(int))
    freq2 = {pair: cnt for pair, cnt in pair_counts.items() if cnt >= min_sup}

    print(f"  Frequent 2-itemsets: {len(freq2)}")
    return freq2


@timed
def show_results(freq1, freq2, products, n_orders):
    by_sup1 = sorted(freq1.items(), key=lambda x: -x[1])[:10]
    print("\nTop 10 frequent 1-itemsets (products):")
    for pid, sup in by_sup1:
        print(f"  {products[pid]}: sup={sup}, support={sup/n_orders:.4f}")

    by_sup2 = sorted(freq2.items(), key=lambda x: -x[1])[:10]
    print("\nTop 10 frequent 2-itemsets (pairs):")
    for (p1, p2), sup in by_sup2:
        print(f"  {products[p1]}, {products[p2]}: sup={sup}, support={sup/n_orders:.4f}")


transactions, products, n_orders = load_data()
freq1, items = freq_1_itemsets(transactions, products, n_orders, min_sup=500)
freq2 = freq_2_itemsets(transactions, freq1, products, n_orders, min_sup=500)
show_results(freq1, freq2, products, n_orders)
