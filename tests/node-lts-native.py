"""Exercise each selected Node point through native and ordinary registry workflows."""
import json
import pathlib
import subprocess
import sys

system = subprocess.check_output(
    ['nix', 'eval', '--impure', '--raw', '--expr', 'builtins.currentSystem'], text=True
).strip()
points = [('legacy-node', '12.22.12'), ('legacy-node-4', '4.9.1')]
if system == 'x86_64-linux':
    points.append(('legacy-node-0', '0.12.18'))
points += [('node-lts-' + major, version) for major, version in [
    ('6', '6.17.1'), ('8', '8.17.0'), ('10', '10.24.1'),
    ('14', '14.21.3'), ('16', '16.20.2'), ('18', '18.20.8'),
    ('20', '20.19.0'), ('22', '22.14.0'), ('26', '26.0.0'),
]]
for name, version in points:
    print('Native registry workflow: Node ' + version, flush=True)
    def build(attribute):
        return pathlib.Path(subprocess.check_output(
            ['nix', 'build', '--no-link', '--print-out-paths',
             '.#checks.' + system + '.' + attribute], text=True
        ).strip())
    tools = build(name + '-tools')
    release = build(name + '.release')
    outputs = json.loads(subprocess.check_output(
        ['nix', 'build', '--no-link', '--json',
         '.#checks.' + system + '.' + name + '.repository^*'], text=True
    ))[0]['outputs']
    yarn = '1.10.1' if version in ['0.12.18', '4.9.1'] else '1.22.22'
    manager = '4.9.1' if version == '0.12.18' else version
    subprocess.run([
        sys.executable, 'tests/legacy-native.py', str(tools),
        str(release / 'legacy-app.tgz'), version, outputs['out'],
        str(pathlib.Path(outputs['metadata']) / 'catalog.json'), yarn, manager,
    ], check=True)
