#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from sys import argv
"""
Usage: python dump2config.py dump.xyz config.out.
by Lianchi Liu
Mar 20th. 2011
"""

def read_dumpfile(dumpfile):
	dumplist = []
	for i in dumpfile:
		if i.count("TIMESTEP") != 0:
			dumplist.append("E N D")
			temp_timestep = dumpfile.readline()
			dumpfile.readline()
			dumplist.append(dumpfile.readline())
			dumplist.append("Timestep "+temp_timestep)
			dumpfile.readline()
			boxinf = [dumpfile.readline(), dumpfile.readline(), dumpfile.readline()]
			dumpfile.readline()
		else:
			dumplist.append(i)
	dumplist.remove("E N D")
	dumplist.append("E N D")
	return dumplist

def get_typedic(datafile):
	typedic = {}
	for i in datafile:
		if len(i.split()) > 2 and i.split()[2] == "#":
			typedic[i.split()[0]] = i.split()[3]
	return typedic

if __name__ == '__main__':
	
	if len(argv) < 2:
		print("Usage: python dump2config.py dump.xyz xyzfile.xyz.")
		sys.exit()

	datafile = open("lammps.data")
	typedic = get_typedic(datafile)
	dumpfile = open(argv[1])
	newfile = open(argv[2], 'w')
	#print read_dumpfile(dumpfile)
	for i in read_dumpfile(dumpfile):
		if len(i.split()) == 1:
			natoms = i.split()
		if len(i.split()) == 2:
			newfile.write("# Timestep %s\n#\n" %i.split()[1])
			newfile.write("# Unit cell lattice vectors:\n")
			newfile.write("# 80.000000 0.000000000 0.000000000\n")
			newfile.write("# 0.000000000 80.000000 0.000000000\n")
			newfile.write("# 0.000000000 0.000000000 80.000000\n")
			newfile.write("#\n")
			newfile.write("# Unit cell origin:\n")
			newfile.write("# 0.000000000 0.000000000 0.000000000\n")
			newfile.write("#\n")
			newfile.write("# Number of particles %s\n" %int(natoms[0]))
			newfile.write("#\n")
			newfile.write("# Particle positions\n")
		elif len(i.split()) >= 4:
			newfile.write(" %s  %s  %s  %s  %12.6e  %12.6e  %12.6e  %12.6e  %12.6e  %12.6e\n" \
							%(int(i.split()[0]), \
							typedic[i.split()[1]], \
							"0", \
							"0.000000e+00", \
							float(i.split()[2]), \
							float(i.split()[3]), \
							float(i.split()[4]), \
							float(i.split()[5]), \
							float(i.split()[6]), \
							float(i.split()[7])))
		elif i.split() == ["E", "N", "D"]:
			newfile.write("#\n")
 
	datafile.close()
	dumpfile.close()
	newfile.close()
