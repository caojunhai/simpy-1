""" A python shell of MC simulation calling LAMMPS as energy engine to get ReaxFF 
energies.

LOG:
Fri Jun 21 23:21:37 PDT 2013
1. Swap move: exchange the atom type of two atoms

@todo: Restraint to avoid Al-O-AL
@todo: Update the coordinations from out.pdb
@todo: deposit water molecules 
@todo: find water molecules from reaxFF simulation
"""
import sys, os
import random
import ConfigParser, string
import socket

LIB = ''

if socket.gethostname() == "cluster.hpc.org":
    LIB = "/home/chengtao/packages/simpy/simpy/lib"
elif socket.gethostname() == "tao-laptop":
    LIB = "/home/tao/Nutstore/code/simupy/lib"
elif socket.gethostname() == "atom.wag.caltech.edu":
    LIB = "/net/hulk/home6/chengtao/soft/simpy/lib"

LIB = "/net/hulk/home6/chengtao/soft/simpy/lib"
sys.path.insert(0 , LIB)

from mytype import System, Molecule, Atom
from pdb import Pdb
from index import Group
from output_conf import toReaxLammps, toGeo, toPdb
from utilities import get_dist
import popen2
import shutil

# PBC specified to model.pdb
# @improve: a variable read from pdb input

def welcome():
    print "-"*20 + "Welcome to simupy MC" + "-"*20
    print "Every time you see the world, you see yourself"
    print "                                          xxxx"
    print "-"*20 + "--------------------" + "-"*20

class MC():
    """MC simulation parameters
    """
    def __init__(self,):
        self.pdbfile = ''
        self.indexfile = ''
        self.controlfile = ''
        self.swap_flag = 0
        self.swap_grp1 = []
        self.swap_grp1_atms = []
        self.swap_grp2 = []
        self.swap_grp2_atms = []
        self.nsteps = 0
        self.step = 0
	self.log = 'log.mc'
	self.code = 'lammps'
        self.mpi = 1
        self.mpicode = ''

def read_control(mc):
    """Read the control file
    """
    print "Reading the control file ...."
    cf = ConfigParser.ConfigParser()
    cf.read("control")

    s = cf.sections()  
    if "MC" in s:
        print "    Simulation type: MC simulations"
        o = cf.options("MC")  
        if "swap" in o:
            mc.swap_flag = cf.getint("MC", "swap")
            if mc.swap_flag:
                print '    swap move'  
                if "swap group 1" in o:
                    mc.swap_grp1 = cf.get("MC", "swap group 1").strip().split()
                else:
                    sys.stderr.write("Error: No swap group 1 was assigned\n")
                    exit()
                if "swap group 2" in o:
                    mc.swap_grp2 = cf.get("MC", "swap group 2").strip().split()
                else:
                    sys.stderr.write("Error: No swap group 2 was assigned\n")
                    exit()
                assert len(mc.swap_grp1) == len(mc.swap_grp2)
        if "mc steps" in o:
            mc.nsteps = cf.getint("MC", "mc steps")
        else:
            sys.stderr.write("Error: No simulation steps assigned")
            exit()
    if "RUN" in s:
        print "    Detail simulation settings"
        o = cf.options("RUN")  
        if "code" in o:
            mc.code = cf.get("RUN", "code").strip() 
            print "        using %s"%mc.code
        if "mpi" in o:
            mc.mpi = int(cf.get("RUN", "mpi").strip())
            print "        using %d cpu(s)"%mc.mpi
            if mc.mpi > 1:
                mc.mpicode = "mpirun -np %d"%mc.mpi

def res_aloal(mc, sim, n, a1, a2):
    # @note: this is hard coded.
    nres_prev = 0
    nres_now = 0
    cutoff = 3.6
    grp = mc.swap_grp2_atms[n]

    for i in range(len(grp)):
        if grp[i] == a2:
            pass
        else:
            r = get_dist(sim.atoms[a2].x, sim.atoms[grp[i]].x, sim.pbc)
            #print r, a2, grp[i]
            if r < cutoff:
                nres_prev += 1

    for i in range(len(grp)):
        if grp[i] == a2:
            pass
        else:
            r = get_dist(sim.atoms[a1].x, sim.atoms[grp[i]].x, sim.pbc)
            #print r, a2, grp[i]
            if r < cutoff:
                nres_now += 1
    return nres_now - nres_prev

