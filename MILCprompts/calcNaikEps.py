# calculate eps-correction to the Naik term using 8-th order expansion
# eps=-27/40*(am)^2+327/1120*(am)^4-15607/268800*(am)^6-73697/3942400*(am)^8
# Follana et al., PRD75, 054502 (2007)

def calcNaikEps(am):
  return -(27.0/40.0)*(am**2)+\
       (327.0/1120.0)*(am**4)-\
   (15607.0/268800.0)*(am**6)-\
  (73697.0/3942400.0)*(am**8)
