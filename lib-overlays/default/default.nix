# SPDX-License-Identifier: MIT
#
# The `yarn-classic-purifier` library namespace: `readLock`
# (lib-overlays/default/read-lock.nix), which reads a project's lockfiles into the lock
# in memory of the purifier contract. It needs no package set. The builder
# `buildYarnClassicProject` is a package in the default package overlay.
{ ... }:
{

  overlay = final: prev: {
    yarn-classic-purifier = {
      readLock = import ./read-lock.nix { lib = final; };
    };
  };

}
