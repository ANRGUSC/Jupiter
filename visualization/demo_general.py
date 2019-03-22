import numpy as np
import pandas as pd
import holoviews as hv
import networkx as nx
hv.extension('bokeh')

X_MARGIN_PERCENT = 10
Y_MARGIN_PERCENT = 35


def gen_DAG(fname):
    """
    read input file from fname, return adj list.
    """
    adj_from_txt = dict()
    node_name_mapping = dict()   # mapping from node name to index
    with open(fname) as f:
        for i,line in enumerate(f):
            if i == 0:
                num_nodes = int(line.strip('\n'))
            else:
                node_list_txt = line.split()[0]
                node_name_mapping[node_list_txt] = i-1
    with open(fname) as f:
        for i,line in enumerate(f):
            if i == 0:
                continue
            if i == num_nodes:
                adj_from_txt[node_name_mapping[line.split()[0]]] = []
                continue
            node_idx = node_name_mapping[line.split()[0]]
            adj_from_txt[node_idx] = [node_name_mapping[nli] for nli in line.split()[3:]]
    return adj_from_txt, node_name_mapping

def generate_nx_graph(adj_list):
    """
    construct a graph of networkx type.
    We want networkx type in order to get the layout, since networkx
    integrated the graphviz layout library for DAG graphs.
    """
    G = nx.DiGraph()
    for node in adj_list.keys():
        G.add_node(node)
        G.add_edges_from([(node,u) for u in adj_list[node]])
    return G

def reconstruct_graph(adj_list, G, node_status, *attr_keys):
    """
    given a graph (G) of networkx type, we would like to transform it to
    a holoviews type. 
    The reason is, after reconstructing to hv type, we can more easily add
    labels to graph nodes, and hence color the nodes.
    """
    x,y = G.nodes.array([0,1]).T
    x_margin = (x.max()-x.min())*X_MARGIN_PERCENT/100.
    y_margin = (y.max()-y.min())*Y_MARGIN_PERCENT/100.
    xy_range = {'x_min':x.min()-x_margin, 
                'x_max':x.max()+x_margin, 
                'y_min':y.min()-0.5*y_margin, 
                'y_max':y.max()+y_margin+y_margin+y_margin}
    ordered_status = []  # the order of each status appearing in node_labels
    for l in node_status['Status']:
        if l not in ordered_status:
            ordered_status.append(l)
    node_indices = (G.nodes.array([2]).T)[0]
    nodes = hv.Nodes((x,y,node_indices,
                      [node_mapping_rev[ni] for ni in node_indices],
                      *[node_status[k] for k in attr_keys]),
                      vdims=['Task name',*attr_keys])  # data dimensions: http://holoviews.org/user_guide/Annotating_Data.html
    source_node_list = []
    target_node_list = []
    edgepaths = []
    for s in adj_list:
        source_node_list += [s]*len(adj_list[s])
        target_node_list += adj_list[s]
        for ti in adj_list[s]:
            idx_s = list(node_indices).index(s)
            idx_t = list(node_indices).index(ti)
            edgepaths.append(np.array([(x[idx_s],y[idx_s]),(x[idx_t],y[idx_t])]))
    graph = hv.Graph(((source_node_list,target_node_list),nodes,edgepaths))
    node_labels = [hv.Text(x[i],y[i],str(int(node_indices[i]))) for i in range(len(x))]
    node_labels = reduce(lambda a,b: a*b, node_labels)
    return graph, ordered_status, xy_range, node_labels

def get_graph(time, node_status, *attr_keys):
    """
    We first construct a networkx graph, cuz we need the layout by graphviz.
    Then we reconstruct a holoviews graph based on the networkx graph layout,
    to set the label attributes of the nodes --> to color nodes based on that. 
    """
    # get layout information
    # this should be a holo_views graph object, so then we search how to add color attribute to holoviews graph
    hv_graph = hv.Graph.from_networkx(G, nx.drawing.nx_agraph.graphviz_layout,prog='dot')#, iterations=iteration)  
    # reconstruction hv graph based on networkx graph layout
    graph, ordered_status, xy_range, node_labels = reconstruct_graph(adj_list, hv_graph, node_status, *attr_keys)
    return graph.opts(plot=dict(color_index='Status'),
                      style=dict(cmap=ListedColormap([STAT_INDICATOR[s] for s in ordered_status]),
                                 node_size=NODE_SIZE)),xy_range,node_labels

    # graphs_info_CIRCE = [get_graph(i, gen_status_CIRCE(timetable_CIRCE,task_proc_mapping,i-task_assign_time.max()-1), 'Status','Execution time','Processor') for i in time_range]
    # graphs_info_WAVE = [get_graph(i, gen_status_WAVE(task_assign_time,task_proc_mapping,i), 'Status','Assign time','Processor') for i in time_range] #, 'Status','Processor','Assignment time'
    # graphs_CIRCE = [g[0] for g in graphs_info_CIRCE]
    # graphs_WAVE = [g[0] for g in graphs_info_WAVE]
    # xy_range = graphs_info_CIRCE[0][1]
    # node_labels = graphs_info_CIRCE[0][2]

    # # To add label to each node: http://holoviews.org/user_guide/Building_Composite_Objects.html
    # title1 = hv.Text(200,500,"WAVE")
    # title2 = hv.Text(200,500,"CIRCE")
    # hmap = hv.HoloMap({i: (graphs_WAVE[int(i)]*node_labels*title1)+(graphs_CIRCE[int(i)]*node_labels*title2) \
    #         for i in time_range}, kdims=[('TimeStamp','TimeStamp')])\
    #         .redim.range(x=(xy_range['x_min'], xy_range['x_max']), y=(xy_range['y_min'], xy_range['y_max']))
    # hmap
