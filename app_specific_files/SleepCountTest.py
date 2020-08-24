import threading 
import time

def sleep():
    time.sleep(5)

def count():
    ct = 0
    for i in range(99999999):
        ct = ct + 1
        ct = ct - 1
  
if __name__ == "__main__": 
    # creating thread 
    t1 = threading.Thread(target=count) 
    t2 = threading.Thread(target=count)
    
    # starting thread 1 
    t1.start() 
    # starting thread 2 
    t2.start() 
    start = time.time()
    # wait until thread 1 is completely executed 
    t1.join()
    t2.join()
    end = time.time()
    # wait until thread 2 is completely executed  
    print("start")
    print(start)
    print("end")
    print(end)
    print("exec")
    print(end-start)
    print('\n')
    # both threads completely executed 
    #print("Done!") 
