#!/usr/bin/env python3
"""Import published bundles only; no application source or credentials are distributed."""
import json, os, pathlib, subprocess, sys, urllib.request
URL = 'https://tgcloudapps.github.io/tgcloud-flatpak/flatpak/'
APPS = ['tgphotos', 'tgdrive']

def gh(*args):
    return subprocess.check_output(['gh', *args], text=True)

if sys.argv[1] == 'plan':
    versions = {}
    for app in APPS:
        release = json.loads(gh('api', f'repos/TGCloudApps/{app}/releases/latest'))
        bundles = {asset['name']: asset['id'] for asset in release['assets'] if asset['name'].endswith('.flatpak')}
        expected = {f'{app}-{arch}.flatpak' for arch in ['x86_64', 'aarch64']}
        if set(bundles) != expected:
            raise SystemExit(f'{app}: incomplete release; preserve the existing repository')
        versions[app] = {'tag': release['tag_name'], 'bundles': bundles}
    expected_app, expected_tag = os.environ.get('EXPECTED_APP'), os.environ.get('EXPECTED_TAG')
    if bool(expected_app) != bool(expected_tag):
        raise SystemExit('Both app and tag are required for a release-triggered deployment')
    if expected_app:
        import re
        def version(tag):
            if not re.fullmatch(r'v?\d+\.\d+\.\d+', tag):
                raise ValueError('Expected a stable semantic version')
            return tuple(map(int, tag.removeprefix('v').split('.')))
        if expected_app not in versions or version(versions[expected_app]['tag']) < version(expected_tag):
            raise SystemExit('Expected app release is not yet publicly available')
    pathlib.Path('versions.json').write_text(json.dumps(versions, sort_keys=True, indent=2) + '\n')
    try:
        with urllib.request.urlopen(URL.removesuffix('flatpak/')+'versions.json', timeout=15) as response:
            previous = json.load(response)
    except (urllib.error.URLError, ValueError):
        previous = None
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write('changed=' + str(versions != previous).lower() + '\n')
elif sys.argv[1] == 'build':
    versions = json.loads(pathlib.Path('versions.json').read_text())
    public = pathlib.Path('public'); public.mkdir(exist_ok=True)
    repository = public/'flatpak'
    subprocess.run(['ostree', f'--repo={repository}', 'init', '--mode=archive'], check=True)
    fingerprint = pathlib.Path('packaging/flatpak/repository-key.fingerprint').read_text().strip()
    sign = [f'--gpg-sign={fingerprint}', '--gpg-homedir='+os.environ['GNUPGHOME']]
    apps = []
    for app, version in versions.items():
        if version is None:
            continue
        apps.append(app)
        directory = pathlib.Path('bundles')/app
        directory.mkdir(parents=True, exist_ok=True)
        subprocess.run(['gh', 'release', 'download', version['tag'], '--repo', 'TGCloudApps/'+app, '--pattern', '*.flatpak', '--dir', str(directory)], check=True)
        for bundle in sorted(directory.glob('*.flatpak')):
            subprocess.run(['flatpak', 'build-import-bundle', *sign, str(repository), str(bundle)], check=True)
    subprocess.run(['flatpak', 'build-update-repo', *sign, '--prune', str(repository)], check=True)
    subprocess.run([sys.executable, 'packaging/flatpak/repository-metadata.py', str(public), '--repository-url', URL, '--apps', *apps], check=True)
    (public/'versions.json').write_text(pathlib.Path('versions.json').read_text())
    size = sum(file.stat().st_size for file in public.rglob('*') if file.is_file())
    if size > 900 * 1024**2:
        raise SystemExit('Repository exceeds the deployment size budget; preserve the existing site')
else:
    raise SystemExit('Expected plan or build')
