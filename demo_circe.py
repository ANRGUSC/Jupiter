from tornado import gen
from functools import partial
from bokeh.models import Button, NumeralTickFormatter
from bokeh.palettes import RdYlBu3
from bokeh.plotting import *
from bokeh.core.properties import value
from bokeh.models import ColumnDataSource, Label, Arrow, NormalHead, LabelSet
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
from bokeh.io import output_file, show
from bokeh.layouts import row
import paho.mqtt.client as mqtt
import time


OUTFNAME = 'demo_circe.html'
SERVER_IP = "localhost"
SUBSCRIPTIONS = 'CIRCE'


start_time =[]
finish_time =0
total_time =0
offset = 0
input_num = 0

source = ColumnDataSource(data=dict(top=[0], bottom=[0],left=[0],right=[0], color=["#9ecae1"],line_color=["black"], line_width=[2]))

source1 = ColumnDataSource(data=dict(x=[8], y=[3.5], time=[''],text_font_style=['bold']))

source2 = ColumnDataSource(data=dict(top=[5.15],bottom=[4.85],left=[3.3],right=[3.7],color=["#C2D2F9"]))

doc = curdoc()
doc.title = 'CIRCE Visualization'

class mq():


    def __init__(self,outfname,subs,server,port,timeout,looptimeout):
        self.OUTFNAME = outfname
        self.subs = subs
        self.server = server
        self.port = port
        self.timeout = timeout
        self.looptimeout = looptimeout
        self.outf = open(OUTFNAME,'a')
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.server, self.port, self.timeout)

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self,client, userdata, flags, rc):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        subres = client.subscribe(self.subs,qos=1)
        print("Connected with result code "+str(rc))


    # The callback for when a PUBLISH message is received from the server.
    def on_message(self,client, userdata, msg):
        start_messages = ['local_pro starts', 'aggregate0 starts', 'aggregate1 starts', 'aggregate2 starts',
        'simple_detector0 starts', 'simple_detector1 starts', 'simple_detector2 starts', 'astute_detector0 starts',
        'astute_detector1 starts', 'astute_detector2 starts', 'fusion_center0 starts', 'fusion_center1 starts', 
        'fusion_center2 starts', 'global_fusion starts']

        end_messages = ['local_pro ends', 'aggregate0 ends', 'aggregate1 ends', 'aggregate2 ends',
        'simple_detector0 ends', 'simple_detector1 ends', 'simple_detector2 ends', 'astute_detector0 ends',
        'astute_detector1 ends', 'astute_detector2 ends', 'fusion_center0 ends', 'fusion_center1 ends', 
        'fusion_center2 ends', 'global_fusion ends']


        top_dag=[5.15, 4.15, 4.15, 4.15, 3.15, 3.15, 3.15, 3.15, 3.15, 3.15, 2.15,2.15,2.15,1.15]
        bottom_dag=[4.85, 3.85,3.85,3.85, 2.85,2.85,2.85,2.85,2.85,2.85, 1.85,1.85,1.85, 0.85]
        left_dag= [3.3,1.3,3.3,5.3, 0.8, 1.8, 2.8, 3.8, 4.8,5.8, 1.3,3.3,5.3,3.3]
        right_dag=[3.7,1.7,3.7,5.7, 1.2, 2.2, 3.2, 4.2, 5.2, 6.2,1.7,3.7,5.7,3.7]


        top = [4,4,4,4,4,4,4,2,2,2,2,2,2,2]
        bottom = [2,2,2,2,2,2,2,0,0,0,0,0,0,0]
        left = [0,1,2,3,4,5,6,0,1,2,3,4,5,6]
        right = [1,2,3,4,5,6,7,1,2,3,4,5,6,7]

        message = msg.payload.decode()
        print(message)
        global start_time
        global finish_time
        global total_time


        if message in start_messages:

            if message == 'local_pro starts':
                new_time =  time.time()
                start_time.append(new_time)

            index = start_messages.index(message)
            top,bottom,left,right = top[index],bottom[index],left[index],right[index]
            topd,bottomd,leftd,rightd = top_dag[index],bottom_dag[index],left_dag[index],right_dag[index]
        
            color = "red"
            doc.add_next_tick_callback(partial(update3, top= topd, bottom=bottomd,left=leftd,right=rightd, color=color))
            doc.add_next_tick_callback(partial(update1, top=top, bottom=bottom,left=left, right=right,color=color))
            

        elif message in end_messages:

            if message == 'global_fusion ends':
                finish_time = time.time()
                total_time = (finish_time - start_time.pop(0))/60
                global offset
                global input_num
                print("TOTAL_TIME: ", total_time, " minutes")
                doc.add_next_tick_callback(partial(update2, x=7.5, y=3.2-offset, time = 'in'+str(input_num)+": "+str(format(total_time, '.4f') + ' min')))
                offset = offset + 0.2
                input_num = input_num+1


            index = end_messages.index(message)
            top,bottom,left,right = top[index],bottom[index],left[index],right[index]
            topd,bottomd,leftd,rightd = top_dag[index],bottom_dag[index],left_dag[index],right_dag[index]


            color=['#C2D2F9',"#5984E8","#5984E8","#5984E8","#9380F0","#9380F0","#9380F0",
            "#1906BF","#1906BF","#1906BF", '#084594','#084594','#084594',"#33148E"]
            color1=["#C2D2F9","#5984E8","#5984E8","#5984E8","#9380F0","#1906BF","#9380F0",
            "#1906BF","#9380F0","#1906BF","#084594","#084594","#084594","#33148E"]

            doc.add_next_tick_callback(partial(update3, top= topd, bottom=bottomd,left=leftd,right=rightd, color=color1[index]))
            doc.add_next_tick_callback(partial(update1, top=top, bottom=bottom,left=left, right=right,color=color[index]))


            
            
