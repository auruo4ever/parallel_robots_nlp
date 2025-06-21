from entities import *
from collections import defaultdict
import snakes.plugins
snakes.plugins.load("gv", "snakes.nets", "nets")


# Indicates parallel or simultaneous actions
parallel_markers = ["while", "as", "when", "whilst", "simultaneously", "at the same time", "meanwhile", "during", "in parallel", "concurrently"]
# Indicates one task happens after another completes
after_completing_markers = ["after", "then", "once", "next", "subsequently", "following that", "later", "thereafter", "afterward"]
# Indicates one task must occur before another starts
before_completing_markers = ["before", "prior to", "in advance of", "ahead of", "earlier than"]
# Indicates a choice between alternatives
choice_markers = ["or", "either", "alternatively", "instead", "optionally"]
# Indicates tasks/actions that should be done together or sequentially with no branching
and_markers = ["and", "as well as", "together with", "additionally", "plus", "along with"]


def add_actors(subj):
    """
    Creates an Actor object from a subject token in the dependency parse tree.
    This function collects any particles related to the subject.
    """
    particles = []
    collect_particles(subj, particles)
    actor = Actor(subj.text, particles)
    return actor

def add_task(actions, actors):
    """
    Constructs a Task object by combining a list of actions and actors.
    If no actors are explicitly provided, a default placeholder actor is inserted 
    to ensure task completeness.
    """
    if len(actors) == 0:
        actors.append(Actor("Some_Actor"))
    task = Task(actions, actors)
    return task

def add_action(action, tag):
    """
    Creates an Action object from a verb token, collecting associated particles and refining the action name.
    This function analyzes the dependency tree to extract verb-related information
    such as prepositions and direct objects, and constructs a structured Action object.
    """
    particles = []
    collect_particles(action, particles) 
    action_name = collect_dobj(action)
    action1 = Action(action_name, particle=particles, tag=tag)
    return action1

def collect_subj_conjuncts(subj, actors):
    """
    Recursively collects all conjunct subjects linked to the main subject.
    """
    for child in subj.children:
        if child.dep_ == "conj":
            actor = add_actors(child)
            actors.append(actor)
            collect_subj_conjuncts(child, actors)

def collect_dobj(action):
    """
    Constructs a compound verb name by appending direct objects to the action.
    """
    action_name = action.text
    for child in action.children:
        if child.dep_ == "dobj":
            action_name += "_" + child.text
    return action_name

def collect_particles(subj, particles):
    """
    Collects particle modifiers associated with a subject or verb.
    """
    for child in subj.children:
        if child.dep_ == "cc":
            particle = Particle(child.text, tag="cc")
            particles.append(particle)
        if child.dep_ == "mark":
            particle = Particle(child.text, tag="mark")
            particles.append(particle)
        
        if child.dep_ == "advmod":
            particle = Particle(child.text, tag="advmod")
            particles.append(particle)
        
        if child.dep_ == "prep":
            particle = Particle(child.text, tag="prep")
            particles.append(particle)
        
def collect_conjuncts(action, task):
    """
    Identifies and processes conjunct or adverbial clause verbs linked to an action,
    and integrates them into the task or subtasks accordingly.
    This function handles both:
      - `conj` verbs 
      - `advcl` verbs 
    """
    for child in action.children:
        if child.dep_ == "conj" and child.pos_ == "VERB":
            conj_nsubj = []
            # Check if the conjunct action has its own subject
            for grandchild in child.children:
                if grandchild.dep_ == "nsubj":
                    actor = add_actors(grandchild)
                    conj_nsubj.append(actor)
                    collect_subj_conjuncts(grandchild, conj_nsubj)
             # Add a tag 
            action = add_action(child, tag="conj")
            # If no subject for the conjunct action, add it to the root's actions
            if not conj_nsubj:
                task.actions.append(action) 
            else:
                task = add_task(action, conj_nsubj)
                all_tasks.append(task)
            collect_conjuncts(child, task)
        if child.dep_ == "advcl" and child.pos_ == "VERB":
            conj_nsubj = []
            # Check if the sub action has its own subject
            for grandchild in child.children:                   
                if grandchild.dep_ == "nsubj":
                    actor = add_actors(grandchild)
                    conj_nsubj.append(actor)
                    collect_subj_conjuncts(grandchild, conj_nsubj)
            # Add a tag 
            action = add_action(child, tag="advcl")
            # Add a new subtask
            if not conj_nsubj:         
                subtask = add_task(action, task.actors)
            else:
                subtask = add_task(action, conj_nsubj)
            task.subtask = subtask

