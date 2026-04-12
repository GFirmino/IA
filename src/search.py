from __future__ import annotations
import heapq
from src.data import heuristic, neighbors
from src.models import FrontierNode

def _result(algorithm, path, cost, iterations, expanded_nodes, success):
    return {'algorithm': algorithm, 'path': path, 'cost': cost, 'iterations': iterations, 'expanded_nodes': expanded_nodes, 'success': success}

# Pesquisa de custo uniforme
def uniform_cost_search(start, goal):
    frontier = [(0, FrontierNode(priority=0, city=start, path=[start], cost=0, depth=0))]
    best_cost = {start: 0}
    iterations = []
    expanded = 0
    while frontier:
        _, current = heapq.heappop(frontier)
        expanded += 1
        iterations.append({'expanded_city': current.city, 'path': current.path, 'g': current.cost, 'frontier_size_after_pop': len(frontier)})
        if current.city == goal:
            return _result('ucs', current.path, current.cost, iterations, expanded, True)
        if current.cost > best_cost.get(current.city, float('inf')):
            continue
        for nxt, distance in neighbors(current.city):
            new_cost = current.cost + distance
            if new_cost < best_cost.get(nxt, float('inf')):
                best_cost[nxt] = new_cost
                node = FrontierNode(priority=new_cost, city=nxt, path=current.path + [nxt], cost=new_cost, depth=current.depth + 1)
                heapq.heappush(frontier, (node.priority, node))
    return _result('ucs', [], float('inf'), iterations, expanded, False)

# Pesquisa por profundidade limitada
def depth_limited_search(start, goal, depth_limit=10):
    stack = [FrontierNode(priority=0, city=start, path=[start], cost=0, depth=0)]
    iterations = []
    expanded = 0
    while stack:
        current = stack.pop()
        expanded += 1
        iterations.append({'expanded_city': current.city, 'path': current.path, 'g': current.cost, 'depth': current.depth, 'stack_size_after_pop': len(stack)})
        if current.city == goal:
            return _result('dls', current.path, current.cost, iterations, expanded, True)
        if current.depth >= depth_limit:
            continue
        for nxt, distance in reversed(neighbors(current.city)):
            if nxt not in current.path:
                stack.append(FrontierNode(priority=0, city=nxt, path=current.path + [nxt], cost=current.cost + distance, depth=current.depth + 1))
    return _result('dls', [], float('inf'), iterations, expanded, False)

# Pesquisa Sófrega
def greedy_search(start, goal):
    frontier = [(heuristic(start, goal), FrontierNode(priority=heuristic(start, goal), city=start, path=[start], cost=0, depth=0))]
    visited = set()
    iterations = []
    expanded = 0
    while frontier:
        _, current = heapq.heappop(frontier)
        if current.city in visited:
            continue
        visited.add(current.city)
        expanded += 1
        iterations.append({'expanded_city': current.city, 'path': current.path, 'g': current.cost, 'h': heuristic(current.city, goal), 'frontier_size_after_pop': len(frontier)})
        if current.city == goal:
            return _result('greedy', current.path, current.cost, iterations, expanded, True)
        for nxt, distance in neighbors(current.city):
            if nxt not in visited:
                h = heuristic(nxt, goal)
                heapq.heappush(frontier, (h, FrontierNode(priority=h, city=nxt, path=current.path + [nxt], cost=current.cost + distance, depth=current.depth + 1)))
    return _result('greedy', [], float('inf'), iterations, expanded, False)

#Pesquisa A*
def astar_search(start, goal):
    start_h = heuristic(start, goal)
    frontier = [(start_h, FrontierNode(priority=start_h, city=start, path=[start], cost=0, depth=0))]
    best_cost = {start: 0}
    iterations = []
    expanded = 0
    while frontier:
        _, current = heapq.heappop(frontier)
        expanded += 1
        current_h = heuristic(current.city, goal)
        iterations.append({'expanded_city': current.city, 'path': current.path, 'g': current.cost, 'h': current_h, 'f': current.cost + current_h, 'frontier_size_after_pop': len(frontier)})
        if current.city == goal:
            return _result('astar', current.path, current.cost, iterations, expanded, True)
        if current.cost > best_cost.get(current.city, float('inf')):
            continue
        for nxt, distance in neighbors(current.city):
            new_cost = current.cost + distance
            if new_cost < best_cost.get(nxt, float('inf')):
                best_cost[nxt] = new_cost
                h = heuristic(nxt, goal)
                f = new_cost + h
                heapq.heappush(frontier, (f, FrontierNode(priority=f, city=nxt, path=current.path + [nxt], cost=new_cost, depth=current.depth + 1)))
    return _result('astar', [], float('inf'), iterations, expanded, False)

def run_algorithm(name, start, goal, depth_limit=10):
    mapping = {
        'ucs': lambda: uniform_cost_search(start, goal),
        'dls': lambda: depth_limited_search(start, goal, depth_limit),
        'greedy': lambda: greedy_search(start, goal),
        'astar': lambda: astar_search(start, goal),
    }
    return mapping[name]()

def run_all_algorithms(start, goal, depth_limit=10):
    return {name: run_algorithm(name, start, goal, depth_limit=depth_limit) for name in ['ucs', 'dls', 'greedy', 'astar']}
