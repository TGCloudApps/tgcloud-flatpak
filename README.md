# TGCloud Flatpak distribution

Public, signed Flatpak repository for TGPhotos and TGDrive. This repository contains distribution metadata and automation only; it contains no application source code or private signing keys.

Requires **Flatpak 1.16 or newer**, including support for restricted gamepad input permissions.

Installation: https://tgcloudapps.github.io/tgcloud-flatpak/

The workflow imports the complete Flatpak bundles from published app releases and signs the OSTree repository. It runs manually and periodically, deploying only when the release assets change. Draft releases are never imported. TGDownloads will be added when its distribution is ready.

Required secret: `FLATPAK_GPG_PRIVATE_KEY` (base64 private key, stored only in GitHub Actions secrets). The public verification key is committed in `packaging/flatpak`.
