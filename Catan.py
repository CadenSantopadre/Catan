import random

class CatanMap:
    def __init__(self):
        # 1. Define a tiny 3-tile board for simplicity: 
        # Coordinate -> (Resource Type, Dice Token Number)
        self.tiles = {
            (0, 0): {"resource": "wood", "token": 6},
            (1, -1): {"resource": "brick", "token": 8},
            (0, -1): {"resource": "wood", "token": 5}
        }
        
        # 2. Track who owns which corner. 
        # Key: Corner Coordinate Tuple -> Value: 'player' or None
        self.settlements = {}

    def get_canonical_corner(self, tile_coord, corner_pos):
        """
        Fixes the duplicate corner problem. 
        Example: The BOTTOM corner of (0,-1) is the EXACT SAME physical space
        as the TOP corner of (0,0). We force the computer to use one shared name.
        """
        q, r = tile_coord
        if corner_pos == "BOTTOM":
            # Instead of tile (q, r)'s bottom, use tile (q, r+1)'s top
            return ((q, r + 1), "TOP")
        # You would expand this for all shared directions, but this works for our demo!
        return (tile_coord, corner_pos)

    def place_settlement(self, tile_coord, corner_pos, player_name="AI"):
        """Saves a settlement to a specific physical corner"""
        corner = self.get_canonical_corner(tile_coord, corner_pos)
        self.settlements[corner] = player_name

    def distribute_resources(self, rolled_dice):
        """
        Scans the board for the rolled number, finds adjacent settlements,
        and returns a dictionary of who gets what.
        """
        payouts = {"wood": 0, "brick": 0}
        
        # Look at every tile on the board
        for tile_coord, tile_data in self.tiles.items():
            if tile_data["token"] == rolled_dice:
                resource_type = tile_data["resource"]
                
                # Check the corners touching this winning tile
                # (For simplicity, we will just check TOP and BOTTOM corners)
                for pos in ["TOP", "BOTTOM"]:
                    corner = self.get_canonical_corner(tile_coord, pos)
                    
                    # If someone built a settlement here, they get a resource!
                    if self.settlements.get(corner) == "AI":
                        payouts[resource_type] += 1
                        
        return payouts


class GameState:
    def __init__(self):
        self.resources = {"wood": 2, "brick": 2, "wheat": 0, "ore": 0} # Start with enough to build
        self.inventory = {"roads": 0, "settlements": 0}
        self.victory_points = 0
        self.turn_count = 0
        
        # INJECT THE MAP CLASS HERE
        self.map = CatanMap()
        
        # Place 1 starting settlement on the board to kick off production
        # Let's put it on the TOP corner of tile (0,0) which is a Wood-6 tile!
        self.map.place_settlement((0, 0), "TOP", player_name="AI")
        self.inventory["settlements"] += 1
        self.victory_points += 1

    def get_valid_actions(self):
        actions = ["END_TURN"]
        if self.resources["wood"] >= 1 and self.resources["brick"] >= 1:
            actions.append("BUILD_ROAD")
        if self.resources["wood"] >= 2 and self.resources["brick"] >= 2:
            # For this simple demo, we see if we can build on the BOTTOM corner of tile (0,0)
            # which is an empty spot touching Wood-6 and Brick-8
            bottom_corner = self.map.get_canonical_corner((0,0), "BOTTOM")
            if bottom_corner not in self.map.settlements:
                actions.append("BUILD_SETTLEMENT")
        return actions

    def apply_action(self, action):
        if action == "BUILD_ROAD":
            self.resources["wood"] -= 1
            self.resources["brick"] -= 1
            self.inventory["roads"] += 1

        elif action == "BUILD_SETTLEMENT":
            self.resources["wood"] -= 2
            self.resources["brick"] -= 2
            self.inventory["settlements"] += 1
            self.victory_points += 1
            
            # Update the physical map state!
            self.map.place_settlement((0,0), "BOTTOM", player_name="AI")
            
        elif action == "END_TURN":
            self._execute_passive_turn_phases()

    def _execute_passive_turn_phases(self):
        self.turn_count += 1
        
        # Simulate a real 2d6 Catan dice roll
        dice = random.randint(1, 6) + random.randint(1, 6)
        
        # ASK THE MAP WHO WINS WHAT
        payouts = self.map.distribute_resources(dice)
        
        # Update our inventory based on map realities
        for resource, amount in payouts.items():
            if amount > 0:
                self.resources[resource] += amount
                print(f"  Turn {self.turn_count}: Rolled a {dice}! Map awarded {amount} {resource}.")

    def is_game_over(self):
        return self.victory_points >= 5


# --- RUN SIMULATION ---
state = GameState()
print("Starting game with 1 settlement on a Wood (6) tile...")

while not state.is_game_over() and state.turn_count < 100:
    moves = state.get_valid_actions()
    
    if "BUILD_SETTLEMENT" in moves:
        chosen_move = "BUILD_SETTLEMENT"
        print(f"Turn {state.turn_count}: AI built a second settlement on a Brick (8) / Wood (6) intersection!")
    elif "BUILD_ROAD" in moves:
        chosen_move = "BUILD_ROAD"
    else:
        chosen_move = "END_TURN"
        
    state.apply_action(chosen_move)

print(f"\nHeuristic AI finished in {state.turn_count} turns. Final VP: {state.victory_points}")
