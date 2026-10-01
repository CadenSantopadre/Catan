import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import RegularPolygon
plt.ion()

STRATS = ["heuristic", "heuristic", "heuristic-trade-adaptive", "heuristic-trade-adaptive"]

DICE_PROBABILITY = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}
SETTLEMENT_URGENCY = 1.5 #How urgent it is to construct a settlement
ORE_CITY_URGENCY = 2.0
WHEAT_CITY_URGENCY = 1.0
OVER_URGENCY = 0.5
RANDOM_TRADE_BORDER = 0.5
ENDGAME_TRADE_SUB = 2.0
WINNING_TRADE_SUB = 0.5


@dataclass
class Vertex: #Vertexes are intersections between hexes
    #Coord is a tuple of hte 3 hex positions meeting at the corner
    coordinate: Tuple[Tuple[int,int,int], Tuple[int,int,int], Tuple[int,int,int]]
    building_type: Optional[str] = None    # None, "Settlement", or "City"
    owner_id: Optional[int] = None         # 0,1,2, etc.

@dataclass
class Edge: #Edges are the connectors between vertices
    coordinate: Tuple[Tuple, Tuple]            # Connects two vertex coordinate strings
    owner_id: Optional[int] = None         # Player ID for roads

@dataclass
class HexTile: #HexTiles are what everyting is against
    coordinate: Tuple[int, int, int]       # Cube coords (q, r, s)
    #https://backdrifting.net/postImages/hex_matplotlib_cube.png
    resource: str                          # "wood", "brick", etc.
    number_token: int
    vertices: List[Tuple] = field(default_factory=list) # Keys to vertices map

class CatanBoard:
    def __init__(self):#This is like a constructor... 
        self.hexes: Dict[Tuple[int, int, int], HexTile] = {} #Maps a coord tuple to it's hextile
        self.vertices: Dict[Tuple, Vertex] = {}#Set of 3 tuples to  vertex
        self.edges: Dict[Tuple[str, str], Edge] = {} #name of vertex connecting to  edge
        self.roll_index: Dict[int, List[HexTile]] = {i: [] for i in range(2, 13)} #Sets 2,12... end is exclusive

    def get_vertex_keys_for_hex(self, q: int, r: int, s: int) -> List[Tuple]:
        center = (q,r,s)

        neighbors = [
            (q + 1, r - 1, s),     # Top Right
            (q + 1, r, s - 1),     # Right
            (q, r + 1, s - 1),     # Bottom Right
            (q - 1, r + 1, s),     # Bottom Left
            (q - 1, r, s + 1),     # Left
            (q, r - 1, s + 1)      # Top Left
        ]

        vertex_keys = []

        for i in range(6):
            n1 = neighbors[i]
            n2 = neighbors[(i+1) % 6]
            #No matter which hex generates the corner, the tuple key will be identical
            sorted_vertex_key = tuple(sorted([center, n1, n2]))
            vertex_keys.append(sorted_vertex_key)

        return vertex_keys


    def register_hex(self, q:int,r:int,s:int, resource:str, token:int):
        hex_coord = (q,r,s)

        vertex_keys = self.get_vertex_keys_for_hex(q,r,s)
        for v_key in vertex_keys:
            if v_key not in self.vertices:
                #If corner is NEW, create it
                self.vertices[v_key] = Vertex(coordinate=v_key)

        for i in range(6):
            v1 = vertex_keys[i]
            v2 = vertex_keys[(i+1) % 6]

            edge_key = tuple(sorted([v1,v2]))
            if edge_key not in self.edges:
                self.edges[edge_key] = Edge(coordinate=edge_key)

        new_hex = HexTile(
            coordinate=hex_coord,
            resource=resource,
            number_token=token,
            vertices=vertex_keys
        )
        self.hexes[hex_coord] = new_hex
        if token in self.roll_index:
            self.roll_index[token].append(new_hex)

    def get_numbers_for_vertex(self, vertex_coords: Tuple) -> List[int]:
        numbers = []
        
        # vertex_coords is literally a tuple containing the 3 surrounding hex centers
        for hex_coord in vertex_coords:
            # Check if the hex exists in our board dictionary (handles outer edges/water)
            if hex_coord in self.hexes:
                hex_tile = self.hexes[hex_coord]
                
                # Make sure it's a valid resource tile with a number (skips Desert/None)
                if hex_tile.number_token is not None and hex_tile.number_token > 0:
                    numbers.append(hex_tile.number_token)
                    
        return numbers



