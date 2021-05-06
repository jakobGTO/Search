import math
import time
from fishing_game_core.game_tree import Node
from fishing_game_core.shared import ACTION_TO_STR


class minmax(object):
    def __init__(self, initial_data):
        self.transposition_table = {}
        self.depth_table = {}

    def hash_state(self, state):
        #Get hashvalues for hook position and fish position, for both players
        hash_hook = hash(frozenset(state.state.hook_positions.items()))
        hash_fish = hash(frozenset(state.state.fish_positions.items()))

        #Get one hashvalue for both state representing hashes
        hash_val = hash((hash_hook, hash_fish))

        return hash_val

    def best_move(self, state, model):
        #Start timer to control runtime
        self.timer = time.time()

        #Compute the children of the nodes
        node_children = state.compute_and_get_children()

        max_depth = 20
        deepening_factor = 2
        beta = math.inf
        alpha = -math.inf
        best_values = []
        best_moves = []

        #Loop over every child
        for child in node_children:
            best_value = -math.inf
            #Begin Iteretive Deepening Search
            for i in range(max_depth):
                res = model.alphabeta(
                    child, i+deepening_factor, alpha, beta)
                #Save current best heuristic value if past time limit
                if time.time() - self.timer > 0.06:
                    best_value = res
                #Save current heuristic value if it is better than previous
                if res > best_value:  
                    best_value = res

            best_values.append(best_value)
            best_moves.append(child.move)

        #Get index of best move according to heuristic
        best_moves_idx = best_values.index(max(best_values))

        return ACTION_TO_STR[best_moves[best_moves_idx]]

    def alphabeta(self, state, depth, alpha, beta):
        '''
            Calculate the alpha-beta pruning minmax function

            @param state() : Children
            @param depth(int): Maximum depth of algorithm
            @param alpha():
            @param beta():
        '''

        #Save the hashvalue for current state
        hash_state = self.hash_state(state)

        #If at depth 0 return heuristic for current state
        if depth == 0:
            return self.heuristic(state.state)

        #If we have already been in this state at current depth, return heuristic value for already 
        #seen state
        if hash_state in self.transposition_table and depth != self.depth_table[hash_state]:
            return self.transposition_table[hash_state]

        #If we have not been in this state already, append information about state
        #to transposition table
        self.depth_table[hash_state] = depth
        self.transposition_table[hash_state] = self.heuristic(state.state)

        maxi = state.state.player == 0
        mini = state.state.player == 1

        children = state.compute_and_get_children()

        #Apply alphabeta pruning algortihm with time condition
        if maxi:
            v = -math.inf
            for child in children:
                result = self.alphabeta(
                    child, depth-1, alpha, beta)
                v = max(v, result)
                alpha = max(alpha, result)
                if beta <= alpha:
                    break   # beta prune
                if time.time() - self.timer > 0.06:
                    break
            return v

        elif mini:
            v = math.inf
            for child in children:
                result = self.alphabeta(
                    child, depth-1, alpha, beta)
                v = min(v, result)
                beta = min(beta, result)
                if beta <= alpha:
                    break   # alpha prune
                if time.time() - self.timer > 0.06:
                    break
            return v

    def heuristic(self, state):
        player_hook = state.hook_positions
        fish_pos = state.fish_positions.items()
        is_fish_caught = state.get_caught()
        fish_score = state.fish_scores
        heur_list = [math.inf]
        
        #Loop over each fish
        for i, fish in fish_pos:
            #If fish is not caught, calculate heuristic
            if fish not in is_fish_caught:
                #Get distance from hook to current fish, normalize by current fish score
                #distance therefore yields smaller value with higher fish_score
                distance1 = ((player_hook[0][0] - fish[0])**2 +
                            (player_hook[0][1] - fish[1])**2) / fish_score[i]
                distance2 = ((player_hook[1][0] - fish[0])**2 +
                            (player_hook[1][1] - fish[1])**2) / fish_score[i]
                #If fish does not have negative value
                if fish_score[i] >= 0:
                    #Append difference of each players hook to fish normalized by fish score
                    #to list
                    heur_list.append((distance2 - distance1))
        #Return the min heuristic of the heuristic list                            
        return min(heur_list)
