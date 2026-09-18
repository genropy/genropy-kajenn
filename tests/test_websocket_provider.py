# Copyright 2025 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""Exercise provider selection in fresh interpreters with real legacy imports.

genropy resolves the ``gnr.web:websockethandler`` entry point in
``websocketHandlerClass()``, called while a site is built — importing the module
has no side effect. An installed genropy without that function predates the
selector, and every test that needs it skips.
"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

SELECTOR = ('from gnr.web.gnrwsgisite_proxy.gnrwebsockethandler '
            'import WsgiWebSocketHandler, websocketHandlerClass\n')


class WebSocketProviderTest(unittest.TestCase):
    def run_import(self, provider, code):
        root = Path(__file__).resolve().parents[1]
        project = tomllib.loads((root / 'pyproject.toml').read_text())
        entry = project['project']['entry-points']['gnr.web']['websockethandler']
        with tempfile.TemporaryDirectory() as temporary:
            metadata = Path(temporary) / 'genropy_kajenn-0.0.0.dist-info'
            metadata.mkdir()
            (metadata / 'METADATA').write_text(
                'Metadata-Version: 2.1\nName: genropy-kajenn\nVersion: 0.0.0\n')
            (metadata / 'entry_points.txt').write_text(
                f'[gnr.web]\nwebsockethandler = {entry}\n')
            env = os.environ.copy()
            env.pop('GNR_DAEMON_PROVIDER', None)
            if provider:
                env['GNR_DAEMON_PROVIDER'] = provider
            env['PYTHONPATH'] = os.pathsep.join(
                [temporary, str(root / 'src'), env.get('PYTHONPATH', '')])
            return subprocess.run(
                [sys.executable, '-c', code], env=env,
                capture_output=True, text=True, timeout=20)

    def require_selector(self):
        """Skip where the installed genropy has no websocket selector."""
        probe = self.run_import(None, SELECTOR)
        if probe.returncode != 0:
            self.skipTest('the installed genropy has no websocketHandlerClass')

    def test_the_selected_handler_is_this_package_and_opens_no_socket(self):
        self.require_selector()
        result = self.run_import('genropy-kajenn', SELECTOR + '''
from unittest.mock import patch
with patch('socket.socket', side_effect=AssertionError('unexpected socket')):
    from genropy_kajenn.websockethandler import WsgiWebSocketHandler as Expected
    handler_class = websocketHandlerClass()
    assert handler_class is Expected
    handler = handler_class(object())
    assert handler.checkSocket() is True
    assert handler.sendCommandToPage('', 'registerNewPage', {}) is None
    assert handler.sendCommandToPage('page', 'publish', {}) is None
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_named_client_is_a_module_genropy_ships(self):
        """``client_module`` must name a file, or the page would load nothing."""
        self.require_selector()
        result = self.run_import('genropy-kajenn', SELECTOR + '''
from pathlib import Path
import gnr
client = websocketHandlerClass().client_module
root = Path(gnr.__file__).resolve().parents[2]
found = list(root.glob(f'gnrjs/*/js/{client}.js'))
assert found, f'{client}.js is in no gnrjs frontend under {root}'
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_classic_import_is_unchanged(self):
        result = self.run_import(None, '''
from gnr.web.gnrwsgisite_proxy.gnrwebsockethandler import WsgiWebSocketHandler
assert WsgiWebSocketHandler.__module__ == 'gnr.web.gnrwsgisite_proxy.gnrwebsockethandler'
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_provider_this_package_does_not_declare_keeps_the_classic_handler(self):
        """The register may be replaced without the socket: no error, no swap."""
        self.require_selector()
        result = self.run_import('another-provider', SELECTOR + '''
assert websocketHandlerClass() is WsgiWebSocketHandler
''')
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
