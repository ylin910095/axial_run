import yaml, sys, re, glob
from string import Template
if len(sys.argv) != 4:
    print('usage:', sys.argv[0], 'run_param.yaml', 'slurm_template.sh', 'slurm_out.sh')
    sys.exit(1)

with open(sys.argv[1], 'r') as f:
    rparam = yaml.load(f)

# Reconstruct slurm header, I got some problems with yaml
rparam['slurm_header'] = "\n".join(rparam['slurm_header'])
rparam['module_command'] = "\n".join(rparam['module_command'])

with open(sys.argv[2], 'r') as slurm_template:
    s = Template(slurm_template.read())
    ns = s.safe_substitute(**rparam)
with open(sys.argv[3], 'w') as slurmout:
    slurmout.write(ns)

