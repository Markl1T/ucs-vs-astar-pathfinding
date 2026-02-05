import heapq

class Node:
    def __init__(self, state, parent=None, cost=0, heuristic=0):
        self.state = state
        self.parent = parent
        self.cost = cost
        self.heuristic = heuristic
    
    def __lt__(self, other):
        # Priority queue comparison: f(n) = g(n) + h(n)
        return (self.cost + self.heuristic) < (other.cost + other.heuristic)


def ucs_search(problem):
    start_state = problem.get_start_state()
    start_node = Node(start_state, cost=0, heuristic=0)
    
    frontier = []
    heapq.heappush(frontier, start_node)
    
    explored = {}
    nodes_expanded = 0
    max_frontier_size = 1
    
    while frontier:
        max_frontier_size = max(max_frontier_size, len(frontier))
        
        yield {
            'status': 'running',
            'frontier_size': len(frontier),
            'expanded': nodes_expanded,
            'current_node': frontier[0],
            'explored_set': explored.copy()
        }
        
        node = heapq.heappop(frontier)
        
        if problem.is_goal(node.state):
            path = []
            curr = node
            while curr:
                path.append(curr.state)
                curr = curr.parent
            
            yield {
                'status': 'success',
                'path': list(reversed(path)),
                'cost': node.cost,
                'expanded': nodes_expanded,
                'max_frontier': max_frontier_size
            }
            return
        
        if node.state in explored and explored[node.state] <= node.cost:
            continue
        
        explored[node.state] = node.cost
        nodes_expanded += 1
        
        for next_state, action_cost in problem.get_successors(node.state):
            new_cost = node.cost + action_cost
            
            if next_state not in explored or new_cost < explored[next_state]:
                new_node = Node(next_state, parent=node, cost=new_cost, heuristic=0)
                heapq.heappush(frontier, new_node)
    
    yield {'status': 'failure', 'expanded': nodes_expanded}


def astar_search(problem):
    start_state = problem.get_start_state()
    start_h = problem.heuristic(start_state)
    start_node = Node(start_state, cost=0, heuristic=start_h)
    
    frontier = []
    heapq.heappush(frontier, start_node)
    
    explored = {} 
    nodes_expanded = 0
    max_frontier_size = 1
    
    while frontier:
        max_frontier_size = max(max_frontier_size, len(frontier))
        
        yield {
            'status': 'running',
            'frontier_size': len(frontier),
            'expanded': nodes_expanded,
            'current_node': frontier[0],
            'explored_set': explored.copy()
        }
        
        node = heapq.heappop(frontier)
        
        if problem.is_goal(node.state):
            path = []
            curr = node
            while curr:
                path.append(curr.state)
                curr = curr.parent
            
            yield {
                'status': 'success',
                'path': list(reversed(path)),
                'cost': node.cost,
                'expanded': nodes_expanded,
                'max_frontier': max_frontier_size
            }
            return
        
        if node.state in explored and explored[node.state] <= node.cost:
            continue
        
        explored[node.state] = node.cost
        nodes_expanded += 1
        
        for next_state, action_cost in problem.get_successors(node.state):
            new_cost = node.cost + action_cost
            
            if next_state not in explored or new_cost < explored[next_state]:
                h = problem.heuristic(next_state)
                new_node = Node(next_state, parent=node, cost=new_cost, heuristic=h)
                heapq.heappush(frontier, new_node)
    
    yield {'status': 'failure', 'expanded': nodes_expanded}
