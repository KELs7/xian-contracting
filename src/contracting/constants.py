from pathlib import Path

RECURSION_LIMIT = 1024

DELIMITER = ':'
INDEX_SEPARATOR = '.'
HDF5_GROUP_SEPARATOR = '/'
DEFAULT = '__default__'
SUBMISSION_CONTRACT_NAME = 'submission'
PRIVATE_METHOD_PREFIX = '__'
EXPORT_DECORATOR_STRING = 'export'
INIT_DECORATOR_STRING = 'construct'
INIT_FUNC_NAME = '__{}'.format(PRIVATE_METHOD_PREFIX)
VALID_DECORATORS = {EXPORT_DECORATOR_STRING, INIT_DECORATOR_STRING}

ORM_CLASS_NAMES = {'Variable', 'Hash', 'ForeignVariable', 'ForeignHash'}

MAX_HASH_DIMENSIONS = 16
MAX_KEY_SIZE = 1024

READ_COST_PER_BYTE = 1
WRITE_COST_PER_BYTE = 25

STAMPS_PER_TAU = 20

BLOCK_NUM_DEFAULT = -1
FILENAME_LEN_MAX = 255

DEFAULT_STAMPS = 1000000

STORAGE_HOME = Path().home().joinpath(".cometbft/xian")
