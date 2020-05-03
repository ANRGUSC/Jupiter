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
class Duplication:

    def __init__(self, links, processors, tasks, comp_cost, data, quaratic_profile, btnk_id):
        self.links = links
        self.processors = processors
        self.btnk_id = btnk_id
        
    def get_dup_node(self, links, processors, btnk_id):
        """
        input: links and nodes, and the bottleneck link to bypass
        calculate a hashmap of candidate nodes and the max value of incurred resource takeup time
        output: best candidate node
        """
        src_proc = self.get_proc_by_id(self.btnk_id.split('_')[0])
        dst_proc = self.get_proc_by_id(self.btnk_id.split('_')[1])
        
        # hashmap {task number (index in the tasks list) -> processor id}
        task_to_proc = self.get_procs_by_tasks()
        
        # get tasks in src proc that transfer file to dst proc
        task_ids_to_dup = []
        btnk_link = self.get_link_by_id(btnk_id)
        btnk_time = btnk_link.time_line[-1].end
        for linkdur in btnk_link:
            task_ids_to_dup.append(linkdur.start_task_num)
        
        
        
    def get_link_by_id(self, link_id):
        for link in self.links:
            if link.id == link_id:
                return link
    
    def get_parent_procs(proc):
    """
    return a list of processors where 
    """
    
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
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        
    def get_tasks_on_proc():
    
    def get_parents_for_all(self):
        for task in self.tasks:
            for parent in self.tasks:
                if self.data[parent.number][task.number] != -1:
                    task.parents_numbers.append(parent.number)
    
    
    
    
    
    
