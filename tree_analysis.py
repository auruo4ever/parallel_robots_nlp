
from entities import *
from collections import defaultdict
import snakes.plugins
snakes.plugins.load("gv", "snakes.nets", "nets")


parallel_markers = ["while", "as", "when", "whilst"]
after_completing_markers = ["after", "then", "After", "Then"]
before_completing_markers = ["before"]
choice_markers = ["or"]
and_markers = ["and"]


def analyse_tree(doc):

    all_tasks = []

    def add_actors(subj):
        prepositions = []
        collect_prepositions(subj, prepositions)
        actor = Noun(subj.text, prepositions)
        return actor
    
    def add_task(verbs, actors):
        if len(actors) == 0:
            actors.append(Noun("Some_Actor"))
        task = Task(verbs, actors)
        return task
    
    def add_verb(verb, tag):
        prepositions = []
        collect_prepositions(verb, prepositions) 
        verb_name = collect_dobj(verb)
        verb1 = Verb(verb_name, preposition=prepositions, tag=tag)
        return verb1

    def collect_subj_conjuncts(subj, actors):
        for child in subj.children:
            if child.dep_ == "conj":
                actor = add_actors(child)
                actors.append(actor)
                collect_subj_conjuncts(child, actors)
    
    def collect_dobj(verb):
        verb_name = verb.text
        for child in verb.children:
            if child.dep_ == "dobj":
                verb_name += "_" + child.text
        return verb_name
    
    def collect_prepositions(subj, prepositions):
        for child in subj.children:
            if child.dep_ == "cc":
                preposition = Preposition(child.text, tag="cc")
                prepositions.append(preposition)

            if child.dep_ == "mark":
                preposition = Preposition(child.text, tag="mark")
                prepositions.append(preposition)
            
            if child.dep_ == "advmod":
                preposition = Preposition(child.text, tag="advmod")
                prepositions.append(preposition)
            
            if child.dep_ == "prep":
                preposition = Preposition(child.text, tag="prep")
                prepositions.append(preposition)
            

    def collect_conjuncts(verb, task):
        for child in verb.children:
            if child.dep_ == "conj" and child.pos_ == "VERB":
                conj_nsubj = []

                # Check if the conjunct verb has its own subject
                for grandchild in child.children:
                    if grandchild.dep_ == "nsubj":
                        actor = add_actors(grandchild)
                        conj_nsubj.append(actor)
                        collect_subj_conjuncts(grandchild, conj_nsubj)

                 # Add a tag 
                verb = add_verb(child, tag="conj")

                # If no subject for the conjunct verb, add it to the root's verbs
                if not conj_nsubj:
                    task.verbs.append(verb) 
                else:
                    task = add_task(verb, conj_nsubj)
                    all_tasks.append(task)

                collect_conjuncts(child, task)

            if child.dep_ == "advcl" and child.pos_ == "VERB":
                conj_nsubj = []
                # Check if the sub verb has its own subject
                for grandchild in child.children:                   
                    if grandchild.dep_ == "nsubj":
                        actor = add_actors(grandchild)
                        conj_nsubj.append(actor)
                        collect_subj_conjuncts(grandchild, conj_nsubj)
                # Add a tag 
                verb = add_verb(child, tag="advcl")

                # Add a new subtask
                if not conj_nsubj:         
                    subtask = add_task(verb, task.nouns)
                else:
                    subtask = add_task(verb, conj_nsubj)
                task.subtask = subtask


    for token in doc:
        if token.dep_ == "ROOT":
            verb = add_verb(token, tag="ROOT")
            verb_data = [verb]  # Start with the root verb
            actors_list = []

            for child in token.children:
                if child.dep_ == "nsubj":
                    actor = add_actors(child)
                    actors_list.append(actor)
                    collect_subj_conjuncts(child, actors_list)

            task = add_task(verb_data, actors_list)
            all_tasks.append(task)
            collect_conjuncts(token, task)

    return all_tasks



def find_subtask_type(task):
    if task.subtask is None:  
        return None  

    for verb in task.subtask.verbs:
        if verb.preposition:  
            return verb.preposition[0]  

    return None 

def is_this_or(actor):
    for p in actor.preposition:
        if p.name == "or":
            return True
    return False

def is_preposition_exist(words, prepositions):
    for word in words:
        for p in word.preposition:
            if p.name in prepositions:
                return True
    return False

def print_names(actors):
    s = ""
    for a in actors:
        s+= a.name+("_")
    return s


