import os 
def parse_gauge(gauge_loc):
    # Only support gauge-fixed ensembles for now
    if '-Coul.' not in gauge_loc or not gauge_loc.endswith('.ildg'):
        raise Exception('Expect coulomb gauge-fixed configurations!')
    else:
        config_name = os.path.basename(gauge_loc)
        ss = config_name.split('-')
        series = ss[-2][-1]
        try:
            str(int(series)) # make sure it is not a number
            series = 'a' # default to series a
            ensemble = ss[-2]
        except:
            ensemble = ss[-2][:-1]
        trajectory = int(config_name.split('.')[-2])
    return {'ensemble': ensemble, 'config_name': config_name,
            'series': series, 'trajectory': trajectory}