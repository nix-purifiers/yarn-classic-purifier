# SPDX-License-Identifier: MIT
{
  pkgs,
  scope,
  version ? "12.22.12",
}:
let
  nodejs = import ./node-fixture.nix {
    inherit pkgs;
    inherit version;
  };
  managerNode =
    if version == "0.12.18" then
      import ./node-fixture.nix {
        inherit pkgs;
        version = "4.9.1";
      }
    else
      nodejs;
  yarnClassic = (pkgs.yarn.override { nodejs = managerNode; }).overrideAttrs (
    pkgs.lib.optionalAttrs (version == "4.9.1" || version == "0.12.18") {
      version = "1.10.1";
      src = pkgs.fetchurl {
        url = "https://github.com/yarnpkg/yarn/releases/download/v1.10.1/yarn-v1.10.1.tar.gz";
        sha256 = "97bf147cb28229e66e4e3c5733a93c851bbcb0f10fbc72696ed011774f4c6f1b";
      };
    }
  );
  yarn = scope.yarn.override {
    inherit nodejs yarnClassic;
    yarnNode = managerNode;
  };
  command = scope.yarn-classic-purifier.override {
    inherit nodejs yarnClassic yarn;
    yarnNode = managerNode;
  };
in
pkgs.buildEnv {
  name = "yarn-classic-node-${version}-tools";
  paths = [
    nodejs
    yarn
    command
  ];
}
