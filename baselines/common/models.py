import numpy as np
import tensorflow as tf
from baselines.a2c import utils
from baselines.a2c.utils import conv, fc, conv_to_fc, batch_to_seq, seq_to_batch
from baselines.common.mpi_running_mean_std import RunningMeanStd
import tensorflow.contrib.layers as layers

mapping = {}

def register(name):
    def _thunk(func):
        mapping[name] = func
        return func
    return _thunk

def nature_cnn(unscaled_images, **conv_kwargs):
    """
    CNN from Nature paper.
    """
    scaled_images = tf.cast(unscaled_images, tf.float32) / 255.
    activ = tf.nn.relu
    h = activ(conv(scaled_images, 'c1', nf=32, rf=8, stride=4, init_scale=np.sqrt(2),
                   **conv_kwargs))
    h2 = activ(conv(h, 'c2', nf=64, rf=4, stride=2, init_scale=np.sqrt(2), **conv_kwargs))
    h3 = activ(conv(h2, 'c3', nf=64, rf=3, stride=1, init_scale=np.sqrt(2), **conv_kwargs))
    h3 = conv_to_fc(h3)
    return activ(fc(h3, 'fc1', nh=512, init_scale=np.sqrt(2)))

@register("mlp")
def mlp(num_layers=2, num_hidden=64, activation=tf.tanh, layer_norm=False):
    """
    Stack of fully-connected layers to be used in a policy / q-function approximator

    Parameters:
    ----------

    num_layers: int                 number of fully-connected layers (default: 2)

    num_hidden: int                 size of fully-connected layers (default: 64)

    activation:                     activation function (default: tf.tanh)

    Returns:
    -------

    function that builds fully connected network with a given input tensor / placeholder
    """
    def network_fn(X):
        h = tf.layers.flatten(X)
        for i in range(num_layers):
            h = fc(h, 'mlp_fc{}'.format(i), nh=num_hidden, init_scale=np.sqrt(2))
            if layer_norm:
                h = tf.contrib.layers.layer_norm(h, center=True, scale=True)
            h = activation(h)

        return h

    return network_fn

@register("simple_rms")
def simple_rms(**simple_rms_kwargs):
    def network_fn(X):
        # receive_rate * .9 - send_rate
        # change = X[-1][3] - X[-1][5]
        received_rate = X[:,-1,3]
        send_rate = X[:,-1,5]
        delta = received_rate * tf.Variable([1.0]) - send_rate
        return delta
    return network_fn

@register("cnn")
def cnn(**conv_kwargs):
    def network_fn(X):
        return nature_cnn(X, **conv_kwargs)
    return network_fn

@register("cnn_1d")
def cnn_qd(**conv_kwargs):
    def network_fn(X):
        buffer_size = X.shape[1]
        net = X
        net = layers.conv1d(net, 5, 3, scope='cnn1d_c1')
        net = layers.conv1d(net, 5, 3, scope='cnn1d_c2')
        net = layers.conv1d(net, 1, 3, scope='cnn1d_c3')
        net = tf.reshape(net, [-1,buffer_size])
        net = fc(net, 'cnn1d_fc1', nh=16, init_scale=np.sqrt(2))
        net = tf.tanh(net)
#        tf.nn.conv1d(X, w, stride, 'SAME')
#        print(X)
        return net
    return network_fn

@register("cnn_1d_small_ac_hybrid.actor")
def cnn_qd1(**conv_kwargs):
    def network_fn(X):
        buffer_size = X.shape[1]
        net = X
        net = layers.conv1d(net, 15, 3, scope='cnn1d_c1')
        net = layers.conv1d(net, 10, 3, scope='cnn1d_c2')
        net = layers.conv1d(net, 5, 3, scope='cnn1d_c3')
        net = layers.conv1d(net, 1, 3, scope='cnn1d_cf')
        net = tf.reshape(net, [-1,buffer_size])
        net = fc(net, 'cnn1d_fc1', nh=16, init_scale=np.sqrt(2))
        net = fc(net, 'cnn1d_fc2', nh=16, init_scale=np.sqrt(2))
        net = tf.tanh(net)
