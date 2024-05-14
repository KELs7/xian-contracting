import h5py

from threading import Lock
from collections import defaultdict
from contracting.storage.encoder import encode, decode

# A dictionary to maintain file-specific locks
file_locks = defaultdict(Lock)

# Constants
ATTR_LEN_MAX = 64000
ATTR_VALUE = "value"
ATTR_BLOCK = "block"


def get_file_lock(file_path):
    """Retrieve a lock for a specific file path."""
    return file_locks[file_path]


def get_value(file_path, group_name):
    return get_attr(file_path, group_name, ATTR_VALUE)


def get_block(file_path, group_name):
    return get_attr(file_path, group_name, ATTR_BLOCK)


def get_attr(file_path, group_name, attr_name):
    with h5py.File(file_path, 'a') as f:
        try:
            value = f[group_name].attrs[attr_name]
            return value.decode() if isinstance(value, bytes) else value
        except KeyError:
            return None


def get_groups(file_path):
    with h5py.File(file_path, 'a') as f:
        return list(f.keys())


def write_attr(file_or_path, group_name, attr_name, value, timeout=20):
    # Attempt to acquire lock with a timeout to prevent deadlock
    if isinstance(file_or_path, str):
        with h5py.File(file_or_path, 'a') as f:
            _write_attr_to_file(f, group_name, attr_name, value, timeout)
    else:
        _write_attr_to_file(file_or_path, group_name, attr_name, value, timeout)


def _write_attr_to_file(file, group_name, attr_name, value, timeout):    
    grp = file.require_group(group_name)
    if attr_name in grp.attrs:
        del grp.attrs[attr_name]
    if value:
        grp.attrs[attr_name] = value
    

def set(file_path, group_name, value, blocknum, timeout=20):
    lock = get_file_lock(file_path if isinstance(file_path, str) else file_path.filename)
    if lock.acquire(timeout=timeout):
        try:
            with h5py.File(file_path, 'a') as f:
                write_attr(f, group_name, ATTR_VALUE, value, timeout)
                write_attr(f, group_name, ATTR_BLOCK, blocknum, timeout)
        finally:
            lock.release()
    else:
        raise TimeoutError("Lock acquisition timed out")


def delete(file_path, group_name, timeout=20):
    lock = get_file_lock(file_path if isinstance(file_path, str) else file_path.filename)
    if lock.acquire(timeout=timeout):
        try:
            with h5py.File(file_path, 'a') as f:
                try:
                    del f[group_name].attrs[ATTR_VALUE]
                    del f[group_name].attrs[ATTR_BLOCK]
                except KeyError:
                    pass
        finally:
            lock.release()
    else:
        raise TimeoutError("Lock acquisition timed out")


def set_value_to_disk(file_path, group_name, value, block_num=None, timeout=20):
    encoded_value = encode(value) if value is not None else None
    set(file_path, group_name, encoded_value, block_num if block_num is not None else -1, timeout)


def delete_key_from_disk(file_path, group_name, timeout=20):
    delete(file_path, group_name, timeout)


def get_value_from_disk(file_path, group_name):
    return decode(get_value(file_path, group_name))
