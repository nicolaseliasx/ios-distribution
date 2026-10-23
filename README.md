# Personal iOS distribution

Public source and build workflow for personal iOS apps. The first milestone is
`ProxmoxAppTest`, a small SwiftUI app used to verify an unsigned IPA can be
installed and refreshed by SideStore on the owner's iPhone.

The GitHub Actions workflow builds for a physical iPhone, packages
`Payload/ProxmoxAppTest.app` into an unsigned IPA, validates its bundle metadata,
and uploads the IPA and SHA-256 metadata as artifacts. No Apple credentials or
signing certificates belong in this repository or the workflow.

This repository does not yet publish a SideStore source or claim a successful
device install. Those steps follow after the owner validates the proof of
concept on their iPhone.
