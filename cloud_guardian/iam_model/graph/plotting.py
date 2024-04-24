from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from cloud_guardian.iam_model.graph.graph import IAMGraph
from loguru import logger


def calculate_figure_size(graph):
    """Calculate the figure size based on the number of nodes."""
    total_nodes = len(graph.nodes())
    base_size = 8  # Base size for a moderate number of nodes
    scaling_factor = max(1, total_nodes / 50)
    return base_size * scaling_factor, base_size * scaling_factor


def calculate_positions(graph, nodes):
    """Calculate positions for graph nodes in a circular layout."""
    total_nodes = len(nodes)
    angle_between_nodes = 2 * np.pi / total_nodes
    pos = {}
    for idx, node_id in enumerate(nodes.keys()):
        angle = angle_between_nodes * idx
        pos[node_id] = (np.cos(angle), np.sin(angle))
    return pos


def draw_nodes(graph, positions, entity_nodes, resource_nodes):
    """Draw nodes on the graph."""
    nx.draw_networkx_nodes(
        graph,
        positions,
        nodelist=list(entity_nodes.keys()),
        node_color="#add8e6",
        node_size=300,
    )
    nx.draw_networkx_nodes(
        graph,
        positions,
        nodelist=list(resource_nodes.keys()),
        node_color="#ffb6c1",
        node_size=300,
    )


def draw_labels(graph, positions, labels):
    """Draw labels slightly above the nodes."""
    label_pos = {node_id: (pos[0], pos[1] + 0.05) for node_id, pos in positions.items()}
    nx.draw_networkx_labels(
        graph, label_pos, labels=labels, font_size=10, verticalalignment="bottom"
    )


def draw_edges(graph, positions, edge_styles):
    """Draw edges with customized colors and styles."""
    edge_colors = {
        "can_assume_role": ("black", "-"),
        "is_part_of": ("black", "-"),
        "permission": ("red", "-"),
    }
    for etype, edges in edge_styles.items():
        color, style = edge_colors.get(etype, ("red", "-"))
        nx.draw_networkx_edges(
            graph,
            positions,
            edgelist=[(e[0], e[1]) for e in edges],
            edge_color=color,
            arrows=True,
            style=style,
        )


def draw_edge_labels(graph, positions, edge_styles):
    """Draw edge labels."""
    edge_labels = {(e[0], e[1]): e[2]["label"] for e in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(
        graph, positions, edge_labels=edge_labels, label_pos=0.5, font_size=6
    )


def classify_edges(graph):
    """Classify edges by their types for styling purposes."""
    edge_styles = {}
    for edge in graph.edges(data=True):
        etype = edge[2]["label"]
        edge_styles.setdefault(etype, []).append(edge)
    return edge_styles


def create_legends(edge_styles):
    """Create legends for node and edge types."""
    edge_colors = {
        "can_assume_role": "black",
        "is_part_of": "black",
        "permission": "red",
    }
    legend_elements = [
        plt.Line2D(
            [0],
            [0],
            color=color,
            marker=">",
            markersize=3,
            linestyle="-",
            label=etype.capitalize(),
        )
        for etype, color in edge_colors.items()
        if etype in edge_styles
    ]
    plt.legend(handles=legend_elements, title="Edge Types", loc="upper right")


def save_graph_pdf(iam_graph: IAMGraph, file_path: Path):
    file_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=calculate_figure_size(iam_graph.graph))
    entities = iam_graph.get_nodes(filter_types=["user", "group", "role", "service"])
    resources = iam_graph.get_nodes(filter_types=["resource"])
    entity_nodes = {node[0]: node[1]["label"] for node in entities}
    resource_nodes = {node[0]: node[1]["label"] for node in resources}
    positions = calculate_positions(iam_graph.graph, {**entity_nodes, **resource_nodes})

    draw_nodes(iam_graph.graph, positions, entity_nodes, resource_nodes)
    draw_labels(iam_graph.graph, positions, {**entity_nodes, **resource_nodes})

    edge_styles = classify_edges(iam_graph.graph)
    draw_edges(iam_graph.graph, positions, edge_styles)
    draw_edge_labels(iam_graph.graph, positions, edge_styles)

    # Add node and edge type legends
    create_legends(edge_styles)

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(file_path, format="pdf")
    logger.info(f"Saved graph to {file_path}")
    plt.close()
