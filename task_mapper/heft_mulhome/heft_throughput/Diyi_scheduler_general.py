import networkx as nx
import numpy as np
import networkx.drawing
import numpy as np

PRINT = False

class Scheduler_General:

    def __init__(self, g_task, g_processor, num_reserve=1):
        """
        Clusters are indexed by integer: 0,1,2,...
        Processors are indexed by integer pairs: (0,0),(0,1),... Where first int refers to cluster ID
        Task names are string.

            g_cluster:          cluster interconnection
                                a node is a cluster
                                node attributes: 'procs': processor IDs for all processors in that cluster
                                                 'avai_procs': processor IDs for available processors in that cluster
                                edge attributes: 'bandwidth': bandwidth of the inter-cluster link
                                                 'quadratic': tuple defining the bw coefficients
            g_processor:        processor interconnection (static: does not change during scheduling)
                                a node is a processor
                                node attributes: 'comp': dict whose key is task ID, value is comp time for that task. The value is computed in
                                gen_proc_graph.py by division instead of profiling
                                edge attributes: 'bandwidth': bandwidth of the inter-processor link
                                                 'quadratic': tuple defining the bw coefficients
            g_task2proc:        task dag, as well as the mapping from task to processors -- mapping is determined by scheduling algorithm
                                a node is a task
                                node attributes: 'proc_l': list of processors to compute that task
                                                 'lambda_l': list of weights for splitting
                                edge attributes: 'data': total data from parent to child task (aggregated amount over all splitted processors)
            g_proc2task:        mapping from processor to tasks -- mapping is determined by scheduling algorithm
                                a node is a processor
                                node attributes: 'task': task ID for the task assigned to the processor
                                edge attributes: 'data': amount of data from parent to child processor (already splitted according to splitting algo)
                                                 'bandwidth': same as g_processor
                                                 'quadratic': same as g_processor
        """
        self.g_cluster = nx.DiGraph()
        self.g_processor = g_processor
        self.g_task2proc = g_task
        self.g_proc2task = nx.DiGraph()
        self.sys_throughput = 0.
        self.num_reserve = num_reserve
        # ---- setup initial ----
        for t in self.g_task2proc.nodes():
            self.g_task2proc.node[t]['proc_l'] = []
            self.g_task2proc.node[t]['lambda_l'] = []
        self.gen_proc2task(None,None)
        # ---- setup g_cluster ----
        cluster_links = np.empty((0,2),int)
        edge_data = dict()
        for l_from,l_to in g_processor.edges():
            cluster_links = np.vstack([cluster_links,(l_from[0],l_to[0])])
            edge_data[(l_from[0],l_to[0])] = g_processor.get_edge_data(l_from,l_to) #data is bw
        cluster_links = np.unique(cluster_links,axis=0)
        for c_from,c_to in cluster_links:
            self.g_cluster.add_edge(c_from,c_to,**edge_data[(c_from,c_to)])
        for c in self.g_cluster.nodes():
            self.g_cluster.node[c]['procs'] = []
            self.g_cluster.node[c]['avai_procs'] = []
        for p in g_processor.nodes():
            self.g_cluster.node[p[0]]['procs'].append(p[1])
            self.g_cluster.node[p[0]]['avai_procs'].append(p[1])
        self.cluster_size = int(self.g_processor.number_of_nodes()/self.g_cluster.number_of_nodes())    #assume equal size clusters


    def gen_proc2task(self,g_task2proc=None,g_proc2task=None):
        """
        generate the proc2task mapping from g_task2proc and g_processor
        properly split the link data based on lambda assignment on the super-link
        """
        if g_task2proc is None:
            g_task2proc = self.g_task2proc
        if g_proc2task is None:
            g_proc2task = self.g_proc2task


        assert ((g_task2proc==self.g_task2proc and g_proc2task==self.g_proc2task) or
         (g_proc2task!=self.g_proc2task and g_task2proc!=self.g_task2proc))


        for t_from,t_to,data in g_task2proc.edges(data=True):
            vol_total = data['data']    # total data on the super link
            split_from = g_task2proc.node[t_from]
            split_to = g_task2proc.node[t_to]
            lambda_merge = np.concatenate((np.array(split_from['lambda_l']).cumsum(),\
                                           np.array(split_to['lambda_l']).cumsum()))
            proc_from_to = [list(split_from['proc_l']),list(split_to['proc_l'])]
            links = []
            for i in np.argsort(lambda_merge)[:-1]//len(split_from['proc_l']):
                links.append((proc_from_to[0][0],proc_from_to[1][0]))
                proc_from_to[i>0].pop(0)
            lambda_delta = np.diff([0.]+sorted(lambda_merge))
            for i,(l1,l2) in enumerate(links):
                if lambda_delta[i]<=0.:
                    continue
                _attr = self.g_processor.edges[l1,l2]
                _attr['data'] = lambda_delta[i]*vol_total
                g_proc2task.add_edge(l1,l2,**_attr)
            #g_proc2task.add_edges_from(edges)
        for t,data in g_task2proc.nodes(data=True):
            for idx,p in enumerate(data['proc_l']):
                _weight = data['lambda_l'][idx]
                g_proc2task.add_node(p,comp=_weight*self.g_processor.nodes[p]['comp'][t.split('#')[-1]],task=t)
                


    def remove_links(self,links):
        """
        links: [{'proc_from':p_from,'proc_to':p_to,'task_from':t_from,'task_to':t_to}]
        update the following correspondingly:
         * g_cluster
         * g_task2proc
         * g_proc2task
        """
        for l in links:
            if 'proc_from' not in l.keys() or 'proc_to' not in l.keys():
                l['proc_from'] = self.g_task2proc.node[l['task_from']]['proc_l'][0]
                l['proc_to'] = self.g_task2proc.node[l['task_to']]['proc_l'][0]
            if 'task_from' not in l.keys() or 'task_to' not in l.keys():
                l['task_from'] = self.g_proc2task.node[l['proc_from']]['task']
                l['task_to'] = self.g_proc2task.node[l['proc_to']]['task']
            # ---- only support link removal for dup step ----
            assert self.g_task2proc.node[l['task_from']]['lambda_l'] == [1]
            assert self.g_task2proc.node[l['task_to']]['lambda_l'] == [1]
            # ---- update g_cluster ----
            # no need to update g_cluster --> don't reset avai_procs for now.
            #for i_ends in ['from','to']:
            #    _c_end,_p_end = l['proc_{}'.format(i_ends)]
            #    try:
            #        assert _p_end not in self.g_cluster.node[_c_end]['avai_procs']
            #    except Exception:
            #        import pdb; pdb.set_trace()
            #    self.g_cluster.node[_c_end]['avai_procs'].append(_p_end)
            # ---- update g_task2proc ----
            self.g_task2proc.remove_edge(l['task_from'],l['task_to'])   # cuz lambda = 1
            # ---- update g_proc2task ----
            self.g_proc2task.remove_edge(l['proc_from'],l['proc_to'])


    def add_links(self,links,F_comp_lookup=lambda t,p:-1,F_data_lookup=lambda t1,t2,p1,p2:-1):
        """
        same as self.remove_links().
        F_comp_lookup: returns the compuatation time of task t on processor p
        F_data_lookup: returns the communication data from task t1 to t2. i.e. data on the new link
        links: [{'proc_from':p_from,'proc_to':p_to,'task_from':t_from,'task_to':t_to}]
        """
        for l in links:
            l['data'] = F_data_lookup(l['task_from'],l['task_to'],l['proc_from'],l['proc_to'])
            l['comp_from'] = F_comp_lookup(l['task_from'],l['proc_from'])
            l['comp_to'] = F_comp_lookup(l['task_to'],l['proc_to'])
            # ---- update g_cluster ----
            for ends in ['from','to']:
                _c_end,_p_end = l['proc_{}'.format(ends)]
                if _p_end in self.g_cluster.node[_c_end]['avai_procs']:
                    self.g_cluster.node[_c_end]['avai_procs'].remove(_p_end)
            # ---- update g_task2proc ----
            self.g_task2proc.add_node(l['task_from'],lambda_l=[1],proc_l=[l['proc_from']])
            self.g_task2proc.add_node(l['task_to'],lambda_l=[1],proc_l=[l['proc_to']])
            self.g_task2proc.add_edge(l['task_from'],l['task_to'],data=l['data'])
            # ---- update g_processor ----
            # maybe no need?
            # ---- update g_proc2task ----
            self.g_proc2task.add_node(l['proc_from'],comp=l['comp_from'],task=l['task_from'])
            self.g_proc2task.add_node(l['proc_to'],comp=l['comp_to'],task=l['task_to'])
            _attr = self.g_processor.edges[l['proc_from'],l['proc_to']]
            #_attr with attribute 'bandwidth' and 'quadratic'
            _attr['data'] = l['data']
            self.g_proc2task.add_edge(l['proc_from'],l['proc_to'],**_attr)


    def split_task(self,task,lambda_):
        """
        when splitting, update 'comp' & 'data' in g_proc2task also
        """
        pass

    def calc_task_throughput(self,task_id,g_task2proc=None,g_proc2task=None):
        if g_task2proc is None:
            g_task2proc = self.g_task2proc
        if g_proc2task is None:
            g_proc2task = self.g_proc2task
        throughput = dict()
        for i,pi in enumerate(g_task2proc.node[task_id]['proc_l']):
            try:
                assert task_id == g_proc2task.node[pi]['task']
            except Exception:
                import pdb; pdb.set_trace()
            _comp = g_proc2task.node[pi]['comp']
            throughput[pi] = 1/_comp if _comp != 0 else float('inf')
        pi_min = min(throughput.keys(), key=lambda x: throughput[x])
        return throughput[pi_min], pi_min


    def calc_link_throughput(self,link_id,g_task2proc=None,g_proc2task=None):
        """
        link_id is a tuple defining the start and end tasks
        """
        if g_task2proc is None:
            g_task2proc = self.g_task2proc
        if g_proc2task is None:
            g_proc2task = self.g_proc2task
        throughput = dict()
        for i,pi in enumerate(g_task2proc.node[link_id[0]]['proc_l']):
            for j,pj in enumerate(g_task2proc.node[link_id[1]]['proc_l']):
                if (pi,pj) not in g_proc2task.edges.keys():
                    continue
                throughput[(pi,pj)] = g_proc2task.edges[pi,pj]['bandwidth']/g_proc2task.edges[pi,pj]['data']
        li_min = min(throughput.keys(), key=lambda x: throughput[x])
        return throughput[li_min], li_min

    def calc_overall_throughput(self,g_task2proc=None,g_proc2task=None):
        isInputNone = True if g_task2proc is None else False
        if g_task2proc is None:
            g_task2proc = self.g_task2proc
        if g_proc2task is None:
            g_proc2task = self.g_proc2task
        throughput = dict()
        for t in g_task2proc.nodes():
            _thp, _p = self.calc_task_throughput(t,g_task2proc,g_proc2task)
            #_p is the processor with minumum thp among self.task2proc.nodes[t]['proc_l']
            throughput[(t,_p)] = _thp
        for l in g_task2proc.edges():
            _thp, _pp = self.calc_link_throughput(l,g_task2proc,g_proc2task)
            throughput[(l,_pp)] = _thp
        component_min = min(throughput.keys(), key=lambda x:throughput[x])
        if isInputNone:
            self.sys_throughput = throughput[component_min]
            #update self.sys_throughput only when the parameters of calc_overall_throughput is default
        #import pdb; pdb.set_trace()
        return throughput[component_min], component_min, throughput
        #"throughput[component_min]" is the system's throughput(some value).
        #"throughput" is a dictionary which contains the throughput of every element


    def calc_clu_path_throughput(self,path_clu,data):
        """
        path_clu: a list defining a path where each node is a cluster in g_cluster
        return the link throughput (min over all cluster links) for path_clu
        (assume links along path_clu are transferring the same amount of data)
        """
        links = [(path_clu[i],path_clu[i+1]) for i,c in enumerate(path_clu[:-1])]
        link_bottleneck = min([self.g_cluster.edges[l]['bandwidth'] for l in links])
        return link_bottleneck/data

    def is_empty_cluster(self,c):
        return self.g_cluster.node[c]['procs'] == self.g_cluster.node[c]['avai_procs']


    def initial_mapping(self):
        """
        input: task_dag and processor_g
        output:initial_mapping dictionary. initial_mapping = {'task1':1;'task2':2,'task3':6}
        ***the processor must be of type int
        """
        #initial_mapping = {'1': 0, '2':1, '3':2, '4':3, '5':4}
        #return initial_mapping
        avg_comp = dict()
        num_proc = len(list(self.g_processor.nodes()))
        #the average compution time of task t over all processors
        for t in list(self.g_task2proc.nodes()):
            avg_comp[t] = 0
            for n in list(self.g_processor.nodes()):
                avg_comp[t] = avg_comp[t]+ self.g_processor.node[n]['comp'][t]

            avg_comp[t] = avg_comp[t]/num_proc

        avg_comm = dict()
        num_link = len(list(self.g_processor.edges()))
        #the average commmunication time of e over all links
        for e1,e2,data in list(self.g_task2proc.edges(data=True)):
            _data = data['data']
            avg_comm[(e1,e2)] = 0
            for l1,l2 in list(self.g_processor.edges()):
                _quad  = self.g_processor.edges[l1,l2]['quadratic']
                avg_comm[(e1,e2)] = avg_comm[(e1,e2)] + (_quad[0]*(_data**2)+_quad[1]*_data+_quad[2])
            avg_comm[(e1,e2)] = avg_comm[(e1,e2)]/num_link

        #NOTE:assume only one input task
        _topo_t = list(nx.topological_sort(self.g_task2proc))
        uprank = dict()
        for t in _topo_t:
            uprank[t] = 0
        for t in _topo_t[1:]:
            _temp = max([(uprank[pre]+avg_comm[(pre,t)]) for pre in self.g_task2proc.predecessors(t)])
            uprank[t] = avg_comp[t]+_temp
        dec_t = sorted(uprank.keys(), key=lambda x:-uprank[x])
        #dec_t is tasks in decreasing order of uprank
        avai_proc = list(self.g_processor.nodes())
        mapping = dict()
        for t in dec_t:
            sucs = list(self.g_task2proc.successors(t))
            data = [self.g_task2proc.edges[t,_suc]['data'] for _suc in sucs]
            #NOTE:check this
            min_occu = float('inf')
            for p in avai_proc:
                #NOTE:need to define avai_proc
                if len(self.g_cluster.nodes[p[0]]['avai_procs']) <= self.num_reserve:
                    continue
                exit_flag = False
                #exit_flag = true if (p,mapping[_suc]) is not an edge in processor_g
                _comp = self.g_processor.node[p]['comp'][t]
                _max_comm = 0
                if len(sucs)!=0:
                    for idx, _suc in enumerate(sucs):
                        _data = data[idx]
                        if self.g_processor.has_edge(p,mapping[_suc]) == False:
                            exit_flag = True
                            break
                        _quadra = self.g_processor.edges[p,mapping[_suc]]['quadratic']
                        _comm = _quadra[0]*(_data**2)+_quadra[1]*_data+_quadra[2]
                        if _comm > _max_comm:
                            _max_comm = _comm
                    if exit_flag == True:
                        continue
                _occu = max(_comp,_max_comm)
                if _occu < min_occu:
                    min_occu = _occu
                    mapping[t] = p
            if t in mapping.keys():
                try:
                    self.g_cluster.nodes[mapping[t][0]]['avai_procs'].remove(mapping[t][1])
                except Exception:
                    import pdb; pdb.set_trace()
                #setup g_cluster
                avai_proc.remove(mapping[t])
            else:
                if PRINT:
                    print('failed to find initial mapping')
                return False
        # ---- setup g_task2proc ----
        for t,p in mapping.items():
            self.g_task2proc.node[t]['proc_l'] = [p]
            self.g_task2proc.node[t]['lambda_l'] = [1]
        #for l in self.g_task2proc:
        #    print(l, "---", self.g_task2proc.node[l])
        # ---- setup g_proc2task ----
        self.gen_proc2task()

        # ---- misc ----
        self.calc_overall_throughput(None,None)
        #the function above updates the self.sys_throughput
        return True
