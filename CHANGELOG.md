# Changelog

All notable changes to genropy-kajenn are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/). Releases before 0.6.0 are listed
on [GitHub Releases](https://github.com/genropy/genropy-kajenn/releases).

## [0.7.0] - 2026-11-13

### Added

- The container image `ghcr.io/genropy/genropy-kajenn`: genropy-kajenn on top
  of the kajenn-orchestra image, started with `kajenn serve` on
  `/app/config.py`. It holds no genropy and no application, and carries no
  `/app/config.py`: an installation brings its recipe. Published at every
  release as `X.Y.Z` and `latest`. `/image-packages.txt` lists its Python
  packages with their versions (#23).

### Changed

- Requires kajenn-orchestra 0.6.1 (#17).

### Fixed

- On macOS a pool started without `PGGSSENCMODE=disable` could not start a
  worker. The pool now sets it when the variable is not set (#21).

## [0.6.0] - 2026-11-10

### Breaking

- Requires kajenn 0.9.0 and kajenn-orchestra 0.6.0.
- The package `genropy_kajenn.proxy` is renamed `genropy_kajenn.gnrapp_wrapper`,
  with no alias. `GenropyProxyMixin` becomes `GnrAppWrapperMixin` and
  `GenropyProxyOpenApiApplication` becomes `GnrAppWrapperApplication`.
- `GnrAppWrapperApplication` is a kajenn `RoutedApplication` and takes no
  `routing_class` or `module`. Subclass it and attach the routing class in the
  constructor: `self.route.add_branches({"name": "api", "instance": MyApi(self)})`.
  The URLs under `api` do not change; MCP answers on `<mount>/_meta/mcp`.
- The HTTP channel is `api`: a channel configured as `rest` for the
  `authenticate` route is written `api`.
- A `GenropySpaApplication` whose group names no `source` no longer stops the
  server. The check runs in `build_pool`, and the front gives up as every
  `SpaApplication` does: only `_server` answers and `/readyz` is not ready.

### Changed

- `genropy_kajenn.gnrapp_wrapper.__version__` reads the version of the
  installed distribution, as the other modules do.
