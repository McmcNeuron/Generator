"""Basic visualization of neurite morphologies using matplotlib."""
import numpy as np
import sys
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cm
import matplotlib.animation as animation
import pylab as pl
from PIL import Image
from numpy.linalg import inv
from McNeuron import Neuron
import neuron_util
import matplotlib
from matplotlib import collections as mc
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection
import itertools
sys.setrecursionlimit(10000)

def get_2d_image(path, size, dpi, background, show_width):

    neu = McNeuron.Neuron(file_format = 'swc without attributes', input_file=path)
    depth = neu.location[2,:]
    p = neu.location[0:2,:]
    widths= 5*neu.diameter
    widths[0:3] = 0
    m = min(depth)
    M = max(depth)
    depth =  background * ((depth - m)/(M-m))
    colors = []
    lines = []
    patches = []

    for i in range(neu.n_soma):
        x1 = neu.location[0,i]
        y1 = neu.location[1,i]
        r = 1*neu.diameter[i]
        circle = Circle((x1, y1), r, color = str(depth[i]), ec = 'none',fc = 'none')
        patches.append(circle)

    pa = PatchCollection(patches, cmap=matplotlib.cm.gray)
    pa.set_array(depth[0]*np.zeros(neu.n_soma))

    for i in range(len(neu.nodes_list)):
        colors.append(str(depth[i]))
        j = neu.parent_index[i]
        lines.append([(p[0,i],p[1,i]),(p[0,j],p[1,j])])
    if(show_width):
        lc = mc.LineCollection(lines, colors=colors, linewidths = widths)
    else:
        lc = mc.LineCollection(lines, colors=colors)

    fig, ax = plt.subplots()
    ax.add_collection(lc)
    ax.add_collection(pa)
    fig.set_size_inches([size + 1, size + 1])
    fig.set_dpi(dpi)
    plt.axis('off')
    plt.xlim((min(p[0,:]),max(p[0,:])))
    plt.ylim((min(p[1,:]),max(p[1,:])))
    plt.draw()
    data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
    data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    border = (dpi/2)
    return np.squeeze(data[border:-border,border:-border,0])


def projection_on_plane(neuron,
                        orthogonal_vec=np.array([0, 0, 1]),
                        rotation=np.array([0.0])):
    """
    Parameters
    ----------
    neuron: Neuron
        the neuron object to be plotted.
    orthogonal_vec: numpy array
        the orthogonal direction for projecting.

    return
    ------

    dependency
    ----------
    This function needs following data from neuron:
        location
        diameter
        parent_index
    """
    # projection all the nodes on the plane and finding the right pixel for their centers
    normal_1 = orthogonal_vec/np.sqrt(sum(orthogonal_vec**2))
    normal_2 = np.zeros(3)
    normal_2[1] = 1
    A = neuron_util.get_swc_matrix(neuron)

    new_neuron = Neuon()

    new_neuron.location = 1
    image = np.zeros(resolution)
    shift = resolution[0]/2
    normal_vec1 = np.array([0,0,1])
    normal_vec2 = np.array([0,1,0])
    P = project_points(neuron.location, normal_vec1, normal_vec2)

    for n in neuron.nodes_list:
        if(n.parent != None):
            n1, n2, dis = project_point(n, normal_vec1, normal_vec2)
            pix1 = np.floor(n1/gap) + shift
            pix2 = np.floor(n2/gap) + shift
            if(0 <= pix1 and 0 <= pix2 and pix1<resolution[0] and pix2 < resolution[1]):
                image[pix1, pix2] = dis
    return image

def project_points(location, normal_vectors):
    """
    Parameters
    ----------
    normal_vectors : array of shape [2,3]
        Each row should a normal vector and both of them should be orthogonal.

    location : array of shape [3, n_nodes]
        the location of n_nodes number of points

    Returns
    -------
    cordinates: array of shape [2, n_nodes]
        The cordinates of the location on the plane defined by the normal vectors.
    """
    cordinates = np.dot(normal_vectors, location)
    return cordinates

def depth_points(location, orthogonal_vector):
    """
    Parameters
    ----------
    orthogonal_vector : array of shape [3]
        orthogonal_vector that define the plane

    location : array of shape [3, n_nodes]
        the location of n_nodes number of points

    Returns
    -------
    depth: array of shape [n_nodes]
        The depth of the cordinates when they project on the plane.
    """
    depth = np.dot(orthogonal_vector, location)
    return depth

