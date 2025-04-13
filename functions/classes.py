from collections import defaultdict

class OccupancyCounter:
    def __init__(self):
        # Dictionary to store the counts with tuple of (list of lists, integer) as keys
        self._counter = defaultdict(int)
    
    def _make_key(self, list_of_lists, integer):
        # Convert the list of lists to a tuple of tuples for immutability
        list_of_lists_tuple = tuple(tuple(sublist) for sublist in list_of_lists)
        return (list_of_lists_tuple, integer)
    
    def __getitem__(self, key):
        list_of_lists, integer = key
        key = self._make_key(list_of_lists, integer)
        return self._counter[key]
    
    def __setitem__(self, key, count):
        list_of_lists, integer = key
        key = self._make_key(list_of_lists, integer)
        if count < 0:
            raise ValueError("Count cannot be negative")
        self._counter[key] = count
    
    def __contains__(self, key):
        list_of_lists, integer = key
        key = self._make_key(list_of_lists, integer)
        return key in self._counter
    
    def __repr__(self):
        # Provide a readable string representation of the counter
        return f"{self.__class__.__name__}({dict(self._counter)})"



class Node:
    def __init__(self, position):
        self.position = position  # (x, y, t)
        self.g = float('inf')
        self.h = 0
        self.f = float('inf')
        self.parent = None

    def __lt__(self, other):
        return self.f < other.f




class Token:
    def __init__(self):
        self.time=0
        self.unassigned_tasks = []
        self.agents = []
        self.nodes = {}
        self.occupied_spacetime = set()
        self.occupied_spacetime_edges = set()
        self.occupied_partition_counter = OccupancyCounter()
        self.occupied_spacetime_wo_counted = set()
        self.makespan=0
        self.tasking_time=0
        self.all_agents_idle_counter=0
        self.completed_tasks=0
        self.observations=[]
        self.replan_counter=0
        self.parking_spots=[]
        self.parking_constant = []



class SingleTeamToken:
    def __init__(self):
        self.time=0
        self.agents = []
        self.nodes = {}
        self.occupied_spacetime = set()
        self.occupied_spacetime_edges = set()
        self.occupied_partition_counter = OccupancyCounter()
        self.occupied_spacetime_wo_counted = set()
        self.parking_spots=[]
        self.parking_constant = []
        self.all_agents_idle_counter=0


        self.unassigned_home_tasks = []
        self.unassigned_guest_tasks = []


        self.home_makespan=0
        self.home_tasking_time=0
        self.home_completed_tasks=0
        self.home_replan_counter=0
        self.guest_makespan=0
        self.guest_tasking_time=0
        self.guest_completed_tasks=0
        self.guest_replan_counter=0




class PathState:
    def __init__(self, path_state=None, time=None, agent_role=None, related_agent_ids=None, gate_or_border_before=None, gate_or_border_after=None):
        self.path_state = path_state
        self.time = time
        self.agent_role = agent_role
        self.related_agent_ids = related_agent_ids
        self.gate_or_border_before = gate_or_border_before
        self.gate_or_border_after = gate_or_border_after






class Agent:
    def __init__(self, id, agent_type, color, location, state, path=None, path_states=None):
        self.id = id
        self.agent_type = agent_type
        self.color = color
        self.location = location
        self.state = state
        self.assigned_task = None
        self.path = path if path is not None else []  # Create a new list if path is None
        self.path_states = path_states if path_states is not None else []  # Same for path_states
        self.current_path_state = None
        self.task_assignment_time = None
        self.path_set = None
        self.gating_path_set = None
        self.claimed_parking_spot = None
        self.earliest_timestep_invalidated = None
        self.latest_path_validated = None
        self.latest_gating_path_set = None

        

class Task:
    def __init__(self, start, goal):
        self.start = start
        self.goal = goal






class PathUnfeasible(Exception):
    def __init__(self, message="No Helper Paths to Make Tentative Path Valid Could be Planned"):
        self.message = message
        super().__init__(self.message)


class SimulationEnd(Exception):
    def __init__(self, message="No Paths Possible. Will Collide."):
        self.message = message
        super().__init__(self.message)