def get_vertex_xy(vertex_key, size=1.0):
    #Gives the x y value of a vertex
    h_dist = size * np.sqrt(3)
    v_dist = size * 1.5
    xs, ys = [], []
    for (q, r, s) in vertex_key:
        xs.append(h_dist * (q + r / 2.0))
        ys.append(v_dist * r)
    return np.mean(xs), np.mean(ys)



engine = CatanBoard()
terrain = ["Wood",
           "Wood",
           "Wood",
           "Wood",
           "Wheat",
           "Wheat",
           "Wheat",
           "Wheat",
           "Wool",
           "Wool",
           "Wool",
           "Wool",
           "Brick",
           "Brick",
           "Brick",
           "Ore",
           "Ore",
           "Ore",
           "Desert"
           ]
tokens = [
    2,
    3,
    3,
    4,
    4,
    5,
    5,
    6,
    6,
    8,
    8,
    9,
    9,
    10,
    10,
    11,
    11,
    12]
random.shuffle(terrain)
random.shuffle(tokens)
for q in range(-2, 3):
    for r in range(-2, 3):
        s = -q - r
        
        if abs(s) <= 2: 
            randTe = terrain.pop()
            
            if randTe == "Desert":
                randTo = 7
            else:
                randTo = tokens.pop()
                
            engine.register_hex(q, r, s, randTe, randTo)

print(f"Total Hexes Generated: {len(engine.hexes)}")
print(f"Total Unique Vertices Registered: {len(engine.vertices)}")

