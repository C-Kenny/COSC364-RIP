import sys
"""
Author: Carl Kenny
Date:   19/04/2015
Prog:   Modified Bellman-Ford helper for RIP. Each router or host is assumed to
        keep all information about all of the destinations within the system.

        The algorithm bases itself on the table in each router listing, via the
        metric heuristic. This metric in simple networks is the number of 'hops',
        in a complex scenario, delay/cost etc might be used instead.
"""
MAX = sys.maxint

def bellmanFord(vertices, edges, source):
    """
    Fills distance and predecessor with shortest-path information
    :param vertices:    list, part of graph
    :param edges:       list, list of tuples 
    :param source:      int, current vertex
    """
    distance = []
    predecessor = []

    # init graph
    for i, elem in enumerate(vertices):
        if elem == source:
            distance[i] = 0  # cost to self is 0...
        else:
            distance[i] = MAX
            predecessor[i] = None

    # relax edges
    for i in range(1, len(vertices) - 1):
        # (u, v, w), tribute to Tad
        for j in edges:
            u, v, w = j
            if (distance[u] + w) < distance[v]:
                distance[v] = distance[u] + w
                predecessor[v] = u

    # check for negative weight cycles
    for i in edges:
        u, v, w = i
        if (distance[u] + w) < distance[v]:
            return ValueError("Negative-weight cycle was found. Fix config\n")

    return distance, predecessor


