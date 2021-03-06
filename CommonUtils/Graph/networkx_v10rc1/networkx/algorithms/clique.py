"""
=======
Cliques
=======

Find and manipulate cliques of graphs.

Note that finding the largest clique of a graph has been
shown to be an NP-complete problem; the algorithms here
could take a long time to run. 

http://en.wikipedia.org/wiki/Clique_problem

"""
__author__ = """Dan Schult (dschult@colgate.edu)"""
#    Copyright (C) 2004-2008 by 
#    Aric Hagberg <hagberg@lanl.gov>
#    Dan Schult <dschult@colgate.edu>
#    Pieter Swart <swart@lanl.gov>
#    Distributed under the terms of the GNU Lesser General Public License
#    http://www.gnu.org/copyleft/lesser.html


__all__ = ['find_cliques', 'find_cliques_recursive', 'make_max_clique_graph',
           'make_clique_bipartite' ,'graph_clique_number',
           'graph_number_of_cliques', 'node_clique_number',
           'number_of_cliques', 'cliques_containing_node',
           'project_down', 'project_up']


import networkx

def find_cliques(G):
    """
    Search for all maximal cliques in a graph.
 
    This algorithm searches for maximal cliques in a graph.
    maximal cliques are the largest complete subgraph containing
    a given point.  The largest maximal clique is sometimes called
    the maximum clique.
 
    This implementation is a generator of lists each
    of which contains the members of a maximal clique.
    To obtain a list of cliques, use list(find_cliques(G)).
    The method essentially unrolls the recursion used in
    the references to avoid issues of recursion stack depth.
    
    See Also
    --------
    find_cliques_recursive : A recursive version of the same algorithm

    Reference::
 
    Based on the algorithm published by Bron & Kerbosch (1973)
        http://doi.acm.org/10.1145/362342.362367
    as adapated by Tomita, Tanaka and Takahashi (2006)
        http://dx.doi.org/10.1016/j.tcs.2006.06.015
    and discussed in Cazals and Karande (2008)
        http://dx.doi.org/10.1016/j.tcs.2008.05.010
 
    """
    # Cache nbrs and find first pivot (highest degree)
    maxconn=-1
    nnbrs={}
    pivotnbrs=set() # handle empty graph
    for n,nbrs in G.adjacency_iter():
        conn = len(nbrs)
        if conn > maxconn:
            nnbrs[n] = pivotnbrs = set(nbrs)
            maxconn = conn
        else:
            nnbrs[n] = set(nbrs)
    # Initial setup
    cand=set(nnbrs)
    smallcand = cand - pivotnbrs
    done=set()
    stack=[]
    clique_so_far=[]
    # Start main loop
    while smallcand or stack:
        try:
            # Any nodes left to check?
            n=smallcand.pop()
        except KeyError:
            # back out clique_so_far
            cand,done,smallcand = stack.pop()
            clique_so_far.pop()
            continue
        # Add next node to clique
        clique_so_far.append(n)
        cand.remove(n)
        done.add(n)
        nn=nnbrs[n]
        new_cand = cand & nn
        new_done = done & nn
        # check if we have more to search
        if not new_cand: 
            if not new_done:
                # Found a clique!
                yield clique_so_far[:]
            clique_so_far.pop()
            continue
        # Shortcut--only one node left!
        if not new_done and len(new_cand)==1:
            yield clique_so_far + list(new_cand)
            clique_so_far.pop()
            continue
        # find pivot node (max connected in cand)
        # look in done nodes first
        numb_cand=len(new_cand)
        maxconndone=-1
        for n in new_done:
            cn = new_cand & nnbrs[n]
            conn=len(cn)
            if conn > maxconndone:
                pivotdonenbrs=cn
                maxconndone=conn
                if maxconndone==numb_cand:
                    break
        # Shortcut--this part of tree already searched
        if maxconndone == numb_cand:  
            clique_so_far.pop()
            continue
        # still finding pivot node
        # look in cand nodes second
        maxconn=-1
        for n in new_cand:
            cn = new_cand & nnbrs[n]
            conn=len(cn)
            if conn > maxconn:
                pivotnbrs=cn
                maxconn=conn
                if maxconn == numb_cand-1:
                    break
        # pivot node is max connected in cand from done or cand
        if maxconndone > maxconn:
            pivotnbrs = pivotdonenbrs
        # save search status for later backout
        stack.append( (cand, done, smallcand) )
        cand=new_cand
        done=new_done
        smallcand = cand - pivotnbrs


