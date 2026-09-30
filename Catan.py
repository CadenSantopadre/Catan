import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import RegularPolygon

plt.ion()

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
DICE_PROBABILITY = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}
@dataclass
class Player:
    id: Optional[int] = None
    strat: str = None

    resources: Dict[str, int] = field(default_factory=lambda: { 
        #We need field(defualt_factory) because
        #Every time a nwe player is created, call the
        #list function to give them a fresh, empty list
        "Wood": 0,
        "Brick": 0,
        "Wheat": 0,
        "Wool": 0,
        "Ore": 0
    })

    roads: List[Tuple] = field(default_factory=list)
    settlements: List[Tuple] = field(default_factory=list)
    cities: List[Tuple] = field(default_factory=list)

    victory_points: int = 0

    def eval_action(self, action, state):
        score = 0
        if action["type"] == "build_settlement":
            score += 15
            hex_numbers = state.board.get_numbers_for_vertex(action["vertex_key"])
            score += sum(DICE_PROBABILITY.get(num, 0) for num in hex_numbers)

        elif action["type"] == "build_city":
            score += 30
            hex_numbers = state.board.get_numbers_for_vertex(action["vertex_key"])
            score += sum(DICE_PROBABILITY.get(num, 0) for num in hex_numbers)

        elif action["type"] == "build_road":
            score += 5

        elif action["type"] == "maritime":
            score +=1

        return score

    def choose_action(self, state):
        actions = state.get_actions()
        if not actions:
            return None
        
        if self.strat == "heuristic":
            scored_actions = [(self.eval_action(a, state), a) for a in actions]
            best_action = max(scored_actions, key=lambda item: item[0])[1]
            return best_action
        return random.choice(actions)

            

class GameState:
    def __init__(self, board, num_players=4): #Constructor
        self.board = board

        strats = ["random", "heuristic", "heuristic", "random"]

        self.players = [
            Player(id=i, strat=strats[i % len(strats)])
            for i in range(num_players)
        ]

        self.current_player = 0
        self.turn_number = 0
        self.dice_roll = None
        self.game_over = False

    @property
    def active_player(self):
        return self.players[self.current_player]

    def give_resources(self, roll):
        if roll == 7:
            return
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
                        owner.resources[hex_tile.resource] += income
                        print(f" -> Player_{owner.id} gained +{income} {hex_tile.resource}!")

    def get_actions(self):
        player = self.active_player
        actions = []

        if(player.resources["Wood"] >= 1 and player.resources["Brick"] >= 1 and player.resources["Wheat"] >= 1 and player.resources["Wool"] >= 1):
            for v_key, vertex in self.board.vertices.items():
                if vertex.building_type is None:
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
        if(player.resources["Wood"] >= 4):
            actions.append({"type": "maritime", "give": "Wood", "get": "Wheat"})
            actions.append({"type": "maritime", "give": "Wood", "get": "Wool"})
            actions.append({"type": "maritime", "give": "Wood", "get": "Ore"})

        if(player.resources["Wheat"] >= 4):            
            actions.append({"type": "maritime", "give": "Wheat", "get": "Wood"})
            actions.append({"type": "maritime", "give": "Wheat", "get": "Wool"})
            actions.append({"type": "maritime", "give": "Wheat", "get": "Ore"})

        if(player.resources["Wool"] >= 4):            
            actions.append({"type": "maritime", "give": "Wool", "get": "Wood"})
            actions.append({"type": "maritime", "give": "Wool", "get": "Wheat"})
            actions.append({"type": "maritime", "give": "Wool", "get": "Ore"})
            
        if(player.resources["Ore"] >= 4):            
            actions.append({"type": "maritime", "give": "Ore", "get": "Wood"})
            actions.append({"type": "maritime", "give": "Ore", "get": "Wool"})
            actions.append({"type": "maritime", "give": "Ore", "get": "Wheat"})

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
            print(f" --> Player {player.id} built a Settlement!")

        elif action_type == "build_city":
            v_key = action["vertex_key"]
            vertex = self.board.vertices[v_key]
            
            vertex.building_type = "City"
            
            player.resources["Wheat"] -= 2
            player.resources["Ore"] -= 3
            print(f" --> Player {player.id} upgraded to a City!")

        elif action_type == "build_road":
            e_key = action["edge_key"]
            edge = self.board.edges[e_key]
            
            edge.owner_id = player.id
            player.resources["Wood"] -= 1
            player.resources["Brick"] -= 1
            print(f" --> Player {player.id} built a Road!")

        elif action_type == "maritime":
            player.resources[action.get("give")] -= 4
            player.resources[action.get("get")] += 1
            print(f"--------------> Player {player.id} maritimed {action.get("give")} for {action.get("get")}")

        elif action_type == "pass":
            print(f" --> Player {player.id} passed.")

#Making example settlements/cities
# Create the game state
state = GameState(engine, num_players=4)
all_vertex_keys = list(engine.vertices.keys())

# Define a mapping of vertex indices to player IDs for testing resource generation
test_settlements = {
    10: 0,  # Player 0 Settlement
    15: 0,  # Player 0 Second Settlement
    25: 1,  # Player 1 Settlement
    32: 1,  # Player 1 Second Settlement
    40: 2,  # Player 2 Settlement
    45: 2,  # Player 2 Second Settlement
    50: 3,  # Player 3 Settlement
    52: 3,  # Player 3 Second Settlement
}

# Seed the board with our test settlements
for vertex_index, player_id in test_settlements.items():
    v_key = all_vertex_keys[vertex_index]
    engine.vertices[v_key].building_type = "Settlement"
    engine.vertices[v_key].owner_id = player_id
    
    # Also log it inside the player profile instances so their inventory state aligns
    state.players[player_id].settlements.append(v_key)

print(f"Successfully seeded {len(test_settlements)} test settlements onto the board layout.")


def roll_dice():
    return random.randint(1, 6) + random.randint(1, 6)
def play_turn_with_visuals(state, ax, fig, road_artists):
    player = state.active_player
    roll = roll_dice()
    state.dice_roll = roll
    state.give_resources(roll)
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

    print(f"Turn {state.turn_number + 1}: {player.id} rolled {roll}")

    turn_highlights = []

    size = 1.0
    h_dist = size * np.sqrt(3)
    v_dist = size * 1.5

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
                2: "#ffffff",
                3: "#b700ff"
            }
    for coord, vertex in board.vertices.items():
        if vertex.building_type is not None:
            x, y = get_vertex_xy(coord, size)
            color = player_colors.get(vertex.owner_id, "#FFFFFF")
            marker = '^' if vertex.building_type == "Settlement" else 's'
            msize = 12 if vertex.building_type == "Settlement" else 14
            
            ax.plot(x, y, marker=marker, color=color, markersize=msize, markeredgecolor='black', markeredgewidth=1.5, zorder=10)

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
    return fig, ax, road_artists

fig, ax, road_artists = setup_catan_board_visuals(engine)
 
for _ in range(100):
    play_turn_with_visuals(state, ax, fig, road_artists)

plt.ioff()
plt.show()