# Workers for modular and expandable PyPI server

This program starts the server with all plugins configured.

At startup, and even to show this help, the program scans all available
plugins, and logs their arguments.

## Plugins activation

Each plugin should contain an activation flag, while reacting to it
depending on the implementation.

Plugins can be **enabled together**, then their behavior will be described
by the following rules:

* Firstly, requests to plugins will be made at the same time.
* In the event that a request requires a response from only one plugin, in
  this case the order of the call and the expected behavior
  are **not guaranteed**.
* _For example_, if several plugins that provide _storage of binary blobs_ are
  enabled, then the request to save the blob will be redirected to all
  plugins at the same time, while the request to receive the blob will be
  sent to only one of the plugins.

## Configuration file format

Default values was based on following configuration files
(**"pypi-server.ini"**, **"~/.config/pypi-server.ini"**,
**"/etc/pypi-server.ini"**).

The configuration files is INI-formatted files where configuration groups
is INI sections.

### Configuration file example:

```ini
[DEFAULT]
pool_size = 8

[log]
level = info
```

