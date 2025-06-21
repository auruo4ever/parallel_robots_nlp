import pydot
import json

def dot_to_json(dot_data, output_file="petri_net.json"):
    graphs = pydot.graph_from_dot_data(dot_data)
    if not graphs:
        print("No graph could be parsed.")
        return
    
    graph = graphs[0]
    nodes = []
    edges = []


    def clean_label(label):
        if label:
            label = label.strip('"')
            if '\\n' in label:
                return label.split('\\n')[0]
            elif '\n' in label:
                return label.split('\n')[0]
            return label
        return None


    def extract_nodes_edges(subgraph):
        for node in subgraph.get_nodes():
            name = node.get_name().strip('"')
            if name in ('node', 'graph'):
                continue  # skip default nodes
            raw_label = node.get_label()
            label = clean_label(raw_label)
            shape = node.get_shape()
            node_type = "transition" if shape == "rectangle" else "place"
            nodes.append({"id": name, "label": label, "type": node_type})
        
        for edge in subgraph.get_edges():
            src = edge.get_source().strip('"')
            dst = edge.get_destination().strip('"')
            edges.append({"source": src, "target": dst})

    subgraphs = graph.get_subgraphs()
    if not subgraphs:
        print("No subgraph found.")
        return

    for subgraph in subgraphs:
        extract_nodes_edges(subgraph)

    output = {"nodes": nodes, "edges": edges}

    if output_file:
        with open(output_file, "w") as f:
            json.dump(output, f, indent=4)
    else:
        print(json.dumps(output, indent=4))
