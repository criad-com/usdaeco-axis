{
  description = "usdAecoAxis semantic library";
  inputs = {
    toolchain.url = "github:criad-com/usdaeco-toolchain?ref=v0.3.10";
    datacentre.url = "github:criad-com/usdaeco-datacentre?ref=v0.4.8";
    datacentre.flake = false;
    nixpkgs.follows = "toolchain/nixpkgs";
    core.url = "github:criad-com/usdaeco-core?ref=v0.9.4";
    core.flake = false;
  };
  outputs = { self, nixpkgs, toolchain, core, ... }:
    let
      eachSystem = nixpkgs.lib.genAttrs [ "aarch64-darwin" "x86_64-linux" ];
      forSystem = system:
        let
          kit = toolchain.lib.forSystem system;
          pkgs = nixpkgs.legacyPackages.${system};
          corePlugin = (kit.buildCodelessSchema { name = "usdAeco"; src = core; }).overrideAttrs (old: {
            postInstall = (old.postInstall or "") + ''
              cp -RL tools/usdaeco_core tools/usdaeco_tools "$out/python/"
            '';
          });
          schema = (kit.buildCodelessSchema { name = "usdAecoAxis"; src = self; deps = [ corePlugin ]; }).overrideAttrs (old: {
            postInstall = (old.postInstall or "") + ''
              cp -RL tools/usdaeco_axis "$out/python/"
            '';
          });
          plugins = kit.pluginSet { plugins = [ schema ]; };
          setup = ''
            export TOOLCHAIN_DIR=${toolchain}
            export CORE_DIR=${core}
            export CORE_PLUGIN_DIR=${corePlugin}/plugins/usdAeco/resources
          '';
          example = pkgs.writeShellApplication {
            name = "example";
            runtimeInputs = [ kit.pythonEnv kit.usd-dev ];
            text = setup + ''
              cp -R ${self} example-work
              chmod -R u+w example-work
              cd example-work
              env -u PYTHONPATH PYTHONPATH="${core}:$PWD" python examples/minimal/run.py "$@"
            '';
          };
          render = pkgs.writeShellApplication {
            name = "render";
            runtimeInputs = [ kit.pythonEnv kit.usd-dev ];
            text = setup + ''
              cp -R ${self} render-work
              chmod -R u+w render-work
              cd render-work
              env -u PYTHONPATH PYTHONPATH="${core}:$PWD" python examples/minimal/run.py "$@"
            '';
          };
        in { inherit kit pkgs schema plugins setup example render; };
    in {
      packages = eachSystem (system: let p = forSystem system; in {
        default = p.schema;
        pluginSet = p.plugins;
      });
      checks = eachSystem (system: let p = forSystem system; in {
        library = p.pkgs.runCommand "usdAecoAxis-check" { nativeBuildInputs = [ p.kit.pythonEnv p.kit.usd-dev ]; }
          (p.setup + ''
            cp -R ${self} source
            chmod -R u+w source
            cd source
            env -u PYTHONPATH PYTHONPATH="${core}:$PWD" python check.py
            env -u PYTHONPATH python -m pytest -q
            mkdir -p "$out"
          '');
        structure = p.pkgs.runCommand "usdAecoAxis-structure" { nativeBuildInputs = [ p.kit.pythonEnv ]; }
          (p.setup + ''
            cp -R ${self} source
            chmod -R u+w source
            cd source
            env -u PYTHONPATH python -c 'import sys; sys.path[:0] = ["tools", "${toolchain}/tools"]; from usdaeco_axis.structure import check_structure; from usdaeco_check.structure import print_results; raise SystemExit(print_results(check_structure(".")))'
            mkdir -p "$out"
          '');
      });
      devShells = eachSystem (system: let p = forSystem system; in {
        default = p.pkgs.mkShell {
          packages = [ p.kit.pythonEnv p.kit.usd-dev ];
          shellHook = p.setup + "unset PYTHONPATH";
        };
      });
      apps = eachSystem (system: let p = forSystem system; in {
        example = { type = "app"; program = "${p.example}/bin/example"; };
        render = { type = "app"; program = "${p.render}/bin/render"; };
      });
    };
}