#        tf.nn.conv1d(X, w, stride, 'SAME')
#        print(X)
        return net
    return network_fn

@register("cnn_1d_small_ac_hybrid.critic")
def cnn_qd1(**conv_kwargs):
    def network_fn(X, action):
        num_layers = 2
        activation = tf.tanh
        num_hidden = 64
        layer_norm = False
        net = tf.layers.flatten(X)
        for i in range(num_layers):
            net = fc(net, 'mlp_fc{}'.format(i), nh=num_hidden, init_scale=np.sqrt(2))
            if layer_norm:
                net = tf.contrib.layers.layer_norm(net, center=True, scale=True)
            net = activation(net)
        net = tf.concat([net,action], 1)
        net = fc(net, 'cnn1d_fc1', nh=16, init_scale=np.sqrt(2))
        net = tf.tanh(net)
#        tf.nn.conv1d(X, w, stride, 'SAME')
#        print(X)
        return net
    return network_fn

@register("cnn_1d_large_ac_hybrid.actor")
def cnn_qd1(**conv_kwargs):
    def network_fn(X):
        buffer_size = X.shape[1]
        net = X
        net = layers.conv1d(net, 100, 3, scope='cnn1d_c1')
        net = layers.conv1d(net, 50, 3, scope='cnn1d_c2')
        net = layers.conv1d(net, 25, 3, scope='cnn1d_c3')
        net = layers.conv1d(net, 1, 3, scope='cnn1d_cf')
        net = tf.reshape(net, [-1,buffer_size])
        net = fc(net, 'cnn1d_fc1', nh=32, init_scale=np.sqrt(2))
        net = fc(net, 'cnn1d_fc2', nh=16, init_scale=np.sqrt(2))
        net = tf.tanh(net)
#        tf.nn.conv1d(X, w, stride, 'SAME')
#        print(X)
        return net
    return network_fn

@register("cnn_1d_large_ac_hybrid.critic")
def cnn_qd1(**conv_kwargs):
    def network_fn(X, action):
        num_layers = 2
        activation = tf.tanh
        num_hidden = 64
        layer_norm = False
        net = tf.layers.flatten(X)
        for i in range(num_layers):
            net = fc(net, 'mlp_fc{}'.format(i), nh=num_hidden, init_scale=np.sqrt(2))
            if layer_norm:
                net = tf.contrib.layers.layer_norm(net, center=True, scale=True)
            net = activation(net)
        net = tf.concat([net,action], 1)
        net = fc(net, 'cnn1d_fc1', nh=32, init_scale=np.sqrt(2))
        net = fc(net, 'cnn1d_fc1', nh=16, init_scale=np.sqrt(2))
        net = tf.tanh(net)
#        tf.nn.conv1d(X, w, stride, 'SAME')
#        print(X)
        return net
    return network_fn

@register("cnn_1d_small_ac.actor")
def cnn_qd1(**conv_kwargs):
    def network_fn(X):
        buffer_size = X.shape[1]
        net = X
        net = layers.conv1d(net, 5, 3, scope='cnn1d_c1')
        net = layers.conv1d(net, 5, 3, scope='cnn1d_c2')
        net = layers.conv1d(net, 1, 3, scope='cnn1d_c3')
        net = tf.reshape(net, [-1,buffer_size])
        net = fc(net, 'cnn1d_fc1', nh=16, init_scale=np.sqrt(2))
        net = tf.tanh(net)
#        tf.nn.conv1d(X, w, stride, 'SAME')
#        print(X)
        return net
    return network_fn

@register("cnn_1d_small_ac.critic")
def cnn_qd1(**conv_kwargs):
    def network_fn(X, action):
        buffer_size = X.shape[1]
        net = X
        net = layers.conv1d(net, 5, 3, scope='cnn1d_c1')
        net = layers.conv1d(net, 5, 3, scope='cnn1d_c2')
        net = layers.conv1d(net, 1, 3, scope='cnn1d_c3')
        net = tf.reshape(net, [-1,buffer_size])
        net = tf.concat([net,action], 1)
        net = fc(net, 'cnn1d_fc1', nh=32, init_scale=np.sqrt(2))
        net = fc(net, 'cnn1d_fc3', nh=16, init_scale=np.sqrt(2))
        net = tf.tanh(net)