def make_image(neuron, A, scale_depth, index_neuron):
    normal_vectors = A[0:2,:]
    orthogonal_vector = A[2,:]
    depth = depth_points(neuron.location, orthogonal_vector)
    p = project_points(neuron.location, normal_vectors)
    m = min(depth)
    M = max(depth)
    depth =  scale_depth * ((depth - m)/(M-m))
    colors = []
    lines = []
    for i in range(len(neuron.nodes_list)):
        colors.append((depth[i],depth[i],depth[i],1))
        j = neuron.parent_index[i]
        lines.append([(p[0,i],p[1,i]),(p[0,j],p[1,j])])
    lc = mc.LineCollection(lines, colors=colors, linewidths=2)
    fig, ax = pl.subplots()
    ax.add_collection(lc)
    pl.axis('off')
    pl.xlim((min(p[0,:]),max(p[0,:])))
    pl.ylim((min(p[1,:]),max(p[1,:])))
    Name = "neuron" + str(index_neuron[0]+1) + "resample" + str(index_neuron[1]+1) + "angle" + str(index_neuron[2]+1) + ".png"
    fig.savefig(Name,figsize=(6, 6), dpi=80)
    img = Image.open(Name)
    img.load()
    data = np.asarray( img, dtype="int32" )
    data = data[:,:,0]
    return data


def make_six_matrix(A):
    six = []
    six.append(A[[0,1,2],:])
    six.append(A[[0,2,1],:])
    six.append(A[[1,2,0],:])
    six.append(A[[1,0,2],:])
    six.append(A[[2,0,1],:])
    six.append(A[[2,1,0],:])
    return six

def make_six_images(neuron,scale_depth,neuron_index, kappa):
    #A = random_unitary_basis(kappa)
    A = np.eye(3)
    six = make_six_matrix(A)
    D = []
    for i in range(6):
        a = np.append(neuron_index,i)
        D.append(make_image(neuron, six[i], scale_depth, a))
    return D

def generate_data(path, scale_depth, n_camrea, kappa):
    """
    input
    -----
    path : list
        list of all the pathes of swc. each element of the list should be a string.

    scale_depth : float in the interval [0,1]
        a value to differentiate between the background and gray level in the image.

    n_camera : int
        number of different angles to set the six images. For each angle, six images will be generated (up,down and four sides)

    kappa : float
        The width of the distribution that the angles come from. Large value for kappa results in the angles close to x aixs
        kappa = 1 is equvalent to the random angle.

    output
    ------
    Data : list of length
    """
    Data = []
    for i in range(len(path)):
        print path[i]
        neuron = Neuron(file_format = 'swc without attributes', input_file=path[i])
        if(len(neuron.nodes_list) != 0):
            for j in range(n_camrea):
                D = np.asarray(make_six_images(neuron, scale_depth, np.array([i,j]), kappa))
                Data.append(D)
    return Data

