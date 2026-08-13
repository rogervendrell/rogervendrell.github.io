import pandas as pd
import ast
import networkx as nx
import plotly.graph_objects as go
import webbrowser
import os



def main():
    df = pd.read_csv("../graph/graph.csv", sep=';')

    G = nx.Graph()

    for _, row in df.iterrows():
        node = row['node']
        neighbors = ast.literal_eval(row['1_hop_neighbours'])
        for neighbor in neighbors:
            G.add_edge(node, neighbor)

    pos = nx.spring_layout(G, seed=42)

    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='gray'),
        hoverinfo='none',
        mode='lines'
    )

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[str(n) for n in G.nodes()],
        textposition='top center',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color='skyblue',
            size=20,
            line=dict(width=2)
        )
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(
                text='Interactive Graph',
                font=dict(size=16)
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
        )
    )

    fig.write_html("graph_visualisation.html")
    fig.show()


if __name__ == '__main__':
    if os.path.exists("graph_visualisation.html"):
        webbrowser.open("graph_visualisation.html")
    else:
        main()
