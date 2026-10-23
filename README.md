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

The catalog is available, but a successful real-device install has not yet
been verified.

## Termix NCLS

The Termix NCLS release is listed in the same SideStore catalog at
[ios.ncls.cc](https://ios.ncls.cc/). Its Sessions screen restores persistent
server sessions and shows the Codex and Codex2 quotas. The iOS Codex widget
reads [status.json](https://ios.ncls.cc/status.json) every few minutes, so it
can update while Termix is closed. The file is deliberately public and contains
only status, remaining percentages, session counts, and the check time. It
contains no credentials, email addresses, or session names. If an update fails,
the last file becomes visibly stale in the widget.

The user-level `ios-distribution-status.timer` regenerates this file every three
minutes. The unsigned IPA is built on a macOS GitHub Actions runner and checked
for its WidgetKit extension before release. Installation and widget rendering
on a physical iPhone still require a real-device check.

## Public distribution server

The `devhub` VM serves only static public files at [ios.ncls.cc](https://ios.ncls.cc/)
through the existing Cloudflare Tunnel. The Python HTTP service binds to
`127.0.0.1:18090`; the tunnel is the only public entry point. Its user-level
systemd unit and release-sync timer are in `systemd/`. The timer checks public
GitHub releases every 15 minutes and mirrors an IPA only after its SHA-256,
size, bundle identifier, version, and iPhone platform pass validation. It
updates `source.json` after the IPA has been published atomically. Old release
files are retained for rollback.

The source can be added directly in SideStore from [ios.ncls.cc](https://ios.ncls.cc/)
after SideStore is installed. The first real-device install remains unverified.
All files under `public/releases/`, plus the generated catalog files, are
runtime outputs and are intentionally ignored by Git. The server uses no
Cloudflare or GitHub token to serve or mirror public files.
