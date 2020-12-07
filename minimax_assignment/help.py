from collections import defaultdict
import time, random
random.seed(2020)
from fishing_game_core.shared import ACTION_TO_STR

class MinimaxModel(object):
    def __init__(self, initial_data, space_subdivisions, use_lookups=True):
        self.get_fish_scores_and_types(initial_data)
        self.space_subdivisions = space_subdivisions

    def get_fish_scores_and_types(self, data):
        data.pop('game_over', None)
        self.fish_scores = {int(key.split('fish')[1]):value['score'] for key, value in data.items()}
        scores_to_type = {s:t for t, s in enumerate(set(self.fish_scores.values()))}
        self.fish_types = {f:scores_to_type[s] for f, s in self.fish_scores.items()}

    def next_move(self, node):
        tree_depth = 6
        max_time = 0.1
        self.start = time.time()
        self.max_time = max_time * 0.999999
        self.max_player = node.state.player
        self.max_depth = tree_depth
        children = node.compute_and_get_children()
        if len(children) == 1:
            return ACTION_TO_STR[children[0].move]
        alpha = -math.inf
        beta = math.inf
        best_value = -math.inf
        best_move = 0
        children_values = [-math.inf] * len(children)
        for i, child in enumerate(children):
            value = self.alpha_beta_prunning(child, alpha, beta, depth=tree_depth)
            children_values[i] = value
            if value > best_value:
                best_value = value
                best_move = ACTION_TO_STR[child.move]
                alpha = value
                if time.time() - self.start > self.max_time:
                    return best_move
                if best_value == math.inf:
                    return best_move

        return best_move

    def alpha_beta_prunning(self, node, alpha, beta, depth):
        if depth == self.max_depth:
            return self.compute_heuristic(node.state)
            children = node.compute_and_get_children()
            if len(children) == 0:
                return self.compute_heuristic(node.state)
            player = node.state.player
            if player == self.max_player:
                best_value = -math.inf
                best_move = 0
                for child in children:
                    value = self.alpha_beta_prunning(child, alpha, beta, depth + 1)
                    if value > best_value:
                        best_value = value
                        best_move = child.move
                        alpha = max(alpha, best_value)
                    if not best_value == math.inf:
                        if alpha >= beta:
                            break
                        if time.time() - self.start > self.max_time:
                            break

        else:
            best_value = math.inf
            best_move = 0
            for child in children:
                value = self.alpha_beta_prunning(child, alpha, beta, depth + 1)
                if value < best_value:
                    best_value = value
                    best_move = child.move
                    beta = min(beta, best_value)
                if not best_value == -math.inf:
                    if alpha >= beta:
                        break
                    if time.time() - self.start > self.max_time:
                        break

        return best_value

    def compute_heuristic(self, state, only_scores=False):
        scores = state.get_player_scores()
        hook_positions = state.get_hook_positions()
        fish_positions = state.get_fish_positions()
        caught_fish = state.get_caught()
        score_based_value = self.get_score_based_value(caught_fish, scores)
        n_fish = len(fish_positions)
        n_caught = int(caught_fish[0] != None) + int(caught_fish[1] != None)
        if n_fish == 0 or n_fish == n_caught:
            if score_based_value > 0:
                return math.inf
            if score_based_value < 0:
                return -math.inf
            return 0.0
        if only_scores:
            return score_based_value
        value_max_player = self.get_proximity_value(hook_positions, fish_positions, caught_fish, self.max_player)
        value_min_player = self.get_proximity_value(hook_positions, fish_positions, caught_fish, 1 - self.max_player)
        proximity_value = value_max_player - value_min_player
        return score_based_value + proximity_value

    def get_score_based_value(self, caught_fish, scores):
        extra_score_max = self.fish_scores[caught_fish[self.max_player]] if caught_fish[self.max_player] is not None else 0
        extra_score_min = self.fish_scores[caught_fish[(1 - self.max_player)]] if caught_fish[(1 - self.max_player)] is not None else 0
        value = 100 * (scores[self.max_player] - scores[(1 - self.max_player)] + extra_score_max - extra_score_min)
        return value

    def get_proximity_value(self, hook_positions, fish_positions, caught_fish, player):
        value = 0.0
        for fish, fish_position in fish_positions.items():
            if fish in caught_fish:
                continue
            else:
                distance_x = min(abs(fish_position[0] - hook_positions[player][0]), self.space_subdivisions - abs(fish_position[0] - hook_positions[player][0]))
                distance_y = abs(fish_position[1] - hook_positions[player][1])
                distance = distance_x + distance_y
            value += float(self.fish_scores[int(fish)]) * math.exp(-2 * distance)

        return value


class StateRepresentative(object):

    def __init__(self, explored_depth, value, best_move):
        self.explored_depth = explored_depth
        self.value = value
        self.best_move = best_move
# okay decompiling opponent.pyc