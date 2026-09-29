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
    owner_id: Optional[str] = None         # "Player_1", "Player_2", etc.

@dataclass
class Edge: #Edges are the connectors between vertices
    coordinate: Tuple[str, str]            # Connects two vertex coordinate strings
    owner_id: Optional[str] = None         # Player ID for roads

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

        new_hex = HexTile(
            coordinate=hex_coord,
            resource=resource,
            number_token=token,
            vertices=vertex_keys
        )
        self.hexes[hex_coord] = new_hex
        if token in self.roll_index:
            self.roll_index[token].append(new_hex)

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

def draw_catan_board(board: CatanBoard):
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    
    color_map = {
        "Wood": "#4B3908",
        "Wheat": "#FFD700",
        "Wool": "#90EE90",
        "Brick": "#B22222",
        "Ore": "#708090",
        "Desert": "#F4A460"
    }
    
    size = 1.0
    h_dist = size * np.sqrt(3)
    v_dist = size * 1.5

    for coord, hex_tile in board.hexes.items():
        q, r, s = coord
        
        #Convert cube coordinates to xy
        x = h_dist * (q + r / 2.0)
        y = v_dist * r
        
        #get color
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

    ax.autoscale_view()
    plt.axis('off')
    plt.title("Generated Catan Board Layout", fontsize=16, weight='bold')
    plt.show()

@dataclass
class Player:
    id: Optional[int] = None

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
    
state = GameState(engine)

def roll_dice():
    return random.randint(1, 6) + random.randint(1, 6)

def play_turn_with_visuals(state, ax, fig):
    player = state.active_player
    roll = roll_dice()
    state.dice_roll = roll

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
        "Brick": "#B22222", "Ore": "#708090", "Desert": "#F4A460"
    }
    
    size = 1.0
    h_dist = size * np.sqrt(3)
    v_dist = size * 1.5

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

    ax.autoscale_view()
    plt.axis('off')
    return fig, ax

fig, ax = setup_catan_board_visuals(engine)
 
for _ in range(100):
    play_turn_with_visuals(state, ax, fig)

plt.ioff()
plt.show()

class GameState:
    def __init__(self, board, num_players=4):
        self.board = board

        self.players = [
            Player(i)
            for i in range(num_players)
        ]

        self.current_player = 0
        self.turn_number = 0
        self.dice_roll = None
        self.game_over = False

    @property
    def active_player(self):
        return self.players[self.current_player]

    def dist_resources(self, roll: int):
        if roll == 7:
            return

        rolled_hexes = self.board