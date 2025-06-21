import snakes.plugins
snakes.plugins.load("gv", "snakes.nets", "nets")
from nets import *
import re
from collections import defaultdict
from save_as_json import dot_to_json 


def transition_exists(net, name):
    try:
        net.transition(name)  
        return True  
    except ConstraintError:
        return False


def place_exists(net, name):
    try:
        net.place(name)  
        return True  
    except ConstraintError:
        return False

def extract_brenching(text):
    pattern = r"ORVERB_([a-zA-Z_]+(?:_[a-zA-Z_]+)*)_"
    words = re.findall(pattern, text)
    return words[0].split('_') if words else []

def extract_oractor(text):
    pattern = r"^(ORNOUN)_([^_]+(?:_[^_]+)*)_([^_]+)$"  
    match = re.match(pattern, text)
    
    if match:
        final_part = f"{match.group(1)}_{match.group(3)}" 
        middle_part = match.group(2) 
        return final_part, middle_part
    return None, None  

def initialize_petri_net():
    n = PetriNet('petri_net')
    n.add_place(Place('start'))
    n.add_transition(Transition('task_start'))
    n.add_input('start', 'task_start', Value("1"))

    n.add_place(Place('end'))
    n.add_transition(Transition('task_end'))
    n.add_output('end', "task_end", Value("1"))

    return n

def process_actor_trace(actor, actions, net):
    net.add_place(Place(actor + str(-1), "Robot is on"))
    net.add_output(actor + str(-1), 'task_start', Value("1"))
    previous_place = actor + str(-1)

    i = 0
    while i < len(actions):
        action = actions[i]

        if not action.startswith(("BARRIER_", "SINC_", "OR")):
            previous_place = handle_regular_action(net, actor, i, action, previous_place)

        elif action.startswith("BARRIER_"):
            previous_place = handle_barrier(net, actor, i, action, previous_place)

        elif action.startswith("SINC_"):
            previous_place = handle_sync(net, actor, i, action, previous_place)

        elif action.startswith("ORVERB_"):
            previous_place = handle_orverb(net, actor, i, action, previous_place)

        elif action.startswith("ORNOUN_"):
            i, previous_place = handle_ornoun(net, actor, i, actions, previous_place)

        if i == len(actions) - 1:
            net.add_input(previous_place, 'task_end', Value("ε"))

        i += 1


def handle_regular_action(net, actor, i, action, previous_place):
    t_name = f"{action}_{actor}_{i}"
    net.add_transition(Transition(t_name))
    net.add_input(previous_place, t_name, Value("1"))
    place_name = f"{actor}{i}"
    net.add_place(Place(place_name))
    net.add_output(place_name, t_name, Value("1"))
    return place_name

def handle_barrier(net, actor, i, action, previous_place):
    if not transition_exists(net, action):
        net.add_transition(Transition(action))
    net.add_input(previous_place, action, Value("1"))
    place_name = f"{actor}{i}"
    net.add_place(Place(place_name))
    net.add_output(place_name, action, Value("1"))
    return place_name

def handle_sync(net, actor, i, action, previous_place):
    if not transition_exists(net, action):
        net.add_transition(Transition(action))
    net.add_input(previous_place, action, Value("1"))
    place_name = f"{actor}{i}"
    net.add_place(Place(place_name))
    net.add_output(place_name, action, Value("1"))
    return place_name

def handle_orverb(net, actor, i, action, previous_place):
    branches = extract_brenching(action)
    place_name = f"{actor}{i}"
    net.add_place(Place(place_name))
    for b in branches:
        t_name = f"{b}_{actor}_{i}"
        net.add_transition(Transition(t_name))
        net.add_input(previous_place, t_name, Value("1"))
        net.add_output(place_name, t_name, Value("1"))
    return place_name

def handle_ornoun(net, actor, i, actions, previous_place):
    transition_name, actors_name = extract_oractor(actions[i])
    if not transition_exists(net, transition_name):
        net.add_transition(Transition(transition_name))
        net.add_place(Place(f"PLACE_{transition_name}"))
        net.add_output(f"PLACE_{transition_name}", transition_name, Value("1"))
    net.add_input(previous_place, transition_name, Value("1"))
    previous_place = f"PLACE_{transition_name}"

    i += 1
    next_action = actions[i]
    t2_name = f"{next_action}_{actors_name}_{i}"
    if not transition_exists(net, t2_name):
        net.add_transition(Transition(t2_name))
        net.add_input(previous_place, t2_name, Value("1"))

        place_name = f"PLACE_{transition_name}2"
        if not place_exists(net, place_name):
            net.add_place(Place(place_name))
            net.add_transition(Transition(f"{transition_name}2"))
            net.add_input(place_name, f"{transition_name}2", Value("1"))
        net.add_output(place_name, t2_name, Value("1"))

    actor_place = f"{actor}{i}"
    net.add_place(Place(actor_place))
    net.add_output(actor_place, f"{transition_name}2", Value("1"))
    return i, actor_place


def save_petri_net_png(net, filename="petri_net.png"):
    """
    Saves the Petri net visualization as a PNG image.
    """
    net.draw(filename)
    print(f"Petri net image saved as {filename}")

def save_petri_net_dot(net, filename="petri_net.dot"):
    """
    Saves the Petri net structure in DOT format.
    """
    net.draw(filename)
    print(f"Petri net DOT file saved as {filename}")

def convert_dot_to_json(dot_filename="petri_net.dot"):
    """
    Converts the DOT file to JSON format using `dot_to_json`.
    """
    with open(dot_filename, "r") as f:
        dot_str = f.read()
    dot_to_json(dot_str)
    print("Petri net DOT file saved as JSON")

def finalize_and_save_petri_net(net):
    save_petri_net_png(net)
    save_petri_net_dot(net)
    convert_dot_to_json()
    print("✅ Petri net saved.")



def draw_petri_net(actors_actions):
    n = initialize_petri_net()
    
    for actor in actors_actions.keys():
        process_actor_trace(actor, actors_actions[actor], n)

    finalize_and_save_petri_net(n)