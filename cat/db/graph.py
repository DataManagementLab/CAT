from collections import defaultdict
from typing import List


class DependencyVertex:
    def __init__(self, table_name: str, table_alias: str = None):
        self.table_name = table_name
        self.table_alias = table_alias if table_alias else table_name

    def __eq__(self, other):
        if not isinstance(other, DependencyVertex):
            return False
        return self.table_name == other.table_name and self.table_alias == other.table_alias

    def __str__(self):
        return f'{self.table_alias}'


class DependencyEdge:
    def __init__(self, from_table: str, to_table: str, from_column: str, to_column: str, from_alias: str = None, to_alias: str = None):
        self.from_table = from_table
        self.to_table = to_table
        self.from_alias = from_alias if from_alias else from_table
        self.to_alias = to_alias if to_alias else to_table
        self.from_column = from_column
        self.to_column = to_column

    def __eq__(self, other):
        if not isinstance(other, DependencyEdge):
            return False
        return self.from_table == other.from_table and self.to_table == other.to_table and \
               self.from_column == other.from_column and self.to_column == other.to_column and \
               self.from_alias == other.from_alias and self.to_alias == other.to_alias

    def __str__(self):
        return f'{self.from_alias} -> {self.to_alias}'

    def get_neighbor(self, table, directed=False):
        if self.to_table != table:
            return self.to_table
        elif not directed and self.from_table != table:
            return self.from_table
        return None


class DependencyGraph:
    def __init__(self, vertices: List[DependencyVertex] = [], edges: List[DependencyEdge] = [], directed=False):
        self.vertices = vertices
        self.edges = edges
        self.adjacents = defaultdict(list)
        self.directed = directed

    def __str__(self):
        return f'{len(self.vertices)} tables, {len(self.edges)} FK relations'

    def add_vertex(self, vertex: DependencyVertex):
        if vertex not in self.vertices:
            self.vertices.append(vertex)

    def add_edge(self, edge: DependencyEdge):
        if edge not in self.edges:
            self.edges.append(edge)
            if edge.to_alias not in self.adjacents[edge.from_alias]:
                self.adjacents[edge.from_alias].append(edge.to_alias)
                if not self.directed and edge.from_alias not in self.adjacents[edge.to_alias]:
                    self.adjacents[edge.to_alias].append(edge.from_alias)

    def get_edges(self, vertex_table: str) -> List[DependencyEdge]:
        edges = []
        for edge in self.edges:
            if edge.from_table == vertex_table:
                edges.append(edge)
            if not self.directed and edge.to_table == vertex_table:
                edges.append(edge)
        return edges

    def get_best_dependency_path(self, start_table, end_table, known_tables=[]) -> List[List[str]]:
        paths = self.get_dependencies_paths(start_table, end_table)
        required_tables = dict([(i, (set(path) - set(known_tables))) for i, path in enumerate(paths)])
        if not required_tables:
            return []
        least_required = min(required_tables.items(), key=lambda rt: len(rt[1]))
        if least_required:
            return list(paths[least_required[0]])

    def get_dependencies_paths(self, from_table: str, to_table: str, path: List[str] = []) -> List[str]:
        path = path + [from_table]
        if from_table == to_table:
            return [path]
        if from_table not in self.adjacents.keys():
            return []
        paths = []
        for vertex in self.adjacents[from_table]:
            if vertex not in path:
                new_paths = self.get_dependencies_paths(vertex, to_table, path)
                for new_path in new_paths:
                    paths.append(new_path)
        return paths

    def get_join_candidates(self, tables: List[str], mapping_tables: List[str] = [], directed=True) -> List[str]:
        candidates = []
        for table in tables:
            edges = self.get_edges(table)
            for edge in edges:
                neighbor = edge.get_neighbor(table, directed)
                if not neighbor:
                    continue
                # take an extra hop for mapping tables
                if neighbor in mapping_tables:
                    mapping_candidates = self.get_join_candidates([neighbor], mapping_tables, directed=False)
                    for candidate in mapping_candidates:
                        if candidate not in tables + candidates:
                            candidates.append(candidate)
                    continue
                # if we have multiple edges to a table on different join columns add the table/column prefix
                if edge.to_table in [other.to_table for other in edges if other.from_column != edge.from_column]:
                    candidate = f'{table}__{edge.from_column}___{neighbor}'
                    if candidate not in tables + candidates:
                        candidates.append(candidate)
                    continue
                if neighbor not in tables + candidates:
                    candidates.append(neighbor)
        return candidates