#        tf.nn.conv1d(X, w, stride, 'SAME')
#        print(X)
        return net
    return network_fn

@register("cnn_1d_ac.actor")
def cnn_qd1(**conv_kwargs):
    def network_fn(X):
        buffer_size = X.shape[1]
        net = X
        net = layers.conv1d(net, 20, 5, scope='cnn1d_c1')
        net = layers.conv1d(net, 15, 3, scope='cnn1d_c2')
        net = layers.conv1d(net, 10, 3, scope='cnn1d_c3')
        net = layers.conv1d(net, 5, 3, scope='cnn1d_c4')
        net = layers.conv1d(net, 1, 3, scope='cnn1d_c5')
        net = tf.reshape(net, [-1,buffer_size])
        net = fc(net, 'cnn1d_fc1', nh=16, init_scale=np.sqrt(2))
        net = tf.tanh(net)
#        tf.nn.conv1d(X, w, stride, 'SAME')
#        print(X)
        return net
    return network_fn

@register("cnn_1d_ac.critic")
def cnn_qd1(**conv_kwargs):
    def network_fn(X, action):
        buffer_size = X.shape[1]
        net = X
        net = layers.conv1d(net, 20, 5, scope='cnn1d_c1')
        net = layers.conv1d(net, 15, 3, scope='cnn1d_c2')
        net = layers.conv1d(net, 10, 3, scope='cnn1d_c3')
        net = layers.conv1d(net, 5, 3, scope='cnn1d_c4')
        net = layers.conv1d(net, 1, 3, scope='cnn1d_c5')
        net = tf.reshape(net, [-1,buffer_size])
        net = tf.concat([net,action], 1)
        net = fc(net, 'cnn1d_fc1', nh=32, init_scale=np.sqrt(2))
        net = fc(net, 'cnn1d_fc2', nh=24, init_scale=np.sqrt(2))
        net = fc(net, 'cnn1d_fc3', nh=16, init_scale=np.sqrt(2))
        net = tf.tanh(net)
#        tf.nn.conv1d(X, w, stride, 'SAME')
#        print(X)
        return net
    return network_fn

@register("cnn_1d_v1")
def cnn_qd1(**conv_kwargs):
    def network_fn(X):
        buffer_size = X.shape[1]
        net = X
        net = layers.conv1d(net, 20, 5, scope='cnn1d_c1')
        net = layers.conv1d(net, 15, 3, scope='cnn1d_c2')
        net = layers.conv1d(net, 10, 3, scope='cnn1d_c3')
        net = layers.conv1d(net, 5, 3, scope='cnn1d_c4')
        net = layers.conv1d(net, 1, 3, scope='cnn1d_c5')
        net = tf.reshape(net, [-1,buffer_size])
        net = fc(net, 'cnn1d_fc1', nh=16, init_scale=np.sqrt(2))
        net = tf.tanh(net)
#        tf.nn.conv1d(X, w, stride, 'SAME')
#        print(X)
        return net
    return network_fn


@register("cnn_small")
def cnn_small(**conv_kwargs):
    def network_fn(X):
        h = tf.cast(X, tf.float32) / 255.

        activ = tf.nn.relu
        h = activ(conv(h, 'c1', nf=8, rf=8, stride=4, init_scale=np.sqrt(2), **conv_kwargs))
        h = activ(conv(h, 'c2', nf=16, rf=4, stride=2, init_scale=np.sqrt(2), **conv_kwargs))
        h = conv_to_fc(h)
        h = activ(fc(h, 'fc1', nh=128, init_scale=np.sqrt(2)))
        return h
    return network_fn


