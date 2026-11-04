#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run after building checks.<system>.legacy-node-tools; takes its store path."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from registry_fixture import registry

tools = Path(sys.argv[1]).resolve()
expected_archive = Path(sys.argv[2]).resolve()
version = sys.argv[3] if len(sys.argv) > 3 else '12.22.12'
prepared = Path(sys.argv[4]) if len(sys.argv) > 4 else None
catalog = Path(sys.argv[5]) if len(sys.argv) > 5 else None
yarn_version = sys.argv[6] if len(sys.argv) > 6 else '1.22.22'
manager_node = sys.argv[7] if len(sys.argv) > 7 else version
env = dict(os.environ, PATH=str(tools / 'bin') + os.pathsep + os.environ['PATH'],
           npm_config_registry='http://127.0.0.1:9', YARN_DISABLE_SELF_UPDATE_CHECK='true')


def run(*args, cwd):
    return subprocess.run(args, cwd=cwd, env=env, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


with tempfile.TemporaryDirectory(prefix='yarn-legacy-native-') as temporary:
    root = Path(temporary) / 'project'
    shutil.copytree(Path(__file__).parent / 'fixtures' / 'legacy-node', root)
    env['HOME'] = str(Path(temporary) / 'home')
    Path(env['HOME']).mkdir()
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert run('node', '--version', cwd=root) == 'v' + version
    assert run('yarn', '--version', cwd=root) == yarn_version
    run('yarn-classic-purifier', 'lock', cwd=root)
    run('yarn-classic-purifier', 'prefetch', cwd=root)
    run('yarn', 'install', '--frozen-lockfile', cwd=root)
    run('yarn', 'workspace', 'legacy-app', 'run', 'build', cwd=root)
    run('yarn', 'workspace', 'legacy-app', 'run', 'test', cwd=root)
    assert (root / 'packages/app/built.txt').read_text() == 'v' + version
    assert run('node', 'packages/app/cli.js', cwd=root) == '42 on v' + version
    assert (root / 'installed.txt').read_text() == 'v' + version
    for path, contents in before.items():
        assert (root / path).read_bytes() == contents, f'native workflow changed {path}'
    with registry(root, version, prepared, catalog) as (url, uploads):
        env['npm_config_registry'] = url
        run('yarn-classic-purifier', 'publish', 'legacy-app', '--new-version', '1.0.0', '--registry', url, cwd=root)
        assert uploads and 'node/v' + manager_node in uploads[0][1], uploads
        if prepared:
            import json
            modules = json.loads(catalog.read_text())['modules']
            app = next(entry for entry in modules if entry['name'] == 'legacy-app')
            ordinary = Path(temporary) / 'ordinary'
            ordinary.mkdir()
            (ordinary / 'package.json').write_text(json.dumps({
                'name': 'ordinary-consumer', 'private': True,
                'dependencies': {'legacy-app': app['version']}}))
            ordinary_env = dict(env, YARN_CLASSIC_PURIFIER='0', YARN_CACHE_FOLDER=str(Path(temporary) / 'ordinary-cache'))
            subprocess.run(['yarn', 'install', '--registry', url, '--non-interactive'],
                           cwd=ordinary, env=ordinary_env, check=True, stdout=subprocess.PIPE, text=True)
            result = subprocess.check_output(['node', 'node_modules/legacy-app/cli.js'],
                                             cwd=ordinary, env=ordinary_env, text=True).strip()
            assert result == '42 on v' + version, result
            assert not (ordinary / '.yarn-classic-purifier').exists()
            print('PASS ordinary registry-index resolution/install/execution of prepared graph', flush=True)
    assert uploads[0][0] == expected_archive.read_bytes(), 'native upload differs from the pure release'
    for path, contents in before.items():
        assert (root / path).read_bytes() == contents, f'publication changed {path}'
    print('PASS Node' + version + '/Yarn1 native lock, prefetch, offline install, workspace build/test and actual publication; source unchanged')
