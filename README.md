# Petri Net Generator from Natural Language

This project provides a tool that converts natural language commands into Petri nets by analyzing sentence structure using spaCy and visualizing actor/action sequences. The tool is useful for modeling task execution plans for multi-agent systems in robotics.

---

1. User input (ML command) is entered via the GUI.
2. The input is parsed using spaCy.
3. Execution trace is extracted using NLP and custom rules.
4. A Petri net is generated and drawn using the extracted information.
5. Output includes:
   - `petri_net.png` – visualization of the Petri net
   - `petri_net.dot` – DOT file format for the graph
   - `petri_net.json` – JSON format 
   - `dependency_tree.svg` – syntax tree of the input

