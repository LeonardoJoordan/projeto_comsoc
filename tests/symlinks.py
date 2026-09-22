"""Skip only demonstrated platform limitations, not arbitrary I/O failures."""
import errno

import pytest


def create_symlink(link, target, *, target_is_directory=False):
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except NotImplementedError:
        pytest.skip('Symbolic links are not implemented on this platform')
    except OSError as exc:
        if getattr(exc, 'winerror', None) == 1314:
            pytest.skip('Windows account lacks the symbolic-link privilege (1314)')
        if exc.errno in {errno.ENOSYS, errno.ENOTSUP}:
            pytest.skip(f'Symbolic links are unsupported: errno {exc.errno}')
        raise