@dataclass
class Player:
    id: Optional[int] = None
    strat: str = None

    resources: Dict[str, int] = field(default_factory=lambda: { 
        #We need field(defualt_factory) because
        #Every time a nwe player is created, call the
        #list function to give them a fresh, empty list
        "Wood": 2, #Give them this to create two settlements at the start
        "Brick": 2,
        "Wheat": 2,
        "Wool": 2,
        "Ore": 0
    })

    roads: List[Tuple] = field(default_factory=list)
    settlements: List[Tuple] = field(default_factory=list)
    cities: List[Tuple] = field(default_factory=list)

    victory_points: int = 0

    def get_res_urgency(self) -> Dict[str, float]:
        #how much do we need a reousrce?
        res = self.resources

        urgency = {k: 0.0 for k in res.keys()}

        for r in ["Wood", "Brick", "Wheat", "Wool",]:
            if res[r] == 0:
                urgency[r] += SETTLEMENT_URGENCY

        if res["Ore"] < 3:
            urgency["Ore"] += ORE_CITY_URGENCY
        if res["Wheat"] < 2:
            urgency["Wheat"] += WHEAT_CITY_URGENCY

        for r, amount in res.items():
            if amount > 4:
                urgency[r] -= OVER_URGENCY

        return urgency

    def propose_trade(self, state, other_player) -> Optional[Dict]:
        if self.strat != "heuristic":
            return None

        urgency = self.get_res_urgency()

        #find what we WANT(most urgent)
        most_needed = max(urgency, key=urgency.get)
        #Compared to what we can GIVE(least urgent)
        most_abundant = min(urgency, key=urgency.get)

        if self.resources[most_abundant] > 1 and urgency[most_needed] > 1.0:
            return {
                "give": {most_abundant: 1},
                "receive": {most_needed: 1}
            }
        return None

    def evaluate_trade(self, trade: Dict, state) -> bool:
        if self.strat != "heuristic":
            return random.random() < RANDOM_TRADE_BORDER

        #If we cna't afford it, no deal
        for res, amount in trade["receive"].items():
            if self.resources[res] < amount:
                return False

            urgency = self.get_res_urgency()

            value_gained = sum(urgency[r] * amount for r, amount in trade["give"].items())
            value_lost = sum(urgency[r] * amount for r, amount in trade["receive"].items())

            trade_score = value_gained - value_lost

            if self.strat == "heuristic-trade-adaptive":
                proposing_player = state.active_player
                if proposing_player.victory_points >= 8:
                    trade_score -= ENDGAME_TRADE_SUB  # Tighten restrictions heavily near endgame
                elif proposing_player.victory_points > self.victory_points:
                    trade_score -= WINNING_TRADE_SUB  # Slight penalty if they are beating us

        # Accept if the trade benefits us on net value
        return trade_score > 0.1
        
    def eval_action(self, action, state):
        score = 0
        
        # 1. Base values for immediate builds
        if action["type"] == "build_settlement":
            score += 50  # Significantly increase settlement priority
            hex_numbers = state.board.get_numbers_for_vertex(action["vertex_key"])
            score += sum(DICE_PROBABILITY.get(num, 0) for num in hex_numbers)

        elif action["type"] == "build_city":
            score += 60
            
        elif action["type"] == "build_road":
            score += 2 
            
        elif action["type"] == "pass":
            score += 10

            res = self.resources
            
            settlement_combos = min(res["Wood"], res["Brick"], res["Wheat"], res["Wool"])
            score += settlement_combos * 25
            
            city_combos = min(res["Ore"] // 3, res["Wheat"] // 2) if res["Ore"] >= 3 else 0
            score += city_combos * 30
            
            total_cards = sum(res.values())
            if total_cards > 7:
                score -= (total_cards - 7) * 5

        return score


    def choose_action(self, state):
        actions = state.get_actions()
        if self.strat == "heuristic" or "heuristic-trade-adaptive":
            scored_actions = [(self.eval_action(a, state), a) for a in actions]
            best_action = max(scored_actions, key=lambda item: item[0])[1]
            return best_action
        #Else return random
        return random.choice(actions)

    def discard_player_resources(self, cards_discard: int, bank: Dict[str, int]):
        
        for _ in range(cards_discard):
            urgency = self.get_res_urgency()
            
            available_urgencies = {
                res: score for res, score in urgency.items() 
                if self.resources[res] > 0
            }
            
            if not available_urgencies:
                break

            least_urgent_res = min(available_urgencies, key=available_urgencies.get)
            
            self.resources[least_urgent_res] -= 1
            bank[least_urgent_res] += 1

    
class GameState:
    def __init__(self, board, num_players=4): #Constructor
        self.board = board

        self.players = [
            Player(id=i, strat=STRATS[i % len(STRATS)])
            for i in range(num_players)
        ]

        self.current_player = 0
        self.turn_number = 0
        self.dice_roll = None
        self.game_over = False

        self.bank = {
            "Wood": 11,#EAch player starts with these remember
            "Brick": 11,
            "Wheat": 11,
            "Wool": 11,
            "Ore": 19
        }

        self.history = {
            "turn": [],
            "vp": {p.id: [] for p in self.players},
            "resources": {
                p.id: {r: [] for r in p.resources}
                for p in self.players
            },
            "urgency": {
                p.id: {r: [] for r in p.resources}
                for p in self.players
            },
            "hand_size": {p.id: [] for p in self.players},
            "bank": {r: [] for r in self.bank}
        }

    def record_state(self):
        self.history["turn"].append(self.turn_number)

        for p in self.players:
            self.history["vp"][p.id].append(p.victory_points)

            for resource in p.resources:
                self.history["resources"][p.id][resource].append(
                    p.resources[resource]
                )

            urgency = p.get_res_urgency()

            for resource in urgency:
                self.history["urgency"][p.id][resource].append(
                    urgency[resource]
                )

            self.history["hand_size"][p.id].append(
                sum(p.resources.values())
            )

        for resource in self.bank:
            self.history["bank"][resource].append(
                self.bank[resource]
            )

    @property
    def active_player(self):
        return self.players[self.current_player]

    def spend_resource(self, player, resource, amount):
        player.resources[resource] -= amount
        self.bank[resource] += amount

    def give_resources(self, roll):
        if roll == 7:
            for player in self.players:
                cards = sum(player.resources.values())

                if cards > 7:
                    cards_discard = cards // 2

                    player.discard_player_resources(cards_discard, self.bank)
        rolled_hexes = self.board.roll_index.get(roll, [])
        for hex_tile in rolled_hexes:
            if hex_tile.resource == "Desert":
                continue
            for v_key in hex_tile.vertices:
                vertex = self.board.vertices.get(v_key)
                if vertex and vertex.building_type is not None:
                    owner = next((p for p in self.players if p.id == vertex.owner_id), None)
                    if owner:
                        income = 1 if vertex.building_type == "Settlement" else 2
                        income = min(income, self.bank[hex_tile.resource])
                        owner.resources[hex_tile.resource] += income
                        self.bank[hex_tile.resource] -= income
                        print(f" -> Player_{owner.id} gained +{income} {hex_tile.resource}!")

    def execute_trade(self, proposer, receiver, trade):
        for res, amt in trade["give"].items():
            proposer.resources[res] -= amt
            receiver.resources[res] += amt

        for res, amt in trade["receive"].items():
            receiver.resources[res] -= amt
            proposer.resources[res] += amt

        print(f"TRADE: Player {proposer.id} traded {amt} {res} with Player {receiver.id}")

    def get_actions(self):
        player = self.active_player
        actions = []
        firstfew = False
        if(len(player.settlements) + len(player.cities) < 2):
            firstfew = True
        if player.resources["Wood"] >= 1 and player.resources["Brick"] >= 1 and player.resources["Wheat"] >= 1 and player.resources["Wool"] >= 1:
            
            for v_key, vertex in self.board.vertices.items():
                if vertex.building_type is None:
                    
                    distance_rule_passed = True
                    connected_to_road = False

                    #Scan all edges to evaluate this specific vertex (v_key)
                    for edge_key, edge in self.board.edges.items():
                        
                        if v_key in edge_key:
                            
                            if edge.owner_id == player.id:
                                connected_to_road = True

                            neighbor_key = edge_key[1] if edge_key[0] == v_key else edge_key[0]
                            neighbor_vertex = self.board.vertices[neighbor_key]
                            
                            if neighbor_vertex.building_type is not None:
                                distance_rule_passed = False

                    if firstfew:
                        connected_to_road = True
                        
                    if distance_rule_passed and connected_to_road:
                        actions.append({"type": "build_settlement", "vertex_key": v_key})


        if player.resources["Wheat"] >= 2 and player.resources["Ore"] >= 3:
            for v_key, vertex in self.board.vertices.items():
                if vertex.building_type == "Settlement" and vertex.owner_id == player.id:
                    actions.append({"type": "build_city", "vertex_key": v_key})

        if(player.resources["Wood"] >= 1 and player.resources["Brick"] >= 1):
            for edge_key, edge in self.board.edges.items():
                if edge.owner_id is None:
                    v1, v2 = edge_key

                    connected = False

                    if self.board.vertices[v1].owner_id == player.id or self.board.vertices[v2].owner_id == player.id:
                        connected = True

                    else:
                        for other_key, other_edge in self.board.edges.items():
                            if other_edge.owner_id == player.id:
                                if v1 in other_key or v2 in other_key:
                                    connected = True
                                    break
                    if connected:
                        actions.append({"type": "build_road", "edge_key": edge_key})

        if player.resources["Wood"] >= 4:
            for get_resource in ["Wheat", "Wool", "Ore"]:
                if self.bank[get_resource] > 0:
                    actions.append({
                        "type": "maritime",
                        "give": "Wood",
                        "get": get_resource
                    })

        if player.resources["Wheat"] >= 4:
                    for get_resource in ["Wood", "Wool", "Ore"]:
                        if self.bank[get_resource] > 0:
                            actions.append({
                                "type": "maritime",
                                "give": "Wheat",
                                "get": get_resource
                            })

        if player.resources["Wool"] >= 4:
                    for get_resource in ["Wheat", "Wood", "Ore"]:
                        if self.bank[get_resource] > 0:
                            actions.append({
                                "type": "maritime",
                                "give": "Wool",
                                "get": get_resource
                            })

        if player.resources["Ore"] >= 4:
                    for get_resource in ["Wheat", "Wool", "Wood"]:
                        if self.bank[get_resource] > 0:
                            actions.append({
                                "type": "maritime",
                                "give": "Ore",
                                "get": get_resource
                            })
        actions.append({"type": "pass"})

        return actions

    def execute_action(self, action: dict):
        player = self.active_player
        action_type = action.get("type")

        if action_type == "build_settlement":
            v_key = action["vertex_key"]
            vertex = self.board.vertices[v_key]
            
            # 1. Update Board
            vertex.building_type = "Settlement"
            vertex.owner_id = player.id
            
            # 2. Deduct Cost
            player.resources["Wood"] -= 1
            player.resources["Brick"] -= 1
            player.resources["Wheat"] -= 1
            player.resources["Wool"] -= 1
            self.bank["Wood"] += 1
            self.bank["Brick"] += 1
            self.bank["Wheat"] += 1
            self.bank["Wool"] += 1
                        
            print(f"        SETTLEMENT: Player {player.id} built a Settlement!")
            player.settlements.append(v_key)
            player.victory_points+=1

        elif action_type == "build_city":
            v_key = action["vertex_key"]
            vertex = self.board.vertices[v_key]
            
            vertex.building_type = "City"
            
            player.resources["Wheat"] -= 2
            player.resources["Ore"] -= 3
            self.bank["Wheat"] += 2
            self.bank["Ore"] += 3
            print(f"        CITY: Player {player.id} upgraded to a City!")
            player.settlements.remove(v_key)
            player.cities.append(v_key)
            player.victory_points+=1

        elif action_type == "build_road":
            e_key = action["edge_key"]
            edge = self.board.edges[e_key]
            
            edge.owner_id = player.id
            player.resources["Wood"] -= 1
            player.resources["Brick"] -= 1
            self.bank["Wood"] += 1
            self.bank["Brick"] += 1
            print(f"        ROAD: Player {player.id} built a Road!")

        elif action_type == "maritime":
            player.resources[action.get("give")] -= 4
            self.bank[action.get("give")] += 4
            player.resources[action.get("get")] += 1
            self.bank[action.get("get")] -= 1
            print(f"MARITIME Player {player.id} maritimed {action.get("give")} for {action.get("get")}")

        elif action_type == "pass":
            print(f"Player {player.id} passed.")

state = GameState(engine, num_players=4)
all_vertex_keys = list(engine.vertices.keys())


def roll_dice():
    return random.randint(1, 6) + random.randint(1, 6)
def play_turn_with_visuals(state, ax, fig, road_artists, building_artists):
    state.record_state()
    player = state.active_player
    if(state.turn_number > 9):
        roll = roll_dice()
        state.dice_roll = roll
        state.give_resources(roll)

    for other_player in state.players:
        if other_player.id != player.id:
            trade_proposal = player.propose_trade(state, other_player)
            if trade_proposal and other_player.evaluate_trade(trade_proposal, state):
                state.execute_trade(player, other_player, trade_proposal)
                break

    legal_moves = state.get_actions()
    chosen_move = player.choose_action(state)
    state.execute_action(chosen_move)

    player_colors = {
            0: "#ff0000",
            1: "#0077ff",
            2: "#FDEC00",
            3: "#b700ff"
        }

    for edge_key, edge in state.board.edges.items():
        if edge.owner_id is not None:
            road_artists[edge_key].set_color(player_colors.get(edge.owner_id, "#000000"))
            road_artists[edge_key].set_visible(True)

    for vertex_key, vertex in state.board.vertices.items():
        if vertex.building_type is not None:
            artist = building_artists[vertex_key]
            artist.set_marker('^' if vertex.building_type == "Settlement" else 's')
            artist.set_markersize(12 if vertex.building_type == "Settlement" else 14)
            artist.set_color(player_colors.get(vertex.owner_id, "#000000"))
            building_artists[vertex_key].set_visible(True)

    if(state.turn_number > 9):
        print(f"Turn {state.turn_number + 1}: {player.id} rolled {roll}")
        
    turn_highlights = []

    size = 1.0
    h_dist = size * np.sqrt(3)
    v_dist = size * 1.5

    if(state.turn_number > 9):
        rolled_hexes = state.board.roll_index.get(roll, [])

        for hex_tile in rolled_hexes:
            q, r, s = hex_tile.coordinate
            x = h_dist * (q + r / 2.0)
            y = v_dist * r
            
            highlight = plt.Circle(
                (x, y), radius=0.25, color='red', 
                fill=False, linewidth=3, zorder=5
            )
            ax.add_patch(highlight)
            turn_highlights.append(highlight)

        ax.set_title(f"Turn {state.turn_number + 1} | {player.id} rolled: {roll}", fontsize=16, weight='bold')
    
    fig.canvas.draw_idle()
    plt.pause(0.1)

    for patch in turn_highlights:
        patch.remove()

    state.current_player = (state.current_player + 1) % len(state.players)
    state.turn_number += 1

def setup_catan_board_visuals(board: CatanBoard):
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    
    color_map = {
        "Wood": "#4B3908", "Wheat": "#FFD700", "Wool": "#90EE90",
        "Brick": "#B22222", "Ore": "#708090", "Desert": "#F4A460",
    }

    
    size = 1.0
    h_dist = size * np.sqrt(3)
    v_dist = size * 1.5

    #Making hexes
    for coord, hex_tile in board.hexes.items():
        q, r, s = coord
        x = h_dist * (q + r / 2.0)
        y = v_dist * r
        
        facecolor = color_map.get(hex_tile.resource, "#FFFFFF")
        hex_patch = RegularPolygon(
            (x, y), numVertices=6, radius=size, facecolor=facecolor, 
            edgecolor='black', linewidth=1.5, alpha=0.8
        )
        ax.add_patch(hex_patch)
        
        label = f"{hex_tile.resource}\n({hex_tile.number_token})"
        ax.text(
            x, y, label, ha='center', va='center', 
            fontsize=9, weight='bold', color='black',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.6, edgecolor='none')
        )
        
        coord_label = f"{q},{r},{s}"
        ax.text(x, y - size*0.5, coord_label, ha='center', va='center', fontsize=7, color='gray')

    #Making vertexes
    player_colors = {
                0: "#ff0000",
                1: "#0077ff",
                2: "#FDEC00",
                3: "#b700ff"
            }
    building_artists = {}
    for coord, vertex in board.vertices.items():
        x, y = get_vertex_xy(coord, size)
        building_type = vertex.building_type or "Settlement"
        artist, = ax.plot(
            x, y,
            marker='^' if building_type == "Settlement" else 's',
            color=player_colors.get(vertex.owner_id, "#FFFFFF"),
            markersize=12 if building_type == "Settlement" else 14,
            markeredgecolor='black',
            markeredgewidth=1.5,
            zorder=10,
            visible=vertex.building_type is not None
        )
        building_artists[coord] = artist

        #Making roads
    road_artists = {}
    for edge_key, edge in board.edges.items():
        v1, v2 = edge_key
        x1, y1 = get_vertex_xy(v1, size)
        x2, y2 = get_vertex_xy(v2, size)
        line, = ax.plot(
            [x1, x2], [y1, y2],
            color=player_colors.get(edge.owner_id, "#000000"),
            linewidth=5,
            zorder=15,
            visible=edge.owner_id is not None
        )
        road_artists[edge_key] = line

    ax.autoscale_view()
    plt.axis('off')
    return fig, ax, road_artists, building_artists

