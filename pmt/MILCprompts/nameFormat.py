
def NameFormatCube(s,i):
    """Replace any occurrences of "$i" in string tuple s with i"""
    """Also possible to substitute vecStr[i] for i to get corner_wall keys"""
    if isinstance(s,str):
        sr = str(i).join(s.split('$i'))
        pass
    elif isinstance(s,tuple):
        sr = ()
        for x in s:
            sr += (str(i).join(x.split('$i')),)
            pass
    return sr

def NameFormatMass(s,m):
    """Replace any occurrences of "$m" in string tuple s with i"""
    if isinstance(s,str):
        sr = str(MassFormat(m)).join(s.split('$m'))
        pass
    elif isinstance(s,tuple):
        sr = ()
        for x in s:
            sr += (str(MassFormat(m)).join(x.split('$m')),)
            pass
    return sr

def MassFormat(m):
    """Replace a float mass with the string of numerals after the decimal point"""
    try:
        mstr = str(m).split('.')[1]
        return mstr + '0'*max(3-len(mstr),0)
    except IndexError:
        return m

