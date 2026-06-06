"""Tests for fallback_urls: mirror handling centralised in dlmachine.

A failing primary falls through to a working fallback; the cache item is keyed
on the PRIMARY url (so re-lookup hits regardless of which mirror served the
bytes); the cache-hit path does not crash (regression test for the
created-but-unrun downloader accessing `_destination`).
"""

import os

import dlmachine as dm
from dlmachine import _constants


def test_fallback_used_and_keyed_on_primary(download_dir):
    manager = dm.DownloadManager(path=download_dir, backend='requests')
    bad = 'http://eu.httpbin.org/status/404'
    good = 'http://eu.httpbin.org/bytes/256'

    dest = manager.download(bad, fallback_urls=[good], force_download=True)
    assert isinstance(dest, str) and os.path.exists(dest)
    assert os.path.getsize(dest) == 256  # served by the fallback

    # Identity is the primary (bad) URL, not the mirror that served it.
    it = manager.cache.best_or_new(bad, params={_constants.DL_PARAMS_KEY: {}})
    assert it.uri == bad

    # Re-lookup with the same primary: cache hit, no re-download, NO crash
    # (the created-but-unrun-downloader `_destination` regression).
    dest2 = manager.download(bad, fallback_urls=[good])
    assert dest2 == dest


def test_no_fallback_backward_compatible(download_dir):
    manager = dm.DownloadManager(path=download_dir, backend='requests')
    dest = manager.download(
        'http://eu.httpbin.org/bytes/128', force_download=True,
    )
    assert isinstance(dest, str) and os.path.getsize(dest) == 128
    # cache hit on re-lookup, no crash
    assert manager.download('http://eu.httpbin.org/bytes/128') == dest