def find_cliques_recursive(G):
    """
    Recursive search for all maximal cliques in a graph.
 
    This algorithm searches for maximal cliques in a graph.
    Maximal cliques are the largest complete subgraph containing
    a given point.  The largest maximal clique is sometimes called
    the maximum clique.
 
    This implementation returns a list of lists each of
    which contains the members of a maximal clique.
    
    See Also
    --------
    find_cliques : An nonrecursive version of the same algorithm

    Reference::
 
    Based on the algorithm published by Bron & Kerbosch (1973)
        http://doi.acm.org/10.1145/362342.362367
    as adapated by Tomita, Tanaka and Takahashi (2006)
        http://dx.doi.org/10.1016/j.tcs.2006.06.015
    and discussed in Cazals and Karande (2008)
        http://dx.doi.org/10.1016/j.tcs.2008.05.010
 
    """
    nnbrs={}
    for n,nbrs in G.adjacency_iter():
        nnbrs[n]=set(nbrs)
    if not nnbrs: return [] # empty graph
    cand=set(nnbrs)
    done=set()
    clique_so_far=[]
    cliques=[]
    _extend(nnbrs,cand,done,clique_so_far,cliques)
    return cliques

def _extend(nnbrs,cand,done,so_far,cliques):
    # find pivot node (max connections in cand)
    maxconn=-1
    numb_cand=len(cand)
    for n in done:
        cn = cand & nnbrs[n]
        conn=len(cn)
        if conn > maxconn:
            pivotnbrs=cn
            maxconn=conn
            if conn==numb_cand:
                # All possible cliques already found
                return
    for n in cand:
        cn = cand & nnbrs[n]
        conn=len(cn)
        if conn > maxconn:
            pivotnbrs=cn
            maxconn=conn
    # Use pivot to reduce number of nodes to examine
    smallercand = cand - pivotnbrs
    for n in smallercand:
        cand.remove(n)
        so_far.append(n)
        nn=nnbrs[n]
        new_cand=cand & nn
        new_done=done & nn
        if not new_cand and not new_done:
            # Found the clique
            cliques.append(so_far[:])
        elif not new_done and len(new_cand) is 1:
            # shortcut if only one node left
            cliques.append(so_far+list(new_cand))
        else:
            _extend(nnbrs, new_cand, new_done, so_far, cliques)
        done.add(so_far.pop())


def make_max_clique_graph(G,create_using=None,name=None):
    """ Create the maximal clique graph of a graph. 
   
    Finds the maximal cliques and treats these as nodes.
    The nodes are connected if they have common members in 
    the original graph.  Theory has done a lot with clique
    graphs, but I haven't seen much on maximal clique graphs.

    Notes
    -----
    This should be the same as make_clique_bipartite followed
    by project_up, but it saves all the intermediate steps.
    """
    cliq=map(set,find_cliques(G))
    size=len(cliq)
    if create_using:
        B=create_using
        B.clear()
    else:
        B=networkx.Graph()
    if name is not None:
        B.name=name

    for i,cl in enumerate(cliq):
        B.add_node(i+1)
        for j,other_cl in enumerate(cliq[:i]):
            # if not cl.isdisjoint(other_cl): #Requires 2.6
            intersect=cl & other_cl
            if intersect:     # Not empty 
                B.add_edge(i+1,j+1)
    return B

def make_clique_bipartite(G,fpos=None,create_using=None,name=None):
    """ Create a bipartite clique graph from a graph G. 
   
    Nodes of G are retained as the "bottom nodes" of B and 
    cliques of G become "top nodes" of B.
    Edges are present if a bottom node belongs to the clique 
    represented by the top node.
 
    Returns a Graph with additional attribute dict B.node_type
    which is keyed by nodes to "Bottom" or "Top" appropriately.

    if fpos is not None, a second additional attribute dict B.pos
    is created to hold the position tuple of each node for viewing
    the bipartite graph.

    """
    cliq=list(find_cliques(G))
    if create_using:
        B=create_using
        B.clear()
    else:
        B=networkx.Graph()
    if name is not None:
        B.name=name

    B.add_nodes_from(G)
    B.node_type={}   # New Attribute for B
    for n in B:
        B.node_type[n]="Bottom"
 
    if fpos:
       B.pos={}     # New Attribute for B
       delta_cpos=1./len(cliq)
       delta_ppos=1./G.order()
       cpos=0.
       ppos=0.
    for i,cl in enumerate(cliq):
       name= -i-1   # Top nodes get negative names
       B.add_node(name)
       B.node_type[name]="Top"
       if fpos:
          if name not in B.pos:
             B.pos[name]=(0.2,cpos)
             cpos +=delta_cpos
       for v in cl:
          B.add_edge(name,v)
          if fpos is not None:
             if v not in B.pos:
                B.pos[v]=(0.8,ppos)
                ppos +=delta_ppos
    return B
   