fig, ax, road_artists, building_artists = setup_catan_board_visuals(engine)

for _ in range(100):
    play_turn_with_visuals(state, ax, fig, road_artists, building_artists)

plt.ioff()
plt.show()

def plot_resources(state, player_id):
    turns = state.history["turn"]

    plt.figure(figsize=(10, 5))

    for resource in state.history["resources"][player_id]:
        values = state.history["resources"][player_id][resource]

        plt.plot(turns, values, label=resource)

    plt.xlabel("Turn")
    plt.ylabel("Resources Held")
    plt.title(f"Player {player_id} Resource Inventory")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

def plot_urgency(state, player_id):
    turns = state.history["turn"]

    plt.figure(figsize=(10, 5))

    for resource in state.history["urgency"][player_id]:
        values = state.history["urgency"][player_id][resource]

        plt.plot(turns, values, label=resource)

    plt.xlabel("Turn")
    plt.ylabel("Urgency")
    plt.title(f"Player {player_id} Resource Urgency")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

def plot_vp(state):
    turns = state.history["turn"]

    plt.figure(figsize=(10, 5))

    for player_id in state.history["vp"]:
        plt.plot(
            turns,
            state.history["vp"][player_id],
            label=f"Player {player_id}"
        )

    plt.xlabel("Turn")
    plt.ylabel("Victory Points")
    plt.title("Victory Points Over Time")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

