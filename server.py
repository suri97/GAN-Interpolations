import socketio
import eventlet.wsgi
import argparse
from flask import Flask
import numpy as np
import pickle
import scipy.ndimage
import tensorflow as tf
import cv2

tf.InteractiveSession()

app = Flask(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--ip', type=str,
                    help='Enter IP address for socket', default = '0.0.0.0')

parser.add_argument('--port', type=str,
                    help='Port', default = '8080')

parser.add_argument('--path', type=str,
                    help='Enter path to saved model file')


args = parser.parse_args()

ip = args.ip
port = args.port
path = args.path

sio = socketio.Server()

num_frames = 100
grid_size = [1,1]

with open(path, 'rb') as file:
    G, D, Gs = pickle.load(file)

smoothing_sec=1.0
mp4_fps=5
all_latents = None
labels = None

def build_image(idx):
    image = Gs.run(all_latents[idx], labels)
    image = np.clip(np.rint((image + 1.0) / 2.0 * 255.0), 0.0, 255.0).astype(np.uint8)  # [-1,1] => [0,255]
    image = image.transpose(0, 2, 3, 1)  # NCHW => NHWC
    #print ( image.shape )
    _, img_encoded = cv2.imencode('.jpg', image[0])
    return img_encoded.tostring()

@sio.on('begin')
def on_start(sid,data):
    params = data
    random_state = np.random.RandomState( params['seed'] )
    shape = [num_frames, np.prod(grid_size)] + Gs.input_shape[1:]  # [frame, image, channel, component]
    global all_latents
    all_latents = random_state.randn(*shape).astype(np.float32)
    all_latents = scipy.ndimage.gaussian_filter(all_latents, [smoothing_sec * mp4_fps] + [0] * len(Gs.input_shape),
                                                mode='wrap')
    all_latents /= np.sqrt(np.mean(np.square(all_latents)))
    global labels
    labels = np.zeros([num_frames] + Gs.input_shapes[1][1:])
    sio.emit('img', build_image(params['idx']) )

@sio.on('data')
def on_rec(sid, idx):
    #print ("New idx ",idx )
    sio.emit('img', build_image(idx) )

app = socketio.Middleware(sio, app)
eventlet.wsgi.server(eventlet.listen((ip, int(args.port) )), app)