def plot_2D(neuron,
            background=1,
            show_width=False,
            show_depth=False,
            size_x=5,
            size_y=5,
            dpi=80,
            line_width=1,
            show_soma=False,
            give_image=False,
            red_after=False,
            node_red=0,
            translation=(0, 0),
            scale_on=False,
            scale=(1, 1),
            save=[]):

    depth = neuron.location[2, :]
    p = neuron.location[0:2, :]
    if scale_on:
        p[0, :] = scale[0] * (p[0, :]-min(p[0, :]))/(max(p[0, :]) - min(p[0, :]))
        p[1, :] = scale[1] * (p[1, :]-min(p[1, :]))/(max(p[1, :]) - min(p[1, :]))
    widths= neuron.diameter
    #widths[0:3] = 0
    m = min(depth)
    M = max(depth)
    depth = background * ((depth - m)/(M-m))
    colors = []
    lines = []
    patches = []

    for i in range(neuron.n_soma):
        x1 = neuron.location[0, i] + translation[0]
        y1 = neuron.location[1, i] + translation[1]
        r = widths[i]
        circle = Circle((x1, y1), r, color=str(depth[i]), ec='none', fc='none')
        patches.append(circle)

    pa = PatchCollection(patches, cmap=matplotlib.cm.gray)
    pa.set_array(depth[0]*np.zeros(neuron.n_soma))

    for i in range(neuron.n_node):
        colors.append(str(depth[i]))
        j = neuron.parent_index[i]
        lines.append([(p[0,i] + translation[0],p[1,i] + translation[1]),(p[0,j] + translation[0],p[1,j] + translation[1])])

    if(show_width):
        if(show_depth):
            lc = mc.LineCollection(lines, colors=colors, linewidths = line_width*widths)
        else:
            lc = mc.LineCollection(lines, linewidths = line_width*widths)
    else:
        if(show_depth):
            lc = mc.LineCollection(lines, colors=colors, linewidths = line_width)
        else:
            lc = mc.LineCollection(lines, linewidths=line_width, color = 'k')

    if(red_after):
        colors = np.zeros(len(lines))
        I = neuron.connecting_after_node(node_red)
        colors[I] = 1
        #lc = mc.LineCollection(lines, color=colors)
        # for i in I1:
        #     j = neuron.parent_index[i]
        #     line1.append([(p[0,i],p[1,i]),(p[0,j],p[1,j])])
        #     lc1 = mc.LineCollection(line1, linewidths = 2*line_width, color = 'r')
        # for i in I2:
        #     j = neuron.parent_index[i]
        #     line2.append([(p[0,i],p[1,i]),(p[0,j],p[1,j])])
        #     lc2 = mc.LineCollection(line2, linewidths = line_width, color = 'k')
            #return (lc1, lc2, (min(p[0,:]),max(p[0,:])), (min(p[1,:]),max(p[1,:])))
        #else:
            #return (lc, (min(p[0,:]),max(p[0,:])), (min(p[1,:]),max(p[1,:])))
    else:
        fig, ax = plt.subplots()
        ax.add_collection(lc)
        if(show_soma):
            ax.add_collection(pa)
        fig.set_size_inches([size_x + 1, size_y + 1])
        fig.set_dpi(dpi)
        plt.axis('off')
        plt.xlim((min(p[0,:]),max(p[0,:])))
        plt.ylim((min(p[1,:]),max(p[1,:])))

        if(len(save)!=0):
            plt.savefig(save, format = "eps")
        plt.show()

def plot_evolution_mcmc(mcmc):
    """
    Showing the evolution of MCMC during the operation.
    """
    k = 0
    for n in mcmc.evo:
        print('step %s' % k)
        k += 1
        plot_2D(n)

def decompose_immediate_children(matrix):
    """
    Parameters
    ----------
    matrix : numpy array of shape (n,n)
        The matrix of connetion. matrix(i,j) is one is j is a grandparent of i.

    Return
    ------
    L : list of numpy array of square shape
        L consists of decomposition of matrix to immediate children of root.
    """
    a = matrix.sum(axis = 1)
    (children,) = np.where(a == 1)
    L = []
    #print(children)
    for ch in children:
        (ind,) = np.where(matrix[:,ch]==1)
        ind = ind[ind!=ch]
        L.append(matrix[np.ix_(ind,ind)])
    p = np.zeros(len(L))
    for i in range(len(L)):
        p[i] = L[i].shape[0]
    s = np.argsort(p)
    List = []
    for i in range(len(L)):
        List.append(L[s[i]])
    return List

def box(x_min, x_max, y, matrix, line):
    """
    The box region for each node in the tree.

    """
    L = decompose_immediate_children(matrix)
    length = np.zeros(len(L)+1)
    for i in range(1,1+len(L)):
        length[i] = L[i-1].shape[0] + 1

    for i in range(len(L)):
        x_left = x_min + (x_max-x_min)*(sum(length[0:i+1])/sum(length))
        x_right = x_min + (x_max-x_min)*(sum(length[0:i+2])/sum(length))
        line.append([((x_min + x_max)/2., y), ((x_left + x_right)/2., y-1)])
        if(L[i].shape[0] > 0):
            box(x_left, x_right, y-1, L[i], line)
    return line


