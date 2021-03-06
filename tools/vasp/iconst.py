"""
Generate 
"""

import math
from operator import itemgetter

class Neighbor():
    def __init__(self):
        self.nmax = 100
        self.rcut = 5.0
        self.rc = 1.4

class Atom():
    def __init__(self):
        self.id = 0
        self.x = [0.0, 0.0, 0.0]
        
def parse_data():
    atoms = []
    f = open("lammps.data", "r")
    for i in f:
        if i.strip().startswith("Atoms"):
            break
    for i in f:
        tokens = i.strip().split()
        if len(tokens) == 6:
            a = Atom()
            a.id = int(tokens[0])
            a.x = [float(j) for j in tokens[3:]]
            atoms.append(a)
    return atoms
    
def parse_evdw(id):
    f = open("lammps.evdw.0", "r")

    H_near = []

    counter = 0
    for i in f:
        if counter < 2:
            pass
        else:
            tokens = i.strip().split()
            a1 = int(tokens[0])
            a2 = int(tokens[1])
            if a1 == id or a2 == id:
                if a1 > 98 or a2 > 98:
                    H_near.append([float(j) for j in tokens])
        counter += 1

    f.close()
    data = sorted(H_near, key=itemgetter(2))
    return data


def find_neighbor(data, atoms, nb):
    nmax = nb.nmax
    rcut = nb.rcut
    rc = nb.rc
    nrcut = 0.001

    ne = []
    counter = 0
    for i in data:
        id1 = int(i[0])
        id2 = int(i[1])
        r = float(i[2])
        nr = (1-math.pow(r/rc, 9))/(1-math.pow(r/rc, 14))
        if counter >= nmax:
            break
        elif r > rcut:
            break
        elif nrcut > nr:
            break
        else:
            print "%10d%10d%12.4f%12.4f%12.4f"%(id1, id2, r, nr, atoms[id2-1].x[2])
            ne.append([id1, id2, r, nr])
        counter += 1
    o = open("ICONST", "w")
    for i in ne:
        o.write("R %10d %10d 0\n"%(i[0], i[1]))
    o.write("D ")
    for i in range(len(ne)):
        o.write("%.2f "%rc)
    o.write("5\n")
    
def main():
    id = 96
    atoms = parse_data()
    data = parse_evdw(id)
    nb = Neighbor()
    nb.rc = 1.3
    nb.rcut = 7.0
    
    find_neighbor(data, atoms, nb)

main()