def plot_hand_size(state):
    turns = state.history["turn"]

    plt.figure(figsize=(10, 5))

    for player_id in state.history["hand_size"]:
        plt.plot(
            turns,
            state.history["hand_size"][player_id],
            label=f"Player {player_id}"
        )

    plt.axhline(7, linestyle="--", label="7-card threshold")

    plt.xlabel("Turn")
    plt.ylabel("Cards in Hand")
    plt.title("Resource Hand Size")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

def plot_bank(state):
    turns = state.history["turn"]

    plt.figure(figsize=(10, 5))

    for resource in state.history["bank"]:
        plt.plot(
            turns,
            state.history["bank"][resource],
            label=resource
        )

    plt.axhline(0, linestyle="--")

    plt.xlabel("Turn")
    plt.ylabel("Cards Remaining in Bank")
    plt.title("Resource Bank Supply")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

def plot_scarcity(state):
    turns = state.history["turn"]
    plt.figure(figsize=(10, 5))

    for resource in state.history["bank"]:
        scarcity_history = [1 - (bank_val / 19) for bank_val in state.history["bank"][resource]]
        
        plt.plot(
            turns,
            scarcity_history,
            label=resource
        )
    plt.axhline(0, linestyle="--")
    
    plt.xlabel("Turn")
    plt.ylabel("Scarcity (1 - Bank / 19)")
    plt.title("Scarcity over time")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

    

plot_resources(state, 0)
plot_urgency(state, 0)
plot_vp(state)
plot_hand_size(state)
plot_bank(state)
plot_scarcity(state)