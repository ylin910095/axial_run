import sys
def make_inp(gaugefile, jobid):
    trajc = gaugefile.split(".")[-2]
    gcset = gaugefile.split("-")[-2][-1]
    jobid = str(jobid.split('.')[0])
    try:
        str(int(gcset))
        gcset = "a" # default silent set a
    except:
        pass

    return "%s_%s%s.inp"%(jobid, gcset, trajc.zfill(4))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("%s usage: gauge_location jobid"%sys.argv[0])
    gaugefile = sys.argv[1]
    jobid = sys.argv[2]
    print(make_inp(gaugefile, jobid))
    