def project_down(B,create_using=None,name=None):
    """Project a bipartite graph B down onto its "bottom nodes". 
    
    The nodes retain their names and are connected if they
    share a common top node in the bipartite graph.

    Returns a Graph.
    """
    if create_using:
        G=create_using
        G.clear()
    else:
        G=networkx.Graph()
    if name is not None:
        G.name=name

    for v,Bvnbrs in B.adjacency_iter():
       if B.node_type[v]=="Bottom":
          G.add_node(v)
          for cv in Bvnbrs:
             G.add_edges_from([(v,u) for u in B[cv] if u!=v])
    return G
 
def project_up(B,create_using=None,name=None):
    """ Project a bipartite graph B down onto its "bottom nodes".
    
    The nodes retain their names and are connected if they
    share a common Bottom Node in the Bipartite Graph.

    Returns a Graph.
    """
    if create_using:
        G=create_using
        G.clear()
    else:
        G=networkx.Graph()
    if name is not None:
        G.name=name

    for v,Bvnbrs in B.adjacency_iter():
       if B.node_type[v]=="Top":
          vname= -v   #Change sign of name for Top Nodes
          G.add_node(vname)
          for cv in Bvnbrs:
             # Note: -u changes the name (not Top node anymore)
             G.add_edges_from([(vname,-u) for u in B[cv] if u!=v])
    return G
 
def graph_clique_number(G,cliques=None):
    """Return the clique number (size of the largest clique) for G.

       An optional list of cliques can be input if already computed.

    """
    if cliques is None:
        cliques=find_cliques(G)
    return   max( [len(c) for c in cliques] )


def graph_number_of_cliques(G,cliques=None):
    """  Returns the number of maximal cliques in G.

       An optional list of cliques can be input if already computed.

    """
    if cliques is None:
        cliques=list(find_cliques(G))
    return   len(cliques)

 
def node_clique_number(G,nodes=None,with_labels=False,cliques=None):
    """ Returns the size of the largest maximal clique containing
        each given node.  

        Returns a single or list depending on input nodes.
        Returns a dict keyed by node if "with_labels=True".
        Optional list of cliques can be input if already computed.

    """
    if nodes is None:                 # none, use entire graph
        nodes=G.nodes()
    elif  not isinstance(nodes, list):    # check for a list
        nodes=[nodes]             # assume it is a single value

    if cliques is None:
        cliques=list(find_cliques(G))
    d={}
    for v in nodes:
        d[v]=max([len(c) for c in cliques if v in c])
    
    if with_labels: return d
    if len(d)==1: return d[v] #return single value
    return d.values()


def number_of_cliques(G,nodes=None,cliques=None,with_labels=False):
    """ Returns the number of maximal cliques for each node.

        Returns a single or list depending on input nodes.
        Returns a dict keyed by node if "with_labels=True".
        Optional list of cliques can be input if already computed.

    """
    if nodes is None:
        nodes=G.nodes()   # none, get entire graph
    elif  not isinstance(nodes, list):    # check for a list
        nodes=[nodes]             # assume it is a single value

    if cliques is None:
        cliques=list(find_cliques(G))
    numcliq={}
    for v in nodes:
        numcliq[v]=len([1 for c in cliques if v in c])

    if with_labels: return numcliq
    if len(numcliq)==1: return numcliq[v]
    return numcliq.values()
    
def cliques_containing_node(G,nodes=None,cliques=None,with_labels=False):
    """ Returns a list of cliques containing the given node.

        Returns a single list or list of lists depending on input nodes.
        Returns a dict keyed by node if "with_labels=True".
        Optional list of cliques can be input if already computed.

    """
    if nodes is None:
        nodes=G.nodes()   # none, get entire graph
    elif  not isinstance(nodes, list):    # check for a list
        nodes=[nodes]             # assume it is a single value

    if cliques is None:
        cliques=list(find_cliques(G))
    vcliques={}
    for v in nodes:
        vcliques[v]=[c for c in cliques if v in c]

    if with_labels: return vcliques
    if len(vcliques)==1: return vcliques[v]
    return vcliques.values()