def plot_dendrogram(neuron,
                    show_all_nodes=False,
                    save=[]):
    """
    Showing the dendogram of the neuron.

    Parameters
    ----------
    neuron: Neuron
        the input neuron
    show_all_nodes: boolean
        if Ture, it will show all the nodes, otherwise only the main points are
        taking into account.
    save: str
        the path to save the figure.
    """
    # for swc format: neuron[:,-1]
    if isinstance(neuron, np.ndarray):
        a = neuron
    else:
        a = neuron.parent_index + 1
        a[0] = 0
        a = a.astype(int)

    A = np.zeros([a.shape[0]+1, a.shape[0]+1])
    A[np.arange(1, a.shape[0]+1), a] = 1
    B = inv(np.eye(a.shape[0]+1) - A)
    l = box(0., 1., 0., B, [])
    min_y = 0
    for i in l:
        min_y = min(min_y, i[1][1])
    lc = mc.LineCollection(l)
    fig, ax = plt.subplots()
    ax.add_collection(lc)
    plt.axis('off')
    plt.xlim((0, 1))
    plt.ylim((min_y, 0))
    plt.draw()
    if(len(save) != 0):
        plt.savefig(save, format="eps")

def show_database(collection):
    for n in collection.database:
        plot_2D(n)
    for name in collection.value_all:
        print name
        print(collection.mean_value[name])
        print(collection.std_value[name])
        print('\n')
    for name in collection.hist_features.keys():
        print name
        m = collection.mean_hist[name]
        v = collection.std_hist[name]/10.
        plt.fill_between(x=collection.hist_features[name][1:], y1=m+v, y2=m-v)
        plt.show()
    plt.imshow(collection.mean_vec_value['pictural image xy'].reshape(10, 10))
    plt.colorbar()
    plt.show()
    plt.imshow(collection.mean_vec_value['pictural image xy tips'].reshape(10, 10))
    plt.colorbar()
    plt.show()
    for name in collection.vec_value:
        print name
        m = collection.mean_vec_value[name]
        v = collection.std_vec_value[name]/10.
        plt.fill_between(x=range(0, len(m)), y1=m+v, y2=m-v)
        plt.show()


def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Purples):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float').T / cm.sum(axis=1).astype('float')
        cm = cm.T
        cm = np.floor(cm*100.).astype(int)
        print cm

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    #plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=90)
    plt.yticks(tick_marks, classes)




    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j],
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    #plt.tight_layout()
    plt.ylabel('True label')
    #plt.xlabel('Predicted label')

def get_segment_collection_neuron(collection,
                                  row=None,
                                  column=None,
                                  scale=None):
    lines = []
    index = 0
    if row is None:
        row = np.floor(np.sqrt(len(collection)))
    if column is None:
        column = np.floor(float(len(collection))/row) + 1
    if scale is None:
        scale = 2.5 * column * 500
    for r in np.arange(row):
        for col in np.arange(column):
            if(index < len(collection)):
                neuron = collection[index]
                index += 1
                p = neuron.location[0:2, :]
                p = p/scale
                for i in range(neuron.n_node):
                    j = neuron.parent_index[i]
                    lines.append([(p[0, i] + col/column, p[1, i] + 1 - r/row),
                                  (p[0, j] + col/column, p[1, j] + 1 - r/row)])
    lc = mc.LineCollection(lines, color='k')
    return lc

def get_segment_collection(neuron):
    lines = []
    p = neuron.location[0:2, :]
    p = p/(.2*p.max())
    for i in range(p.shape[1]):
        j = neuron.parent_index[i]
        if(j>=0):
            lines.append([(p[0,i] ,p[1,i]),
                        (p[0,j],p[1,j] )])
    lc = mc.LineCollection(lines, color = 'k')
    return lc

def evolution_with_increasing_node(neuron):
    for i in range(10):
        m = neuron_util.get_swc_matrix(neuron)
        m = m[40*i:, :]
        I = m[:, 6]
        I = I - 40*i
        I[I < 0] = -1
        m[:, 6] = I
        n = Neuron(input_file=m, input_format='Matrix of swc without Node class')
        lc = get_segment_collection(n)
        fig = plt.figure(figsize=(4, 4))
        fig, ax = plt.subplots()
        ax.add_collection(lc)
        plt.axis('off')
        plt.xlim((-6, 6))
        plt.ylim((-6, 6))
        #plt.draw()
        plt.show()
