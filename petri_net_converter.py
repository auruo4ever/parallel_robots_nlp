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

def extract_ornoun(text):
    pattern = r"^(ORNOUN)_([^_]+(?:_[^_]+)*)_([^_]+)$"  
    match = re.match(pattern, text)
    
    if match:
        final_part = f"{match.group(1)}_{match.group(3)}" 
        middle_part = match.group(2) 
        return final_part, middle_part
    return None, None  


def draw_petri_net(actors_actions):
    n = PetriNet('petri_net')
    n.add_place(Place('start'))
    n.add_transition(Transition('task_start'))
    n.add_input('start', 'task_start', Value("1"))
    
    n.add_place(Place('end'))
    n.add_transition(Transition('task_end'))
    n.add_output('end', "task_end", Value("1"))


    for actor in actors_actions.keys():
        #start place and transition
        n.add_place(Place(actor+str(-1), "Robot is on"))
        previous_place = actor+str(-1)
        n.add_output(actor+str(-1), 'task_start', Value("1"))
        
        i = 0
        while i < len(actors_actions[actor]):
            verb = actors_actions[actor][i]
            
            #for sequential
            if not verb.startswith(("BARRIER_", "SINC_", "OR")):
                n.add_transition(Transition(verb+'_'+actor+'_'+str(i)))
            
                n.add_input(previous_place, verb+'_'+actor+'_'+str(i), Value("1"))
                n.add_place(Place(actor+str(i)))
                n.add_output(actor+str(i), verb+'_'+actor+'_'+str(i), Value("1"))
                
                previous_place = actor+str(i)
                    
            else:
            #for barriers
                if verb.startswith(("BARRIER_")):
                    if not transition_exists(n, verb):
                        n.add_transition(Transition(verb))
                    n.add_input(previous_place, verb, Value("1"))
                    n.add_place(Place(actor+str(i)))
                    n.add_output(actor+str(i), verb, Value("1"))
                    previous_place = actor+str(i)                    
        

                if verb.startswith(("SINC_")):    
                    verb = actors_actions[actor][i]
                    if not transition_exists(n, verb):
                        n.add_transition(Transition(verb))
                    n.add_input(previous_place, verb, Value("1"))
                    n.add_place(Place(actor+str(i)))
                    n.add_output(actor+str(i), verb, Value("1"))
                    previous_place = actor+str(i)           
                    
                    
                #for OR between verbs
                if verb.startswith(("ORVERB_")):
                    #ORVERB_take_wash_0
                    brenches = extract_brenching(verb)
                    print(brenches)

                    n.add_place(Place(actor+str(i)))
                    for b in brenches:
                        transition_name = b+'_'+actor+'_'+str(i)
                        n.add_transition(Transition(transition_name))
                        n.add_input(previous_place, transition_name, Value("1"))
                        n.add_output(actor+str(i), transition_name, Value("1"))
                    
                    previous_place = actor+str(i)  
                
                #for OR between nouns
                if verb.startswith(("ORNOUN_")):    
                    print("hehehe")
                    transition_name, actors_name = extract_ornoun(verb)
                    print(transition_name)
                    if not transition_exists(n, transition_name):
                        n.add_transition(Transition(transition_name))
                        n.add_place(Place("PLACE_"+transition_name))
                        n.add_output("PLACE_"+transition_name, transition_name, Value("1"))
                    n.add_input(previous_place, transition_name, Value("1"))
                    previous_place = "PLACE_"+transition_name
                    i+=1
                    verb = actors_actions[actor][i]
                    transition_name_2 = verb+'_'+actors_name+'_'+str(i)
                    if not transition_exists(n, transition_name_2):
                        n.add_transition(Transition(transition_name_2))
                        n.add_input(previous_place, transition_name_2, Value("1"))
                    
                        place_name="PLACE_"+transition_name+'2'
                        if not place_exists(n, place_name):
                            n.add_place(Place(place_name))
                            n.add_transition(Transition(transition_name+'2'))
                            n.add_input(place_name, transition_name+'2', Value("1"))
                        n.add_output(place_name, transition_name_2, Value("1"))
                    n.add_place(Place(actor+str(i)))
                    n.add_output(actor+str(i), transition_name+'2', Value("1"))
                    previous_place = actor+str(i)
                    
                                       
                    
            if i == len(actors_actions[actor]) - 1:
                n.add_input(previous_place, 'task_end', Value("ε"))     
            
            i += 1           

    n.draw("petri_net.png")
    n.draw("petri_net.dot")
    with open("petri_net.dot", "r") as f:
        dot_str = f.read()
    dot_to_json(dot_str)
    print(f"✅ Petri net saved")

def save_dependency_tree_as_svg(doc, filename="dependency_tree.svg"):
    svg = displacy.render(doc, style="dep", jupyter=False)
    if not svg:
        raise ValueError("Error: displacy.render() returned None.")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"✅ Dependency tree saved as {filename}")
