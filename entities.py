
#Entities
class Preposition:
    def __init__(self, name, tag=None):
        self.name = name
        self.tag = tag 

    def __str__(self):
        return f"({self.name}, TAG: {self.tag})" if self.tag else f"({self.name})"

    
class Verb:
    def __init__(self, name, preposition=None, tag=None):
        self.name = name
        self.preposition = [preposition] if preposition and not isinstance(preposition, list) else (preposition or [])
        self.tag = tag  

    def __str__(self):
        prepositions = ', '.join(str(p) for p in self.preposition) if self.preposition else ''
        tag_str = f"TAG: {self.tag}" if self.tag else ''
        
        components = [self.name]
        if prepositions:
            components.append(f"Prepositions: {prepositions}")
        if tag_str:
            components.append(tag_str)
        
        return ', '.join(components)


class Noun:
    def __init__(self, name, preposition=None):
        self.name = name
        self.preposition = preposition if isinstance(preposition, list) else [preposition]
    
    def __str__(self):
        if self.preposition:
            p = ', '.join(str(p) for p in self.preposition)
            return f"{self.name}, {p}"
        else:
            return f"{self.name}"

    
class Task:
    def __init__(self, verbs, nouns, subtask=None):
        self.verbs = verbs if isinstance(verbs, list) else [verbs] 
        self.nouns = nouns if isinstance(nouns, list) else [nouns]
        self.subtask = subtask if isinstance(subtask, Task) else None  

    def __str__(self):
        verb_str = ', '.join(str(verb) for verb in self.verbs)
        nouns_str = ', '.join(str(noun) for noun in self.nouns)
        subtask_str = f", Subtask: ({self.subtask})" if self.subtask else ""

        return f"Task(Verbs: [{verb_str}], Nouns: [{nouns_str}]{subtask_str})"

    def get_all_actors(self):
        actors = [noun.name for noun in self.nouns]
        if self.subtask:
            actors.extend(self.subtask.get_all_actors())  
        return actors