# create a plot and style its properties
p = figure(plot_width=900, plot_height=500, responsive = True)
p.background_fill_color = "#EEEDED"
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.xaxis.axis_label = 'Raspberry Pi Cluster'
p.xaxis.axis_label_text_font_size='20pt'

p.quad(top=[2,2,2,2,2,2,2,4,4,4,4,4,4,4], bottom=[0,0,0,0,0,0,0,2,2,2,2,2,2,2], left=[0,1,2,3,4,5,6,0,1,2,3,4,5,6],
       right=[1,2,3,4,5,6,7,1,2,3,4,5,6,7], color=["#1906BF","#1906BF","#1906BF", '#084594','#084594','#084594',"#33148E",
       '#C2D2F9',"#5984E8","#5984E8","#5984E8","#9380F0","#9380F0","#9380F0"], 
       line_color="black", line_width=2)

lab = LabelSet(x='x', y='y', text='time',text_font_style='bold',text_color='black',source=source1)
p.add_layout(lab)

p.add_layout(Label(x=7.5, y=3.6, text='TOTAL TIME', text_color= "black", text_font_style='bold'))

p.quad(top=4, bottom =0, left=7.3, right=9,line_color="black",color="#EEEDED",line_width=2)


for i in range(0, 7):
    rp = Label(x=0.4+i ,y=3 , text=str(i+1), text_color='black', text_font_size='20pt',text_font_style='bold')
    p.add_layout(rp)
for i in range(0, 7):
    rp = Label(x=0.4+i ,y=1, text=str(i+8), text_color='black', text_font_size='20pt',text_font_style='bold')
    p.add_layout(rp)


l = p.quad(top='top', bottom='bottom', left='left', right='right',color="color", line_color="black", line_width=2, source=source)




m = mq(outfname='mqtt_emon.html',subs=SUBSCRIPTIONS,
           server = SERVER_IP,port=1883,timeout=60,looptimeout=1)





p1=figure(plot_width=900, plot_height=650, responsive = True)
p1.background_fill_color = "#EEEDED"
p1.xgrid.grid_line_color = None
p1.ygrid.grid_line_color = None
p1.xaxis.axis_label = 'Network Anomaly Detection Task Graph and Mapping'
p1.xaxis.axis_label_text_font_size='20pt'


p1.add_layout(Label(x= 5.5, y=4.7, text="CIRCE", text_color="black", text_font_style='bold',text_font_size='38pt'))



p1.quad(top=[4.5,4.25,4,3.75,3.5,3.25,3,2.75,2.5,2.25,2,1.75,1.5,1.25], 
    bottom =[4.25,4,3.75,3.5,3.25,3,2.75,2.5,2.25,2,1.75,1.5,1.25,1], 
    left=[7,7,7,7,7,7,7,7,7,7,7,7,7,7],
    right=[9.7,9.7,9.7,9.7,9.7,9.7,9.7,9.7,9.7,9.7,9.7,9.7,9.7,9.7],
    color=["#C2D2F9","#5984E8","#5984E8","#5984E8","#9380F0","#9380F0","#9380F0","#1906BF","#1906BF","#1906BF","#084594","#084594","#084594","#33148E"],
    line_color="black", line_width=2)

