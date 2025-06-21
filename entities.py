
#Entities
class Particle:
    """
    Represents a particle used in a command.
    
    Attributes:
        name (str): The actual particle text.
        tag (str, optional): An optional tag for additional metadata or categorization.
    """
    
    def __init__(self, name, tag=None):
        self.name = name
        self.tag = tag 

    def __str__(self):
        return f"({self.name}, TAG: {self.tag})" if self.tag else f"({self.name})"

    
class Action:
    """
    Represents an action and its associated prepositions and tag.

    Attributes:
        name (str): The action itself
        preposition (list of Preposition): Prepositions linked with this action
        tag (str, optional)
    """
    def __init__(self, name, particle=None, tag=None):
        self.name = name
        self.particle = [particle] if particle and not isinstance(particle, list) else (particle or [])
        self.tag = tag  

    def __str__(self):
        particles = ', '.join(str(p) for p in self.particle) if self.particle else ''
        tag_str = f"TAG: {self.tag}" if self.tag else ''
        
        components = [self.name]
        if particles:
            components.append(f"particles: {particles}")
        if tag_str:
            components.append(tag_str)
        
        return ', '.join(components)


class Actor:
    """
    Represents an actor entity in the command, possibly associated with a preposition.

    Attributes:
        name (str): The actor itself
        preposition (list of Preposition): Prepositions linked with this actor.
    """
    def __init__(self, name, particle=None):
        self.name = name
        self.particle = particle if isinstance(particle, list) else [particle]
    
    def __str__(self):
        if self.particle:
            p = ', '.join(str(p) for p in self.particle)
            return f"{self.name}, {p}"
        else:
            return f"{self.name}"

    
class Task:
    """
    Represents a high-level instruction composed of actions and actors, 
    and optionally containing a nested subtask.

    Attributes:
        actions (list of Action): Actions involved in the task.
        actors (list of Actor): Actors involved in the task.
        subtask (Task, optional): An optional nested Task representing a sub-action.
    """
    def __init__(self, actions, actors, subtask=None):
        self.actions = actions if isinstance(actions, list) else [actions] 
        self.actors = actors if isinstance(actors, list) else [actors]
        self.subtask = subtask if isinstance(subtask, Task) else None  

    def __str__(self):
        action_str = ', '.join(str(action) for action in self.actions)
        actors_str = ', '.join(str(actor) for actor in self.actors)
        subtask_str = f", Subtask: ({self.subtask})" if self.subtask else ""

        return f"Task(Actions: [{action_str}], Actors: [{actors_str}]{subtask_str})"

    def get_all_actors(self):
        actors = [actor.name for actor in self.actors]
        if self.subtask:
            actors.extend(self.subtask.get_all_actors())  
        return actors


