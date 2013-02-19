#!/usr/bin/env python
#
"""Converts a Jaguar input or output file to a bgf file
   Usage: run bgf2jag.py inputFile and follow instructions interactivly.
   06/22/2007: Yi Liu 
   10/30/2007: Andres Jaramillo-Botero 
	- modified to generate a bgf structure file per optimized geometry in jaguar output file
	- also, allows user to call lingraf in batch mode to automatically generate bgf connectivity
	- 11/9/2007: added support to add charges and connectivity from a template file
	- 11/15/2007: takes all parameters, except coordinates from template bgf
"""
import os,sys,string
import datetime, time

def splitNum(string):
    str = string
    nums = ['0','1','2','3','4','5','6','7','8','9']
    for num in nums:
        chars = str.split(num)
        char = chars[0]
        if not char:
            break
        elif char != str:
            str = char
            continue
    return char

def jag2bgf(filename,template):
    """
        Convert Jaguar input or output (converged optimization) file to bgf file (*.bgf).
    """

    basename = ''
    if filename.find('.') != -1:
        parts = filename.split('.')
        for part in parts[:-1]:
            basename += part + '.' 
        basename = basename[:-1]
    else:
        basename = filename

    jagFile = open(filename, 'r')
    input = False
    output = False
    zmatLine = False
    elems = []
    coords = []
    count = 0
    cont=0 	# geometry counter
    geometry_coords={}
    for line in jagFile.readlines():
        if line.find('&zmat') == 0:
            input = True
            zmatLine = True
            continue
        if line.find('  final geometry') == 0:
            output = True
            continue
        if input:
            if zmatLine and line.find('&') != 0:
                if len(line) < 4:
                    sys.exit('zmat line not complete. Abort')
                else:
                    fields = line.split()
                    elems.append(fields[0])
                    for i in range(1,4):
                        if fields[i].find('#') != -1:
                            # Remove the '#'.
                            fields[i] = fields[i].split('#')[0]
                        else:
                            continue
                    coords.append([float(fields[1]),float(fields[2]),float(fields[3])])
                    continue
            if line.find('&') == 0:
                zmatLine = False
                continue
        elif output:
            if count < 2:
                count += 1
                continue
            elif count >= 2:
                fields = line.split()
                if len(fields) != 4:
                    geometry_coords[cont]=coords
                    count=0
                    output=False
                    coords=[]
                    cont += 1
                    continue            
                else:
                    if cont==0: elems.append(fields[0]) # only need elem list for first structure
                    coords.append([float(fields[1]),float(fields[2]),float(fields[3])])
                    continue
        else:
            continue

    if not elems or not geometry_coords:
        sys.exit('Error in reading Jaguar file. Abort')

    numAtoms = len(elems)
    fftype = []
    atomtype = []
    res=[]
    group=[]
    group1=[]
    group2=[]
    for elem in elems:
        char = splitNum(elem) 
        atomtype.append(char)
        if len(char) == 1:
            # Hybridization of N may be added in future but for now only for C and O.
            if char.lower() == 'c' or char.lower() == 'o':
                char = char + '_2'    
            else: 
                char = char + '_'    
        fftype.append(char)

    newlines_start = []
    newlines_end = []
    charge={}
    
    #chunk = 'XTLGRF 200\n'
    chunk = 'BIOGRF 200\n'
    newlines_start.append(chunk)
    # Need to change DESCRP to short file name instead of tmp
    chunk = 'DESCRP %s\n' % 'tmp' 
    newlines_start.append(chunk)
    chunk = 'REMARK BGF file generated by jag2bgf.py in CMDF on %s\n' % datetime.datetime.now()
    newlines_start.append(chunk)
    chunk = 'REMARK Structure contains %d atoms\n' % (numAtoms)
    newlines_start.append(chunk)

    # Create charges and connectivity string information
    if template=="":    # no charges/connectivity template provided
        # no explicit connectivity
        print ('Note: No charges and connectivity information included in bgfs (use a template file as optional argument !)')
        newlines_end.append('FORMAT CONECT (a6,12i6)\n')
        for i in range(numAtoms):
            chunk = 'CONECT%6d\n' % (i+1)
            newlines_end.append(chunk)
            charge[i]=0.0
	    res.append('RES')
	    group.append(444)
	    group1.append(1)
	    group2.append(0)
    else:
        # Extract charges and connectivity from template bgf (the same for all bgfs)
        print ('Using %s as template to add charges and connectivity information ...'%(template))
        template_bgf=open(template, 'r')
	fftype=[]
	atomtype=[]     
        for line in template_bgf.readlines():
            # get charges
            if line.find('HETATM')==0:
                temp=line.split()
                atomNum=string.atoi(temp[1])
                charge[atomNum-1]=string.atof(temp[12])
		fftype.append(temp[9])
		atomtype.append(temp[2])
		res.append(temp[3])
		group.append(string.atoi(temp[5]))
		group1.append(string.atoi(temp[10]))
		group2.append(string.atoi(temp[11]))
            # get connectivity
            if line.find('CONECT')==0 or line.find('ORDER')==0:
                newlines_end.append(line)
        if len(charge) != numAtoms:
            print "... please verify your template bgf file (e.g. number of atoms, etc. must match)\n"
            sys.exit(1)
            
    # Closing bgf string
    chunk = "END\n"
    newlines_end.append(chunk)        

    # add coordinates data
    chunk = 'FORMAT ATOM   (a6,1x,i5,1x,a5,1x,a3,1x,a1,1x,a5,3f10.5,1x,a5,i3,i2,1x,f8.5)\n'
    newlines_start.append(chunk)

    for geometry in range(len(geometry_coords)):
        newlines = []
        newlines.append(string.join(newlines_start,''))
        for i in range(numAtoms):
            atom_data = ('HETATM', i+1, atomtype[i], res[i], 'A',\
                         group[i], geometry_coords[geometry][i][0], geometry_coords[geometry][i][1], geometry_coords[geometry][i][2],
                         fftype[i], group1[i], group2[i], charge[i])

            #format_string = '%-6s %5d %-5s %3s %1s %-4d %10.5f %10.5f %10.5f %-5s %3d %2d %9.5f\n'
            format_string = '%-6s %5d %-5s %3s %1s %-5d%10.5f%10.5f%10.5f %-5s%3d%2d %8.5f\n'
            chunk = format_string % atom_data
            newlines.append(chunk)

        # Add connection string data
        newlines.append(string.join(newlines_end,''))
        current_dir = os.getcwd()
        bgfname = basename+'.'+str(geometry)+'.bgf'
        full_bgfname = current_dir+'/'+bgfname
        f = open(full_bgfname,'w')
        f.writelines(newlines)
        f.close()
        
        print (' Generated %s !' % (bgfname))

    print "Done ...\n"
    
    return

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 1:
        inputFile = raw_input("Please provide an input file name: ")
        template = raw_input("Please provide a template bgf file name (optional to adds charges/connectivity): ")
    else:
        try:
            inputFile = sys.argv[1]
            if len(sys.argv) == 3:
                template = sys.argv[2]
            else: template=""
        except:
            print """Usage: jag2bgf.py <inputfile> <template (optional)>
                    - <inputfile> can be either Jaguar input or output file
                    - <template> bgf file is used to port charges/connectivity into the bgfs
                    Note:
                    - if template file is not given - no charges are added to output bgfs
                    - connectivity information can be optionally added by selecting the lingraf option"""
            sys.exit(1)
    jag2bgf(inputFile,template)

