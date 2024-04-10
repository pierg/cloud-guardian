from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from cloud_guardian.iam_model.graph.graph import IAMGraph


def calculate_figure_size(graph):
    """Calculate the figure size based on the number of nodes."""
    total_nodes = len(graph.nodes())
    base_size = 8  # Base size for a moderate number of nodes
    # Adjust the division factor as needed
    scaling_factor = max(1, total_nodes / 50)
    figure_width = base_size * scaling_factor
    figure_height = base_size * scaling_factor
    return figure_width, figure_height


def save_graph_pdf(iam_graph: IAMGraph, file_path: Path):
    plt.figure(figsize=calculate_figure_size(iam_graph.graph))

    # Access the graph from IAMGraph instance
    iam_graph.graph

    # Get nodes by type
    entities = iam_graph.get_nodes_by_type("entity")
    resources = iam_graph.get_nodes_by_type("resource")

    # Calculate positions for a circular layout
    total_nodes = len(entities) + len(resources)
    angle_between_nodes = 2 * np.pi / total_nodes

    pos = {}
    # Place entities on one half of the circle
    for i, node_id in enumerate(entities):
        angle = angle_between_nodes * i
        pos[node_id] = (np.cos(angle), np.sin(angle))
    # Place resources on the other half of the circle
    offset = len(entities) * angle_between_nodes
    for i, node_id in enumerate(resources):
        angle = offset + angle_between_nodes * i
        pos[node_id] = (np.cos(angle), np.sin(angle))

    # Node labels based on their ID
    node_labels = {node_id: node_id for node_id in iam_graph.graph.nodes()}

    entity_color = "#add8e6"  # Light blue
    resource_color = "#ffb6c1"  # Light red

    # Legend for node types
    entity_legend = plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=entity_color,
        markersize=10,
        label="Entities",
    )
    resource_legend = plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=resource_color,
        markersize=10,
        label="Resources",
    )
    first_legend = plt.legend(
        handles=[entity_legend, resource_legend],
        title="Node Types",
        loc="upper left",
    )
    plt.gca().add_artist(first_legend)  # Add the first legend manually

    # Drawing the nodes with their respective colors
    nx.draw_networkx_nodes(
        iam_graph.graph,
        pos,
        nodelist=entities,
        node_color=entity_color,
        label="Entities",
        node_size=300,
    )
    nx.draw_networkx_nodes(
        iam_graph.graph,
        pos,
        nodelist=resources,
        node_color=resource_color,
        label="Resources",
        node_size=300,
    )

    # Adjust labels to be above nodes
    label_pos = {
        node: (position[0], position[1] + 0.05) for node, position in pos.items()
    }
    nx.draw_networkx_labels(
        iam_graph.graph,
        label_pos,
        labels=node_labels,
        font_size=10,
        verticalalignment="bottom",
    )

    # Draw edges with IAMAction enum values as labels
    edge_labels = {
        (u, v): data["permission"].label
        for u, v, data in iam_graph.graph.edges(data=True)
    }

    deny_edges = []
    other_edges = []
    flow_enabler_edges = []

    for u, v, data in iam_graph.graph.edges(data=True):
        if data["permission"].is_action_denied():
            deny_edges.append((u, v))
        else:
            if data["permission"].is_flow_active():
                flow_enabler_edges.append((u, v))
            else:
                other_edges.append((u, v))

    # Draw flowEnabler edges with red arrows
    nx.draw_networkx_edges(
        iam_graph.graph,
        pos,
        edgelist=flow_enabler_edges,
        edge_color="red",
        arrows=True,
        width=1,
        arrowstyle="->",
    )

    # Draw other edges with black arrows
    nx.draw_networkx_edges(
        iam_graph.graph, pos, edgelist=other_edges, edge_color="black", arrows=True
    )

    # Draw deny edges with dashed lines
    nx.draw_networkx_edges(
        iam_graph.graph,
        pos,
        edgelist=deny_edges,
        edge_color="gray",
        arrows=True,
        style="dashed",
    )

    nx.draw_networkx_edge_labels(
        iam_graph.graph, pos, edge_labels=edge_labels, label_pos=0.5, font_size=6
    )

    # Legend for edge types
    flow_enabler_legend = plt.Line2D(
        [0],
        [0],
        color="red",
        marker=">",
        markersize=3,
        label="Flow Enabler",
    )
    other_legend = plt.Line2D(
        [0],
        [0],
        color="black",
        marker=">",
        markersize=3,
        label="Allowed",
    )
    deny_legend = plt.Line2D(
        [0],
        [0],
        color="gray",
        marker=">",
        markersize=3,
        linestyle="--",
        label="Deny",
    )
    second_legend = plt.legend(
        handles=[flow_enabler_legend, other_legend, deny_legend],
        title="Edge Types",
        loc="upper right",
    )
    plt.gca().add_artist(second_legend)  # Add the second legend manually

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(file_path, format="pdf")
    plt.close()
