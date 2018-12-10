from __future__ import print_function

import sys
from functools import total_ordering

from pyparsing import *
import numpy as np

__all__ = [ "Tree", "Edge", "NewickParser", "get_tree", "tree_distance" ]

def indent( s ):
    return "\n".join( "    " + line for line in s.split( "\n" ) )

def print_( p, s ):
    print(p, type(s), s)
    return s

@total_ordering
class Tree( object ):
    def __init__( self, label, edges=None ):
        self.label = label
        self.edges = edges
    def pretty( self ):
        if self.edges:
            return "Tree( '%s',\n%s\n)" % ( self.label, indent( "\n".join( repr( edge ) for edge in self.edges ) ) )
        else:
            return "Tree( '%s' )" % self.label
    def __lt__(self, other):
        return self.__dict__ < other.__dict__
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
    def __repr__( self ):
        return "Tree( %s, %s )" % ( repr( self.label ), repr( self.edges ) )

@total_ordering
class Edge( object ):
    def __init__( self, length, tip ):
        self.length = length
        self.tip = tip
    def pretty( self ):
        return "Edge( %s, \n%s\n)" % ( repr( self.length ), indent( repr( self.tip ) ) )
    def __lt__(self, other):
        return self.__dict__ < other.__dict__
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
    def __repr__( self ):
        return "Edge( %s, %s )" % ( repr( self.length ), repr( self.tip ) )

def create_parser():
    """
    Create a 'pyparsing' parser for newick format trees roughly based on the
    grammar here:
        http://evolution.genetics.washington.edu/phylip/newick_doc.html

    Problems:
        - Is a single leaf a valid tree?
        - Branch length on root? Doesn't make sense to me, and forces the root
          to be an edge.
    """
    # Basic tokens
    real = Combine( Word( "+-" + nums, nums ) +
                    Optional( "." + Optional( Word( nums ) ) ) +
                    Optional( CaselessLiteral( "E" ) + Word( "+-" + nums, nums ) ) )
    lpar = Suppress( "(" )
    rpar = Suppress( ")" )
    colon = Suppress( ":" )
    semi = Suppress( ";" )
    quot = Suppress( "'" )
    # Labels are either unquoted or single quoted, if unquoted underscores will be replaced with spaces
    quoted_label = QuotedString( "'", None, "''" ).setParseAction( lambda s, l, t: t[0] )
    simple_label = Word( alphas + nums + "_." ).setParseAction( lambda s, l, t: t[0].replace( "_", " " ) )
    label = quoted_label | simple_label
    # Branch length is a real number (note though that exponents are not in the spec!)
    branch_length = real.setParseAction( lambda s, l, t: float( t[0] ) )
    # Need to forward declare this due to circularity
    node_list = Forward()
    # A node might have an list of edges (for a subtree), a label, and/or a branch length
    node = ( Optional( node_list, None ) + Optional( label, "" ) + Optional( colon + branch_length, None ) ) \
        .setParseAction( lambda s, l, t: Edge( t[2], Tree( t[1] or None, t[0] ) ) )
    node_list << ( lpar + delimitedList( node ) + rpar ) \
        .setParseAction( lambda s, l, t: [ t.asList() ] )
    # The root cannot have a branch length
    tree = ( node_list + Optional( label, "" ) + semi )\
        .setParseAction( lambda s, l, t: Tree( t[1] or None, t[0] ) )
    # Return the outermost element
    return tree

class NewickParser( object ):
    """
    Class wrapping a parser for building Trees from newick format strings
    """
    def __init__( self ):
        self.parser = create_parser()
    def parse_string( self, s ):
        return self.parser.parseString( s )[0]

def get_tree(ts):
    newick_parser = NewickParser()

    root_node = newick_parser.parse_string(ts)

    return root_node


def _find_path(node, label, path=None):
    if path is None:
        path = []

    if node.label == label:
        return path

    edges = node.edges or []
    for n, child_node in enumerate(edge.tip for edge in edges):
        result = _find_path(child_node, label, path + [n])
        if result is not None:
            return result

    return None

def _walk_path(node, path):
    distance = 0.0
    for edge_no in path:
        edge = node.edges[edge_no]
        distance += edge.length
        node = edge.tip

    return node, distance


def tree_distance(root_node, label_one, label_two):
    path_one = _find_path(root_node, label_one)
    path_two = _find_path(root_node, label_two)
    common_path = []
    for n in xrange(min(len(path_one), len(path_two))):
        if path_one[n] != path_two[n]:
            break
        common_path.append(path_one[n])
    path_one = path_one[len(common_path):]
    path_two = path_two[len(common_path):]

    common_node, common_distance = _walk_path(root_node, common_path)
    node_one, distance_one = _walk_path(common_node, path_one)
    node_two, distance_two = _walk_path(common_node, path_two)

    assert node_one.label == label_one
    assert node_two.label == label_two

    return distance_one + distance_two

def main():
    with open(sys.argv[1]) as f:
        root_node = get_tree(f.read())


if __name__ == '__main__':
    main()