@register("lstm")
def lstm(nlstm=128, layer_norm=False):
    """
    Builds LSTM (Long-Short Term Memory) network to be used in a policy.
    Note that the resulting function returns not only the output of the LSTM
    (i.e. hidden state of lstm for each step in the sequence), but also a dictionary
    with auxiliary tensors to be set as policy attributes.

    Specifically,
        S is a placeholder to feed current state (LSTM state has to be managed outside policy)
        M is a placeholder for the mask (used to mask out observations after the end of the episode, but can be used for other purposes too)
        initial_state is a numpy array containing initial lstm state (usually zeros)
        state is the output LSTM state (to be fed into S at the next call)


    An example of usage of lstm-based policy can be found here: common/tests/test_doc_examples.py/test_lstm_example

    Parameters:
    ----------

    nlstm: int          LSTM hidden state size

    layer_norm: bool    if True, layer-normalized version of LSTM is used

    Returns:
    -------

    function that builds LSTM with a given input tensor / placeholder
    """

    def network_fn(X, nenv=1):
        nbatch = X.shape[0]
        nsteps = nbatch // nenv

        h = tf.layers.flatten(X)

        M = tf.placeholder(tf.float32, [nbatch]) #mask (done t-1)
        S = tf.placeholder(tf.float32, [nenv, 2*nlstm]) #states

        xs = batch_to_seq(h, nenv, nsteps)
        ms = batch_to_seq(M, nenv, nsteps)

        if layer_norm:
            h5, snew = utils.lnlstm(xs, ms, S, scope='lnlstm', nh=nlstm)
        else:
            h5, snew = utils.lstm(xs, ms, S, scope='lstm', nh=nlstm)

        h = seq_to_batch(h5)
        initial_state = np.zeros(S.shape.as_list(), dtype=float)

        return h, {'S':S, 'M':M, 'state':snew, 'initial_state':initial_state}

    return network_fn


@register("cnn_lstm")
def cnn_lstm(nlstm=128, layer_norm=False, **conv_kwargs):
    def network_fn(X, nenv=1):
        nbatch = X.shape[0]
        nsteps = nbatch // nenv

        h = nature_cnn(X, **conv_kwargs)

        M = tf.placeholder(tf.float32, [nbatch]) #mask (done t-1)
        S = tf.placeholder(tf.float32, [nenv, 2*nlstm]) #states

        xs = batch_to_seq(h, nenv, nsteps)
        ms = batch_to_seq(M, nenv, nsteps)

        if layer_norm:
            h5, snew = utils.lnlstm(xs, ms, S, scope='lnlstm', nh=nlstm)
        else:
            h5, snew = utils.lstm(xs, ms, S, scope='lstm', nh=nlstm)

        h = seq_to_batch(h5)
        initial_state = np.zeros(S.shape.as_list(), dtype=float)

        return h, {'S':S, 'M':M, 'state':snew, 'initial_state':initial_state}

    return network_fn


@register("cnn_lnlstm")
def cnn_lnlstm(nlstm=128, **conv_kwargs):
    return cnn_lstm(nlstm, layer_norm=True, **conv_kwargs)


@register("conv_only")
def conv_only(convs=[(32, 8, 4), (64, 4, 2), (64, 3, 1)], **conv_kwargs):
    '''
    convolutions-only net

    Parameters:
    ----------

    conv:       list of triples (filter_number, filter_size, stride) specifying parameters for each layer.

    Returns:

    function that takes tensorflow tensor as input and returns the output of the last convolutional layer

    '''

    def network_fn(X):
        out = tf.cast(X, tf.float32) / 255.
        with tf.variable_scope("convnet"):
            for num_outputs, kernel_size, stride in convs:
                out = layers.convolution2d(out,
                                           num_outputs=num_outputs,
                                           kernel_size=kernel_size,
                                           stride=stride,
                                           activation_fn=tf.nn.relu,
                                           **conv_kwargs)

        return out
    return network_fn

def _normalize_clip_observation(x, clip_range=[-5.0, 5.0]):
    rms = RunningMeanStd(shape=x.shape[1:])
    norm_x = tf.clip_by_value((x - rms.mean) / rms.std, min(clip_range), max(clip_range))
    return norm_x, rms


def get_network_builder(name):
    """
    If you want to register your own network outside models.py, you just need:

    Usage Example:
    -------------
    from baselines.common.models import register
    @register("your_network_name")
    def your_network_define(**net_kwargs):
        ...
        return network_fn

    """
    if callable(name):
        return name
    elif name in mapping:
        return mapping[name]
    else:
        raise ValueError('Unknown network type: {}'.format(name))