def get_energy(mc, sim, grp):
    """get reaxFF energy by calling LAMMPS externally
    """
    ener = 0.0
    toReaxLammps(sim)
    f1, f2, f3 = popen2.popen3("%s %s -in lammps_input"%(mc.mpicode, mc.code))
    for i in f1:
        if i.strip().startswith("PotEng"):
            tokens = i.strip().split()
            n = tokens.index("PotEng")
            ener = float(tokens[n + 2])
    return ener

def assign_swap_grps(mc, sim, grp):
    """ Assign the atoms in the swap group
    """
    print "Assigning swap groups ..."
    for i in range(len(mc.swap_grp1)):
        name = mc.swap_grp1[i]
        if name in grp.names:
            n = grp.names.index(name)
            mc.swap_grp1_atms.append(grp.groups[n])
            print "    swap group 1 %s with %d atoms"%(name, len(grp.groups[n]))
        else:
            print "No group %s defined in the index file!"%name
            exit()
        
    for i in range(len(mc.swap_grp2)):
        name = mc.swap_grp2[i]
        if name in grp.names:
            n = grp.names.index(name)
            mc.swap_grp2_atms.append(grp.groups[n])
            print "    swap group 2 %s with %d atoms"%(name, len(grp.groups[n]))
        else:
            print "No group %s defined in the index file!"%name
            exit()

def mc_swap(mc, sim, grp, log):
    """MC swap move
    """
    e_old = get_energy(mc, sim, grp)
    nres = 1
    while(nres > 0):
        nres = 0
        i = random.randint(0, len(mc.swap_grp1) - 1)
        n1 = random.randint(0, len(mc.swap_grp1_atms[i]) - 1)
        a1 = mc.swap_grp1_atms[i][n1]
        n2 = random.randint(0, len(mc.swap_grp2_atms[i]) - 1)
        a2 = mc.swap_grp2_atms[i][n2]
        nres = res_aloal(mc, sim, i, a1, a2)

    #switch ID
    tmp = sim.atoms[a1].type1
    sim.atoms[a1].type1 = sim.atoms[a2].type1
    sim.atoms[a2].type1 = tmp

    log.write("    swap move: ")
    log.write("atom 1: %5d atom 2: %5d "%(a1+1, a2+1))

    e_new = get_energy(mc, sim, grp)

    log.write("E_old = %.3f, "%e_old)
    log.write("E_new= %.3f "%e_new)

    if e_old >= e_new:
        mc.swap_grp1_atms[i][n1] = a2
        mc.swap_grp1_atms[i][n2] = a1
        log.write("accept\n")
    else:
        log.write("regject\n")
        tmp = sim.atoms[a1].type1
        sim.atoms[a1].type1 = sim.atoms[a2].type1
        sim.atoms[a2].type1 = tmp
    log.flush()

def mc_moves(mc, sim, grp, log):
    """ mc moves
    """
    if mc.swap_flag == 1:
        mc_swap(mc, sim, grp, log)

def monte_carlo():
    """ a python shell for Monte Carlo reaxFF simulation'
    """
    welcome()
    mc = MC()
    # read the pdb file
    print("Reading input pdbfile")
    pdbfile = "model.pdb"
    a = Pdb(pdbfile)
    sim = a.parser()
    sim.assignEleTypes()
    sim.assignAtomTypes()
    # read the control file
    read_control(mc)
    # read index file
    indexfile = "index.ndx"
    grp = Group(indexfile)

    # system init
    log = open(mc.log, "w")

    if mc.swap_flag == 1:
        assign_swap_grps(mc, sim, grp)
    
    print "Starting simulation:"
    for i in range(mc.nsteps):
        print("Running step %d"%i)
        log.write("step %-6d"%i)
        mc_moves(mc, sim, grp, log)
        shutil.copy("out.data", "out.data.%06d"%i)
        shutil.copy("dump.lmp", "dump.lmp.%06d"%i)

    toReaxLammps(sim, "lammps.data.final")
    log.close()

if __name__ == "__main__":
    monte_carlo()