def analyse_tree(doc):
    """
    Constructs an execution plan E = (T1, T2, ..., Tn) from a natural language directive, 
    where each Ti represents a root task extracted from the dependency parse tree.
    """
    all_tasks = []

    for token in doc:
        if token.dep_ == "ROOT":
            action = add_action(token, tag="ROOT")
            action_data = [action]  # Start with the root action
            actors_list = []

            for child in token.children:
                if child.dep_ == "nsubj":
                    actor = add_actors(child)
                    actors_list.append(actor)
                    collect_subj_conjuncts(child, actors_list)

            task = add_task(action_data, actors_list)
            all_tasks.append(task)
            collect_conjuncts(token, task)

    return all_tasks



def find_subtask_type(task):
    """
    Determines the type of a subtask based on the first particle of its action.
    """
    if task.subtask is None:  
        return None  

    for action in task.subtask.actions:
        if action.particle:  
            return action.particle[0]  

    return None 

def is_this_or(actor):
    """
    Checks whether an actor is associated with the logical operator 'or'.
    """
    for p in actor.particle:
        if p.name == "or":
            return True
    return False

def is_particle_exist(words, particles):
    """
    Checks if any particle in the list of words matches one of the given particle names.
    """
    for word in words:
        for p in word.particle:
            if p.name.lower() in particles:
                return True
    return False

def print_names(actors):
    """
    Returns a string containing all actor names joined with underscores.
    """
    s = ""
    for a in actors:
        s+= a.name+("_")
    return s

def add_barrier_and_actions(actors, actions, names_str, order_cnt, actors_actions):
    """
    Appends BARRIER, actions, and SINC markers to each actor's action trace.
    """
    for actor in actors:
        actors_actions[actor.name].append(f"BARRIER_{names_str}{order_cnt}")
        if isinstance(actions, list):
            actors_actions[actor.name].extend(action.name for action in actions)
        else:
            actors_actions[actor.name].append(actions.name)
        actors_actions[actor.name].append(f"SINC_{names_str}{order_cnt}")

def handle_or_action_block(actors_before, action, order_cnt, actors_actions):
    """
    Handles disjunction logic for a group of actors,
    appending ORNOUN labels and the action to each actor's sequence.
    """
    if is_particle_exist(actors_before, and_markers):
        names_str = print_names(actors_before)
        for a in actors_before:
            label = f"ORNOUN_{names_str}_{order_cnt}"
            actors_actions[a.name].append(label)
            actors_actions[a.name].append(action.name)
    else:
        for a in actors_before:
            label = f"ORNOUN_{a.name}_{order_cnt}"
            actors_actions[a.name].append(label)
            actors_actions[a.name].append(action.name)

    return []

def add_barrier(actor, names_str, order_cnt, actors_actions):
    """
    Appends a barrier marker to the given actor's action sequence.
    """
    actors_actions[actor.name].append(f"BARRIER_{names_str}{order_cnt}")


def handle_after_marker(task, prev_task, order_cnt, actors_actions):
    unique_actors = {a.name: a for a in task.actors + prev_task.actors}
    actors = list(unique_actors.values())
    if len(actors) > 1:
        names_str = print_names(actors)
        for actor in actors:
            add_barrier(actor, names_str, order_cnt, actors_actions)
        order_cnt += 1
    return order_cnt

def handle_subtask_by_type(task, subtask_prep, order_cnt, actors_actions):
    subtask = task.subtask
    if subtask_prep.name in parallel_markers:
        return handle_parallel_subtask(task, subtask, order_cnt, actors_actions), True
    if subtask_prep.name in after_completing_markers:
        return handle_direct_subtask(task, subtask, order_cnt, actors_actions, before=False), True
    if subtask_prep.name in before_completing_markers:
        return handle_direct_subtask(task, subtask, order_cnt, actors_actions, before=True), True
    return order_cnt, False


