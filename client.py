from tkinter import *
import cv2
import socketio
import argparse
import numpy as np
from PIL import Image, ImageTk

sio = socketio.Client()
parser = argparse.ArgumentParser()
parser.add_argument('--ip', type=str,
                    help='Enter IP address for socket', default = '0.0.0.0')

parser.add_argument('--port', type=str,
                    help='Port', default = '8080')

args = parser.parse_args()

ip = args.ip
port = args.port

panel = None

master = Tk()

params = {
    'seed': None,
    'idx': None
}

def onStartClick():

   params['seed'] = int( ent.get() )
   params['idx'] = w1.get()

   sio.emit('begin', params)

@sio.on('img')
def show_img(img):
    nparr = np.frombuffer(img, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img = cv2.resize(img, (512,512))
    image = Image.fromarray(img)
    #print ( image.size )
    image = ImageTk.PhotoImage(image)

    global panel
    if panel is None:
        # the first panel will store our original image
        panel = Label(image=image)
        panel.image = image
        panel.pack(side=TOP, padx=10, pady=10)
    else:
        # update the pannels
        panel.configure(image=image)
        panel.image = image

url = 'http://' + ip + ':' + port
print ( "Connecting to ", url )

sio.connect(url)

curr_idx = 0

def updateValue(event):
    new_idx = int( w1.get() )
    global curr_idx
    if ( curr_idx == new_idx ):
        return
    curr_idx = new_idx
    sio.emit('data', new_idx)



row = Frame(master)
lab = Label(row, width=15, text="Random Seed", anchor=CENTER)
ent = Entry(row ,width = 10 )
row.pack(side=LEFT, fill=X, padx=5, pady=5)
lab.pack(side=LEFT)
ent.pack(side=LEFT, fill=X)

w1 = Scale(master, from_=0, to=100, tickinterval=10,length=600, orient=HORIZONTAL)
w1.pack(side=TOP, padx=5, pady=5)
w1.set(0)
w1.bind("<B1-Motion>", updateValue)



btn = Button(master, text='Start', command = onStartClick)
btn.pack(side=TOP, padx=5, pady=5)

mainloop()