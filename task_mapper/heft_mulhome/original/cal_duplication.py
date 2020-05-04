"""
The condition under which duplication can improve the throughput: 
possible new bottlenecks introduced in the system are less than the old one. 


Possible new bottlenecks include:

1. Copy tasks (which transfer data using bottleneck link) from src node to idle node. Don't copy all src node tasks.
   The new execution time sum of those copied tasks on the idle node cannot exceed the bottleneck time.
2. Find all nodes who has a parent task of any of the copied tasks. Since we use virtual links, 
   the links related to a new node are all idle, thus we just need to make sure 
   the new file transfer time on each link is less than the bottleneck.
3. Transfer time from new node to dst node is less than bottleneck.

"""
class CalDuplication:

    def __init__(self, links, processors, tasks, comp_cost, data, quaratic_profile, btnk_id):
        self.links = links
        self.processors = processors
        self.btnk_id = btnk_id
        self.tasks = tasks
        self.comp_cost = comp_cost
        self.data = data
        self.quaratic_profile = quaratic_profile
        
    def get_dup_node(self, links, processors, btnk_id):
        """
        input: links and nodes, and the bottleneck link to bypass
        calculate a hashmap of candidate nodes and the max value of incurred resource takeup time
        output: best candidate node
        """
        btnk_link = self.get_link_by_id(btnk_id)
        src_proc = self.get_proc_by_id(self.btnk_id.split('_')[0])
        dst_proc = self.get_proc_by_id(self.btnk_id.split('_')[1])
        
        # hashmap {task number (index in the tasks list) -> processor id}
        task_to_proc = self.get_procs_by_tasks()
        
        # get tasks in src proc that transfer file to dst proc
        # get tasks in dst proc that receive file from src node
        task_ids_to_dup = []
        task_ids_to_recv = []
        btnk_time = btnk_link.time_line[-1].end
        for linkdur in btnk_link:
            task_ids_to_dup.append(linkdur.start_task_num)
            task_ids_to_recv.append(linkdur.end_task_num)
        
        # find all parents of the to-be-duplicated tasks
        parent_tasks = set()
        for parent in tasks:
            for task_id in task_ids_to_dup:
                if self.data[parent.number][task_id] > 0:
                    parent_tasks.add(parent)
                    
        files_to_dst = [] # a list of file sizes to transfer from idle node to dst node
        files_from_src = {} # node id -> list of file sizes to transfer to idle node
        for tid_scr in task_ids_to_dup:
            for tid_dst in task_ids_to_recv:
                if self.data[tid_src][tid_dst] > 0:
                    files_to_dst.append(self.data[tid_src][tid_dst])
        for tid_scr in parent_tasks:
            for tid_dst in task_ids_to_dup:
                if self.data[tid_src][tid_dst] > 0:
                    src_proc = task_to_proc[tid_src]
                    if not src_proc in files_from_src:
                        files_from_src[src_proc] = []
                    files_from_src[src_proc].append(self.data[tid_src][tid_dst])
        
        # hashmap {idle node id to duplicate : max new time incurred}. New incurred times:
        # 1. all parent nodes to idle node link usage
        # 2. idle node computation
        # 3. idle node to destination node transfer
        procid_to_max_time = {}
        for proc in self.processors:
            if len(proc.time_line) != 0:
                continue
            else: # this is an idle node
                # get sum of computation time
                comp_time = 0
                for task_id in task_ids_to_dup:
                    comp_time = comp_time + comp_cost[task_id][proc.number]
                
                # get the max of all link transfer time
                # new node to destination node
                time_to_dst = 0.0
                for file_size in files_to_dst:
                    time_to_dst += self.cal_comm_quadratic(file_size, self.quaratic_profile[proc.number][dst_proc.number])
                        
                # all source nodes to new node
                time_from_src = []
                for key in files_from_src:
                    cur_time = 0.0
                    for file_size in files_from_src[key]:
                        cur_time += self.cal_comm_quadratic(file_size, self.quaratic_profile[key.number][proc.number])
                    time_from_src.append(cur_time)
                
                new_btnk_proc = max(time_from_src)
                new_btnk_proc = max(new_btnk_proc, time_to_dst)
                new_btnk_proc = max(new_btnk_proc, comp_time)
                
                procid_to_max_time[proc.number] = new_btnk_proc
        
        min_btnk = time.time()
        node = -1
        for key in procid_to_max_time:
            if procid_to_max_time[key] < min_btnk:
                min_btnk = procid_to_max_time[key]
                node = key
            
        if min_btnk >= btnk_time: # no point for duplication
            return (-1, time.time())
        return (node, min_btnk)
            
    def get_link_by_id(self, link_id):
        for link in self.links:
            if link.id == link_id:
                return link
    
    def get_proc_by_id(self, proc_id):
        for proc in self.processors:
            if proc.number == proc_id:
                return proc
                
    def get_procs_by_tasks(self):
        task_to_proc = {}
        for proc in self.processors:
            if len(proc.time_line) == 0:
                continue
            else:
                for duration in proc.time_line:
                    task_to_proc[duration.task_num] = proc.number
        return task_to_proc
            
    def cal_comm_quadratic(self, file_size, quaratic_profile):
        return (np.square(file_size)*quaratic_profile[0] + file_size*quaratic_profile[1] + quaratic_profile[2])
            
