def get_bottleneck_id(links, processors):
    """
    given current processor and link usage, return the id of resource with max takeup time 
    (without considering pipelined wait times)
    input: an array of links and an array of processors (with takeup time)
    output: id of bottleneck resource (string)
    """
    max_time = 0.0
    bottleneck = ""
    for link in links:
        if len(link.time_line) != 0:
            if link.time_line[-1].end > max_time:
                max_time = link.time_line[-1].end
                bottleneck = link.id
                
    for processor in processors:
        if len(processor.time_line) != 0:
            if processor.time_line[-1].end > max_time:
                max_time = processor.time_line[-1].end
                bottleneck = str(processor.id)
                
    return bottleneck
    
    
def is_link(rsrc_id):
    """
    return true if the bottleneck id represents a link
    false if processor
    """
    for c in rsrc_id:
        if c == '_':
            return True
    return False
