from flask import Flask, request, jsonify
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64
from flask_cors import CORS

# defini l'application de flask pour etre appellee par CORS
app = Flask(__name__)
# cette ligne permet seulment les requetes arrivant du port 3000 de passer sans etre blocker par CORS
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

def construire_graphe(data):
    """
    Construct the graph from the provided data.
    """
    G = nx.DiGraph()
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    # Add nodes
    G.add_nodes_from(nodes)

    # Add edges with capacities
    for edge in edges:
        G.add_edge(edge['source'], edge['target'], capacity=edge['capacity'], flow=0)

    return G

def trouver_chemin_ameliore(G, source, puits):
    chemins = {source: []}
    pile = [(source, float('inf'))]

    while pile:
        u, flux_actuel = pile.pop()
        for v in G[u]:
            capacite = G[u][v]['capacity'] - G[u][v]['flow']
            if capacite > 0 and v not in chemins:
                chemins[v] = chemins[u] + [(u, v)]
                flux_min = min(flux_actuel, capacite)
                if v == puits:
                    return chemins[v], flux_min
                pile.append((v, flux_min))
    return None, 0

def ford_fulkerson(G, source, sink):
    """
    Ford-Fulkerson algorithm to calculate max flow. Returns the total flow
    and a list of graph states at each iteration.
    """
    flow_total = 0
    graph_states = []  # To store graph states

    while True:
        # Find an augmenting path
        path, flow = trouver_chemin_ameliore(G, source, sink)
        if flow == 0:
            break  # No more augmenting paths

        flow_total += flow

        # Update flows along the path
        for u, v in path:
            G[u][v]['flow'] += flow

        # Save the current state of the graph
        graph_image = afficher_graphe(G)
        graph_states.append(graph_image)

    return flow_total, graph_states


def afficher_graphe(G):
    """
    Generate a graph visualization and return it as a base64 string.
    """
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(G)
    couleurs = ['blue' for _ in G.edges]
    nx.draw(G, pos, with_labels=True, edge_color=couleurs, node_size=700, font_size=10, arrows=True)
    etiquettes = {(u, v): f"{G[u][v]['flow']}/{G[u][v]['capacity']}" for u, v in G.edges}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=etiquettes)
    
    # Save the graph to a BytesIO buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    graph_image = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    return graph_image

@app.route('/calculate-max-flow', methods=['POST'])
def calculate_max_flow():
    """
    API endpoint to calculate max flow and return results.
    """
    data = request.json
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    source = data.get("source")
    sink = data.get("sink")

    if not nodes or not edges or not source or not sink:
        return jsonify({'error': 'Invalid input data'}), 400

    G = construire_graphe(data)

    # Run Ford-Fulkerson algorithm
    max_flow, graph_states = ford_fulkerson(G, source, sink)

    return jsonify({'maxFlow': max_flow, 'graphImages': graph_states})


if __name__ == '__main__':
    app.run(debug=True)