p1.line([8.8,8.8], [1,4.5],line_width=2,line_color = "black")


source3 = ColumnDataSource(data=dict(height=[4.5, 4.25,4,3.75,3.5,3.25,3,2.75,2.5,2.25,2,1.75,1.5,1.25,1, 4.25,4,3.75,3.5,3.25,3,2.75,2.5,2.25,2,1.75,1.5,1.25,1],
                                    weight=[7.1, 7.1,7.1,7.1,7.1,7.1,7.1,7.1,7.1,7.1,7.1,7.1,7.1,7.1,7.1, 8.8,8.8,8.8,8.8,8.8,8.8,8.8,8.8,8.8,8.8,8.8,8.8,8.8,8.8],
                                    names=['Mapping tasks to nodes','local_pro', 'aggregate0', 'aggregate1', 'aggregate2','simple_detector0','simple_detector1',
                                    'simple_detector2','astute_detector0','astute_detector1','astute_detector2','fusion_center0',
                                    'fusion_center1','fusion_center2','global_fusion',
                                    'RPi 1','RPi 2','RPi 3','RPi 4','RPi 5','RPi 6','RPi 7','RPi 8','RPi 9','RPi 10','RPi 11',
                                    'RPi 12','RPi 13','RPi 14']))

labels = LabelSet(x='weight', y='height', text='names', level='glyph',
              x_offset=5, y_offset=5, source=source3, render_mode='canvas',text_color='black')
p1.add_layout(labels)


p1.quad(top=[5.15, 4.15, 4.15, 4.15, 3.15, 3.15, 3.15, 3.15, 3.15, 3.15, 2.15,2.15,2.15,1.15], 
    bottom=[4.85, 3.85,3.85,3.85, 2.85,2.85,2.85,2.85,2.85,2.85, 1.85,1.85,1.85, 0.85], 
    left=[3.3,1.3,3.3,5.3, 0.8, 1.8, 2.8, 3.8,  4.8,5.8, 1.3,3.3,5.3,3.3], 
    right=[3.7,1.7,3.7,5.7, 1.2, 2.2, 3.2,  4.2,   5.2,  6.2,     1.7,3.7,5.7,3.7],
    color=["#C2D2F9","#5984E8","#5984E8","#5984E8","#9380F0","#1906BF","#9380F0","#1906BF","#9380F0","#1906BF","#084594","#084594","#084594","#33148E"])



#p1.ellipse(3.5, 5, size=40, color="#C2D2F9") #local_pro
local_pro = Label(x=2.3, y=4.9, text='local_pro',text_color='black',background_fill_color='#C2D2F9', background_fill_alpha=0.5)
p1.add_layout(local_pro)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=4.85, x_end=1.5, y_end=4.2))
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=4.85, x_end=3.5, y_end=4.2))
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=4.85, x_end=5.5, y_end=4.2))


#p1.ellipse(1.5, 4, size=40, color="#5984E8") #aggregate0
aggregare0 = Label(x=1, y=4.3, text='aggregate0',text_color='black',background_fill_color='#5984E8', background_fill_alpha=0.5)
p1.add_layout(aggregare0)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=1.5, y_start=3.83, x_end=1, y_end=3.2))
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=1.5, y_start=3.83, x_end=2, y_end=3.2))


#p1.ellipse(3.5, 4, size=40, color="#5984E8") #aggregate1
aggregate1 = Label(x=3.15, y=4.3, text='aggregate1',text_color='black',background_fill_color='#5984E8', background_fill_alpha=0.5)
p1.add_layout(aggregate1)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=3.83, x_end=3, y_end=3.2))
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=3.83, x_end=4, y_end=3.2))


#p1.ellipse(5.5, 4, size=40, color="#5984E8") #aggregate2
aggregate2 = Label(x=5, y=4.3, text='aggregate2',text_color='black',background_fill_color='#5984E8', background_fill_alpha=0.5)
p1.add_layout(aggregate2)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=5.5, y_start=3.83, x_end=5, y_end=3.2))
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=5.5, y_start=3.83, x_end=6, y_end=3.2))


