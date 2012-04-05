import math

def magnitude(v):
    return math.sqrt(sum(v[i]*v[i] for i in range(len(v))))

def add(u, v):
    return [ u[i]+v[i] for i in range(len(u)) ]

def sub(u, v):
    return [ u[i]-v[i] for i in range(len(u)) ]

def dot(u, v):
    return sum(u[i]*v[i] for i in range(len(u)))

def normalize(v):
    vmag = magnitude(v)
    if vmag:
        a = [ v[i]/vmag  for i in range(len(v)) ]
    else:
        a = [ 0  for i in range(len(v)) ]

    return a
    
def percent(v):
    vmag = float(sum(v))

    if vmag:
        a = [ v[i]/vmag  for i in range(len(v)) ]
    else:
        a = [ 0  for i in range(len(v)) ]

    return a
    
