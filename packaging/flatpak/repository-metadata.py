#!/usr/bin/env python3
"""Write public Flatpak installation metadata; never reads private keys."""
import argparse,base64,pathlib
from urllib.parse import urlsplit
root=pathlib.Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('output',type=pathlib.Path)
parser.add_argument('--repository-url',required=True)
parser.add_argument('--apps', nargs='*', choices=['tgphotos','tgdrive','tgdownloads'], default=['tgphotos','tgdrive','tgdownloads'])
args=parser.parse_args()
parts=urlsplit(args.repository_url)
if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
 parser.error('Use a public HTTPS repository URL without credentials or tokens')
out=args.output;out.mkdir(parents=True,exist_ok=True)
key=base64.b64encode((root/'packaging/flatpak/repository-key.gpg').read_bytes()).decode()
url=args.repository_url.rstrip('/')+'/'
(out/'tgcloud.flatpakrepo').write_text(f'[Flatpak Repo]\nTitle=TGCloud\nUrl={url}\nHomepage=https://github.com/TGCloudApps\nDescription=TGCloud applications\nGPGKey={key}\n')
for app in args.apps:
 (out/f'{app}.flatpakref').write_text(f'[Flatpak Ref]\nTitle={app}\nName=com.tgcloud.{app}\nBranch=stable\nUrl={url}\nIsRuntime=false\nRuntimeRepo=https://dl.flathub.org/repo/flathub.flatpakrepo\nGPGKey={key}\n')
(out/'.nojekyll').touch()
(out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>TGCloud Flatpak</title><h1>TGCloud</h1>'+''.join(f'<p><a href="{app}.flatpakref">{app}</a></p>' for app in args.apps))