#p1.ellipse(1, 3, size=40, color="#9380F0") #simple_detector0
simple_detector0 = Label(x=0.7, y=3.35, text='simple_detector0',text_color='black',background_fill_color='#9380F0', background_fill_alpha=0.5)
p1.add_layout(simple_detector0)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=1, y_start=2.83, x_end=1.45, y_end=2.18))


#p1.ellipse(2, 3, size=40, color="#1906BF") #astute_detector0
astute_detector0 = Label(x=1.5, y=2.6, text='astute_detector0',text_color='black',background_fill_color='#1906BF', background_fill_alpha=0.7)
p1.add_layout(astute_detector0)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=2, y_start=2.83, x_end=1.55, y_end=2.18))


#p1.ellipse(3, 3, size=40, color="#9380F0") #simple_detector1
simple_detector1 = Label(x=2.5, y=3.35, text='simple_detector1',text_color='black',background_fill_color='#9380F0', background_fill_alpha=0.5)
p1.add_layout(simple_detector1)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3, y_start=2.83, x_end=3.45, y_end=2.18))


#p1.ellipse(4, 3, size=40, color="#1906BF") #astute_detector1
astute_detector1 = Label(x=3.5, y=2.6, text='astute detector1',text_color='black',background_fill_color='#1906BF', background_fill_alpha=0.7)
p1.add_layout(astute_detector1)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=4, y_start=2.83, x_end=3.55, y_end=2.18))


#p1.ellipse(5, 3, size=40, color="#9380F0") #simple_detector2
simple_detector2 = Label(x=4.5, y=3.35, text='simple_detector2',text_color='black',background_fill_color='#9380F0', background_fill_alpha=0.5)
p1.add_layout(simple_detector2)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=5, y_start=2.83, x_end=5.45, y_end=2.18))


#p1.ellipse(6, 3, size=40, color="#1906BF") #astute_detector2
astute_detector2 = Label(x=5.5, y=2.6, text='astute_detector2',text_color='black',background_fill_color='#1906BF', background_fill_alpha=0.7)
p1.add_layout(astute_detector2)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=6, y_start=2.83, x_end=5.55, y_end=2.18))


#p1.ellipse(1.5, 2, size=40, color="#084594") #fusion_center0
fusion_center0 = Label(x=1, y=1.6, text='fusion_center0',text_color='black',background_fill_color='#084594', background_fill_alpha=0.5)
p1.add_layout(fusion_center0)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=1.5, y_start=1.83, x_end=3.3, y_end=1.18))


#p1.ellipse(3.5, 2, size=40, color='#084594') #fusion_center1
fusion_center1 = Label(x=3, y=1.6, text='fusion_center1',text_color='black',background_fill_color='#084594', background_fill_alpha=0.5)
p1.add_layout(fusion_center1)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=1.83, x_end=3.5, y_end=1.18))


#p1.ellipse(5.5, 2, size=40, color='#084594') #fusion_center2
fusion_center2 = Label(x=5, y=1.6, text='fusion_center2',text_color='black',background_fill_color='#084594', background_fill_alpha=0.5)
p1.add_layout(fusion_center2)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=5.5, y_start=1.83, x_end=3.7, y_end=1.18))


#p1.ellipse(3.5, 1, size=40, color="#33148E") #global_fusion
global_fusion = Label(x=2, y=0.9, text='global_fusion',text_color='black',background_fill_color='#33148E', background_fill_alpha=0.5)
p1.add_layout(global_fusion)



ellipse_source = p1.quad(top='top', bottom='bottom', left='left', right='right',color='color', source= source2)


def update():
    m.client.loop(timeout=0.5)


@gen.coroutine
def update1(top,bottom,right,left,color):
    source.stream(dict(top=[top], bottom=[bottom],left=[left],right=[right],color=[color],line_color=["black"], line_width=[2]))


@gen.coroutine
def update2(x,y,time):
    source1.stream(dict(x=[x], y=[y], time=[time], text_font_style= ['bold']))

@gen.coroutine
def update3(top,bottom,left,right,color):
    source2.stream(dict(top=[top], bottom=[bottom],left=[left],right=[right],color=[color]))

doc.add_root(p)
doc.add_root(p1)

doc.add_periodic_callback(update, 50) 
