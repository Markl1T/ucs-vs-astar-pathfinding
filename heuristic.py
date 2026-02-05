def manhattan_distance(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def pirate_heuristic(state, key_pos, chest_pos, goal):
    x, y, has_key, has_treasure = state
    
    if not has_key:
        # Must visit key, chest, then goal
        dist_to_key = manhattan_distance((x, y), key_pos)
        key_to_chest = manhattan_distance(key_pos, chest_pos)
        chest_to_goal = manhattan_distance(chest_pos, goal)
        return dist_to_key + key_to_chest + chest_to_goal
    
    if has_key and not has_treasure:
        # Must visit chest, then goal
        dist_to_chest = manhattan_distance((x, y), chest_pos)
        chest_to_goal = manhattan_distance(chest_pos, goal)
        return dist_to_chest + chest_to_goal
    
    if has_treasure:
        # Direct path to goal
        return manhattan_distance((x, y), goal)
    
    return 0
