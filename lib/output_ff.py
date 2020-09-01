""" Output force field file, current suport ffield.
"""
import sys
import time, datetime

def toFfieldLammps(ff, outfile='out.ffield'):
    o = open(outfile, 'w')
    for i in ff.pair:
        o.write('%s %d %d %.4f %.4f # %s\n'%(i[0], int(i[1]), int(i[2]),
                float(i[3]), float(i[4]), i[5])) 
    for i in ff.bond:
        o.write('%s %d %.4f %.4f # %s\n'%(i[0], int(i[1]),
                float(i[2]), float(i[3]), i[4])) 
    for i in ff.angle:
        o.write('%s %d %.4f %.4f # %s\n'%(i[0], int(i[1]),
                float(i[2]), float(i[3]), i[4])) 
    o.close()

def toFfield(ff, outfile="out.ffield"):
    o = open(outfile, 'w')
    ts = time.time()
    o.write(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
    o.write(" : %s\n"%("|".join(ff.elements)))
    # Write gobal parameters
    o.write(" %d\n"%len(ff.gl))
    for i in ff.gl:
        o.write("%10.4f\n"%i)

    # Write atom parameters
    o.write(""" %d    ! Nr of atoms; cov.r; valency;a.m;Rvdw;Evdw;gammaEEM;cov.r2;#
            alfa;gammavdW;valency;Eunder;Eover;chiEEM;etaEEM;n.u.
            cov r3;Elp;Heat inc.;n.u.;n.u.;n.u.;n.u.
            ov/un;val1;n.u.;val3,vval4\n"""%len(ff.atom))
    for i in ff.atom:
        counter = 0
        for j in i:
            if counter == 0:
                o.write(" %-2s"%j)
            elif counter > 0 and counter % 8 == 0:
                o.write("%9.4f"%float(j))
                o.write('\n')
            elif counter > 1 and counter % 8 == 1:
                o.write("   ")
                o.write("%9.4f"%float(j))
            else:
                o.write("%9.4f"%float(j))
            counter += 1
        #o.write("\n")

    # Write bond parameters
    o.write(""" %d      ! Nr of bonds; Edis1;LPpen;n.u.;pbe1;pbo5;13corr;pbo6
                         pbe2;pbo3;pbo4;n.u.;pbo1;pbo2;ovcorr\n"""%len(ff.bond))
    for i in ff.bond:
        counter = 0
        for j in i:
            if counter >=0 and counter < 2:
                o.write("%3d"%int(j))
            elif counter >=2 and counter < 9:
                o.write("%9.4f"%float(j))
            elif counter == 9:
                o.write("%9.4f\n"%float(j))
            elif counter == 10:
                o.write("      %9.4f"%float(j))
            elif counter > 10 and counter < 17:
                o.write("%9.4f"%float(j))
            else:
                o.write("%9.4f\n"%float(j))
            counter += 1
    # Write off parameters
    o.write(" %d    ! Nr of off-diagonal terms; Ediss;Ro;gamma;rsigma;rpi;rpi2\n"%len(ff.off))
    for i in ff.off:
       counter = 0
       for j in i:
           if counter >=0 and counter < 2:
               o.write("%3d"%int(j))
           else:
               o.write("%9.4f"%float(j))
           counter += 1
       o.write("\n")
    # Write angle parameters
    o.write(" %d    ! Nr of angles;at1;at2;at3;Thetao,o;ka;kb;pv1;pv2\n"%len(ff.angle))
    for i in ff.angle:
        counter = 0
        for j in i:
            if counter >= 0 and counter < 3:
                o.write("%3d"%int(j))
            else:
                o.write("%9.4f"%float(j))
            counter += 1
        o.write("\n")
    # Write torsion parameters
    o.write(" %d    ! Nr of torsions;at1;at2;at3;at4;;V1;V2;V3;V2(BO);vconj;n.u;n\n"%len(ff.torsion))
    for i in ff.torsion:
        counter = 0
        for j in i:
            if counter >= 0 and counter < 4:
                o.write("%3d"%int(j))
            else:
                o.write("%9.4f"%float(j))
            counter += 1
        o.write("\n")
    # Write torsion parameters
    o.write("  %d    ! Nr of hydrogen bonds;at1;at2;at3;Rhb;Dehb;vhb1\n"%len(ff.hbond))
    for i in ff.hbond:
        counter = 0
        for j in i:
            if counter >= 0 and counter < 3:
                o.write("%3d"%int(j))
            else:
                o.write("%9.4f"%float(j))
            counter += 1
        o.write("\n")
    o.close()

if __name__ == "__main__":
   pass 