#rules for created dictionary
def get_parallel_tasks(doc):
    order_cnt = 0
    actors_actions = defaultdict(list)
    all_tasks = analyse_tree(doc)
    print(all_tasks)


    for i, task in enumerate(all_tasks):
        
        #if task has a subsequencial mark
        if is_preposition_exist(task.verbs, after_completing_markers):
            prev_task = all_tasks[i-1]
            unique_nouns = {}

            for noun in task.nouns + prev_task.nouns:
                unique_nouns[noun.name] = noun  
            actors = list(unique_nouns.values())
            if len(actors) > 1:
                names_str = print_names(actors)
                for actor in actors: 
                    actors_actions[actor.name].append("BARRIER_" + names_str + str(order_cnt))                           
                order_cnt+=1
            

        #if task has subtask 
        subtask_prep = find_subtask_type(task)    
        if (subtask_prep):
            subtask = task.subtask

            #parallel synchronized execution
            if subtask_prep.name in parallel_markers:
                
                unique_nouns = {}
                for noun in task.nouns + subtask.nouns:
                    unique_nouns[noun.name] = noun  
                actors = list(unique_nouns.values())

                names_str = print_names(actors)
                if len(actors) > 1:
                    for actor in task.nouns:                                               
                        actors_actions[actor.name].append("BARRIER_" + names_str + str(order_cnt))
                        for verb in task.verbs:
                            actors_actions[actor.name].append(verb.name)
                        actors_actions[actor.name].append("SINC_"+ names_str + str(order_cnt))
                    for actor in subtask.nouns:                                               
                        actors_actions[actor.name].append("BARRIER_" + names_str + str(order_cnt))
                        for verb in subtask.verbs:
                            actors_actions[actor.name].append(verb.name)
                        actors_actions[actor.name].append("SINC_"+ names_str + str(order_cnt))    
                    order_cnt+=1
                else: 
                    actor = task.nouns[0]
                    for verb in task.verbs:
                        actors_actions[actor.name].append(verb.name)
                    for verb in subtask.verbs:
                        actors_actions[actor.name].append(verb.name)
                continue
            
            #direct order
            #one action directly after another
            if subtask_prep.name in after_completing_markers:
                actors = list(set(task.nouns + subtask.nouns))
                names_str = print_names(actors)
                for actor in task.nouns:                                               
                    actors_actions[actor.name].append("BARRIER_" + names_str + str(order_cnt))
                    for verb in task.verbs:
                        actors_actions[actor.name].append(verb.name)
                for actor in subtask.nouns:                                               
                    actors_actions[actor.name].append(subtask.verbs[0].name)
                    actors_actions[actor.name].append("BARRIER_" + names_str + str(order_cnt))
                order_cnt+=1
                continue
            
            #direct order
            #one action directly before another
            if subtask_prep.name == "before":
                actors = list(set(task.nouns + subtask.nouns))
                names_str = print_names(actors)
                for actor in task.nouns: 
                    for verb in task.verbs:
                        actors_actions[actor.name].append(verb.name)
                    actors_actions[actor.name].append("BARRIER_" + names_str + str(order_cnt))                          

                for actor in subtask.nouns:                                               
                    actors_actions[actor.name].append("BARRIER_" + names_str + str(order_cnt))
                    actors_actions[actor.name].append(subtask.verbs[0].name)
                order_cnt+=1
                continue

        if len(task.nouns) > 1:
            #has OR between verbs     
            if (is_preposition_exist(task.verbs, choice_markers)):
                verbs_str = print_names(task.verbs)
                for actor in task.nouns:                             
                    if actor.name not in actors_actions:
                        actors_actions[actor.name].append("ORVERB_"+ verbs_str  + str(order_cnt))                                  
            else:        
                for verb in task.verbs:
                    #task choice
                    if (is_preposition_exist(task.nouns, choice_markers)): #gather actors groups if there is OR 
                        actors_before = []
                        groups = ""
                        for actor in task.nouns:
                            if actor.name not in actors_actions:
                                actors_before.append(actor)
                            if (is_this_or(actor)):
                                if (is_preposition_exist(actors_before, and_markers)):
                                    names_str = print_names(actors_before)
                                    for a in actors_before:
                                        actors_actions[a.name].append("ORNOUN_" + names_str + str(order_cnt))
                                        actors_actions[a.name].append(verb.name)
                                else:
                                    for a in actors_before:
                                        actors_actions[a.name].append("ORNOUN_" + a.name + "_" + str(order_cnt))
                                        actors_actions[a.name].append(verb.name) 
                                actors_before = []                           
                        names_str = print_names(actors_before)
                        for a in actors_before:
                            actors_actions[a.name].append("ORNOUN_" + names_str + str(order_cnt))
                            actors_actions[a.name].append(verb.name)
                        print(groups)
                        order_cnt+=1

 
                    #no choice
                    else:
                        names_str = print_names(task.nouns)
                        for actor in task.nouns:                                               
                            actors_actions[actor.name].append("BARRIER_" + names_str + str(order_cnt))
                            actors_actions[actor.name].append(verb.name)
                            actors_actions[actor.name].append("SINC_"+ names_str + str(order_cnt))
                        order_cnt+=1
        else:
            if (is_preposition_exist(task.verbs, choice_markers)):
                verbs_str = print_names(task.verbs)
                for actor in task.nouns:                             
                    if actor.name not in actors_actions:
                        actors_actions[actor.name] = []
                        actors_actions[actor.name].append("ORVERB_"+ verbs_str  + str(order_cnt))
            else:
                actor = task.nouns[0]
                for verb in task.verbs:
                    actors_actions[actor.name].append(verb.name)
    print(actors_actions)
    return actors_actions