def handle_parallel_subtask(task, subtask, order_cnt, actors_actions):
    unique_actors = {a.name: a for a in task.actors + subtask.actors}
    actors = list(unique_actors.values())
    names_str = print_names(task.actors)

    if len(actors) > 1:
        add_barrier_and_actions(task.actors, task.actions, names_str, order_cnt, actors_actions)
        add_barrier_and_actions(subtask.actors, subtask.actions, names_str, order_cnt, actors_actions)
        order_cnt += 1
    else:
        actor = task.actors[0]
        for action in task.actions + subtask.actions:
            actors_actions[actor.name].append(action.name)
    return order_cnt

def handle_direct_subtask(task, subtask, order_cnt, actors_actions, before):
    actors = list(set(task.actors + subtask.actors))
    names_str = print_names(actors)

    if not before:
        for actor in task.actors:
            add_barrier(actor, names_str, order_cnt, actors_actions)
            for action in task.actions:
                actors_actions[actor.name].append(action.name)
        for actor in subtask.actors:
            actors_actions[actor.name].append(subtask.actions[0].name)
            add_barrier(actor, names_str, order_cnt, actors_actions)
    else:
        for actor in task.actors:
            for action in task.actions:
                actors_actions[actor.name].append(action.name)
            add_barrier(actor, names_str, order_cnt, actors_actions)
        for actor in subtask.actors:
            add_barrier(actor, names_str, order_cnt, actors_actions)
            actors_actions[actor.name].append(subtask.actions[0].name)

    return order_cnt + 1

def handle_multi_actor_task(task, order_cnt, actors_actions):
    if is_particle_exist(task.actions, choice_markers):
        actions_str = print_names(task.actions)
        for actor in task.actors:
            if actor.name not in actors_actions:
                actors_actions[actor.name].append("ORVERB_" + actions_str + str(order_cnt))
    else:
        for action in task.actions:
            if is_particle_exist(task.actors, choice_markers):
                actors_before = []
                for actor in task.actors:
                    if actor.name not in actors_actions:
                        actors_before.append(actor)
                    if is_this_or(actor):
                        actors_before = handle_or_action_block(actors_before, action, order_cnt, actors_actions)
                names_str = print_names(actors_before)
                for a in actors_before:
                    actors_actions[a.name].append("ORNOUN_" + names_str + str(order_cnt))
                    actors_actions[a.name].append(action.name)
                order_cnt += 1
            else:
                names_str = print_names(task.actors)
                add_barrier_and_actions(task.actors, action, names_str, order_cnt, actors_actions)
                order_cnt += 1
    return order_cnt

def handle_single_actor_task(task, order_cnt, actors_actions):
    actor = task.actors[0]
    if is_particle_exist(task.actions, choice_markers):
        actions_str = print_names(task.actions)
        if actor.name not in actors_actions:
            actors_actions[actor.name].append("ORVERB_" + actions_str + str(order_cnt))
    else:
        for action in task.actions:
            actors_actions[actor.name].append(action.name)
    return order_cnt


def get_parallel_tasks(doc):
    """
    Constructs parallel execution traces for all actors from a parsed natural language document.
    For each actor a ∈ A, we define a linearized execution trace Ea, which is an ordered
    sequence of action and synchronization elements derived from the shared execution plan.
    
    Formally, the execution trace for actor a is represented as:
        Ea = (e1, e2, ..., en)
    """
    order_cnt = 0
    actors_actions = defaultdict(list)
    all_tasks = analyse_tree(doc)

    for i, task in enumerate(all_tasks):
        if i > 0 and is_particle_exist(task.actions, after_completing_markers):
            order_cnt = handle_after_marker(task, all_tasks[i-1], order_cnt, actors_actions)

        subtask_prep = find_subtask_type(task)
        if subtask_prep:
            order_cnt, should_continue = handle_subtask_by_type(task, subtask_prep, order_cnt, actors_actions)
            if should_continue:
                continue

        if len(task.actors) > 1:
            order_cnt = handle_multi_actor_task(task, order_cnt, actors_actions)
        else:
            order_cnt = handle_single_actor_task(task, order_cnt, actors_actions)

    print(actors_actions)
    return actors_actions
