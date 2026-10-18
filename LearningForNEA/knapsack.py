from itertools import combinations

import time 

items = [
    {"weight": 2, "value": 12},
    {"weight": 5, "value": 25},
    {"weight": 3, "value": 18},
    {"weight": 7, "value": 35},
    {"weight": 1, "value": 7},
    {"weight": 4, "value": 22},
    {"weight": 6, "value": 30},
    {"weight": 8, "value": 40},
    {"weight": 2, "value": 14},
    {"weight": 9, "value": 42},
    {"weight": 3, "value": 16},
    {"weight": 5, "value": 28},
    {"weight": 10, "value": 50},
    {"weight": 4, "value": 19},
    {"weight": 7, "value": 33}
]

capacity = 50

def knapsack_brute_force(items, capacity):
    n = len(items)
    best_value = 0 
    best_combination = None
    used_capacity = None 

    for r in range(n + 1):
        for combination in combinations(items, r):
            total_weight = sum(item['weight'] for item in combination)
            total_value = sum(item['value'] for item in combination)
            if total_weight <= capacity and total_value > best_value:
                best_value = total_value
                best_combination = combination
                used_capacity = total_weight

    return best_value, best_combination, total_weight, used_capacity

print(knapsack_brute_force(items,capacity))