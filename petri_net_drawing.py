
import snakes.plugins
snakes.plugins.load("gv", "snakes.nets", "nets")
from nets import *
import re
from collections import defaultdict
import time
import spacy.displacy as displacy
from tree_analysis import get_parallel_tasks 
from petri_net_converter import draw_petri_net 
from petri_net_converter import save_dependency_tree_as_svg
import spacy
import snakes.plugins
snakes.plugins.load("gv", "snakes.nets", "nets")
from nets import *
import tkinter as tk


class PetriNetApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("800x600")  

        self.entry = tk.Entry(root, width=60, font=("Arial", 14), bd=3, relief="solid")
        self.entry.pack(pady=20)

        self.button = tk.Button(root, text="Draw Petri Net", command=self.on_button_click)
        self.button.pack(pady=5)

        self.output_label = tk.Label(root, text="", font=("Arial", 12))
        self.output_label.pack(pady=20)
        self.nlp = spacy.load("en_core_web_sm")

    def on_button_click(self):
        input_text = self.entry.get()
        self.present_output(input_text)

    def present_output(self, input_text):
        doc = self.nlp(input_text)  
        input_data = get_parallel_tasks(doc)

        self.save_dependency_tree(doc) 
        
        draw_petri_net(input_data)

        output = "Petri Net created.\n"
        current_text = self.output_label.cget("text")
        self.output_label.config(text=current_text + output)

         

    def save_dependency_tree(self, doc, filename="dependency_tree.svg"):
        options = {
            "compact": True,
            "color": "black",
            "bg": "white",
        }

        svg = displacy.render(doc, style="dep", jupyter=False, options=options)
        if not svg or not isinstance(svg, str):
            output = "Error: displacy.render() returned None.\n"
            current_text = self.output_label.cget("text")
            self.output_label.config(text=current_text + output)
            raise ValueError("Error: displacy.render() returned None.")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(svg)

        output = f"Dependency tree saved as {filename}.\n"
        current_text = self.output_label.cget("text")
        self.output_label.config(text=current_text + output)
 
