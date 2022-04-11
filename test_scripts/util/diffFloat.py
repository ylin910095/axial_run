"""
By Jim Simone originally. Compare two different correlators files to 
see the lines that are more different by the set amount of tolerance.
"""
import sys, re, math, bz2

intRe = re.compile ( '^\d+$' )
floatRe = re.compile ( '^[-+]?(\d+(\.\d*)?|\d*\.\d+)([eE][-+]?\d+)?$' )

tolerance = 5e-6

def compare ( a, b ) :
    if intRe.search ( a ) == None or intRe.search ( b ) == None :
        # not integers, so try float
        if floatRe.search ( a ) and floatRe.search ( b ) :
            af = float ( a )
            bf = float ( b )
            if af == 0.0 or bf == 0.0 :
                rel = math.fabs ( af - bf )
            else :
                rel = math.fabs ( 0.5 * ( af - bf ) / ( af + bf ) )
            if rel > tolerance :
                n = 16 #max ( len(a), len(b) )
                fmt = 'float mismatch line %%5d field %%3d %%%ds %%%ds error %%.1e' % ( n, n )
                print  fmt % ( lineNo, fieldCnt, a, b, rel )
            return
    # compare as strings everything else
    if a != b :
        print 'string mismatch line', lineNo, 'field', fieldCnt, a, b
        return
    

file = []
for n in range ( 1, 3 ) :
    name = sys.argv [n]
    isBz = re.search ( '\.bz2$', name )
    #print 'open', sys.argv [n]
    if isBz :
        f = bz2.BZ2File ( name, "r" )
    else :
        f = open ( name, 'r' )
    file.append ( f )

lineNo = 0 # 1-base
for line in zip ( file [0], file [1] ) :
    lineNo += 1
    field0 = line [0].split ()
    field1 = line [1].split ()
    fieldCnt = 0 # 0-base
    for f in zip ( field0, field1 ) :
        compare ( f[0], f[1] )
        fieldCnt += 1

