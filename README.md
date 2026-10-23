# Personal iOS distribution

Public source and build workflow for personal iOS apps. The first milestone is
`ProxmoxAppTest`, a small SwiftUI app used to verify an unsigned IPA can be
installed and refreshed by SideStore on the owner's iPhone.

The GitHub Actions workflow builds for a physical iPhone, packages
`Payload/ProxmoxAppTest.app` into an unsigned IPA, validates its bundle metadata,
and uploads the IPA and SHA-256 metadata as artifacts. No Apple credentials or
signing certificates belong in this repository or the workflow.

## First iPhone test

The public [0.1.0 release](https://github.com/nicolaseliasx/ios-distribution/releases/tag/poc-v0.1.0)
contains the unsigned IPA. On the iPhone, install and configure SideStore using
its [official instructions](https://docs.sidestore.io/docs/installation/prerequisites)
and [installation guide](https://docs.sidestore.io/docs/installation/install).
SideStore needs Wi-Fi and LocalDevVPN enabled while installing, updating, or
refreshing an app. Its documentation recommends a current nightly build for
iOS 26.4 and newer when the stable build encounters installation errors.

Open this link on the iPhone after SideStore is working:

[Install ProxmoxAppTest in SideStore](sidestore://install?url=https%3A%2F%2Fgithub.com%2Fnicolaseliasx%2Fios-distribution%2Freleases%2Fdownload%2Fpoc-v0.1.0%2FProxmoxAppTest-0.1.0-1.ipa)

If the link is not clickable in a GitHub viewer, download the
[IPA directly](https://github.com/nicolaseliasx/ios-distribution/releases/download/poc-v0.1.0/ProxmoxAppTest-0.1.0-1.ipa)
and choose it from SideStore, or paste the `sidestore://install?...` link into
Safari.

Confirm that the app installs, opens, shows version `0.1.0` and build `1`, and
that **Verificar conexão** reaches `termix.ncls.cc`. Report the exact SideStore
error if installation fails. Refreshing the free Apple Account signature is a
separate action from installing a new app version.

This repository does not yet publish a SideStore source or claim a successful
device install. Hosting and automated updates follow the real-device test.
