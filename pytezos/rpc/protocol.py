import os
import tarfile
import requests
import io
import netstruct
import simplejson as json
import patch as pypatch
from tempfile import TemporaryDirectory
from functools import lru_cache
from binascii import hexlify
from collections import OrderedDict
from typing import List, Tuple
from difflib import unified_diff
from tqdm import tqdm
from loguru import logger

from pytezos.rpc.node import RpcQuery
from pytezos.crypto import blake2b_32
from pytezos.encoding import base58_encode

pypatch.warning = logger.warning


def dir_to_files(path) -> List[Tuple[str, str]]:
    files = list()

    with open(os.path.join(path, 'TEZOS_PROTOCOL')) as f:
        index = json.load(f)

    for module in index['modules']:
        for ext in ['mli', 'ml']:
            name = f'{module.lower()}.{ext}'

            filename = os.path.join(path, name)
            if not os.path.exists(filename):
                continue

            with open(filename, 'r') as file:
                text = file.read()
                files.append((name, text))

    return files


def tar_to_files(path=None, raw=None) -> List[Tuple[str, str]]:
    assert path or raw

    fileobj = io.BytesIO(raw) if raw else None
    with tarfile.open(name=path, fileobj=fileobj) as tar:
        with TemporaryDirectory() as tmp_dir:
            tar.extractall(tmp_dir)
            files = dir_to_files(tmp_dir)

    return files


def url_to_files(url) -> List[Tuple[str, str]]:
    res = requests.get(url, stream=True)
    raw = b''

    for data in tqdm(res.iter_content()):
        raw += data

    return tar_to_files(raw=raw)


def files_to_proto(files: List[Tuple[str, str]]) -> dict:
    components = OrderedDict()

    for filename, text in files:
        name, ext = filename.split('.')
        key = {'mli': 'interface', 'ml': 'implementation'}[ext]
        name = name.capitalize()
        data = hexlify(text.encode()).decode()

        if name in components:
            components[name][key] = data
        else:
            components[name] = {'name': name, key: data}

    proto = {
        'expected_env_version': 0,  # TODO: this is V1
        'components': list(components.values())
    }
    return proto


def files_to_tar(files: List[Tuple[str, str]], output_path=None):
    fileobj = io.BytesIO() if output_path is None else None
    nameparts = os.path.basename(output_path).split('.')
    mode = 'w'
    if len(nameparts) == 3:
        mode = f'w:{nameparts[-1]}'

    with tarfile.open(name=output_path, fileobj=fileobj, mode=mode) as tar:
        for filename, text in files:
            file = io.BytesIO(text.encode())
            ti = tarfile.TarInfo(filename)
            ti.size = len(file.getvalue())
            tar.addfile(ti, file)

    if fileobj:
        return fileobj.getvalue()


def proto_to_files(proto: dict) -> List[Tuple[str, str]]:
    files = list()
    extensions = {'interface': 'mli', 'implementation': 'ml'}

    for component in proto.get('components', []):
        for key, ext in extensions.items():
            if key in component:
                filename = f'{component["name"].lower()}.{ext}'
                text = bytes.fromhex(component[key]).decode()
                files.append((filename, text))

    return files


def proto_to_bytes(proto: dict) -> bytes:
    res = b''

    for component in proto.get('components', []):
        res += netstruct.pack(b'I$', component['name'].encode())

        if component.get('interface'):
            res += b'\xff' + netstruct.pack(b'I$', bytes.fromhex(component['interface']))
        else:
            res += b'\x00'

        # we should also handle patch case
        res += netstruct.pack(b'I$', bytes.fromhex(component.get('implementation', '')))

    res = netstruct.pack(b'hI$', proto['expected_env_version'], res)
    return res


class Protocol(RpcQuery):

    def __init__(self, data=None, *args, **kwargs):
        super(Protocol, self).__init__(*args, **kwargs)
        self._data = data

    def __repr__(self):
        if self._data:
            return str(self._data)
        return super(Protocol, self).__repr__()

    def __call__(self, *args, **kwargs):
        if self._data:
            return self._data
        return super(Protocol, self).__call__(*args, **kwargs)

    def __iter__(self):
        return iter(proto_to_files(self()))

    @classmethod
    @lru_cache(maxsize=None)
    def from_uri(cls, uri):
        """
        Loads protocol implementation from various sources and converts it to the RPC-like format
        :param uri: link/path to a tar archive or path to a folder with extracted contents
        :return: Protocol instance
        """
        if uri.startswith('http'):
            files = url_to_files(uri)
        elif os.path.isfile(uri):
            files = tar_to_files(uri)
        elif os.path.isdir(uri):
            files = dir_to_files(uri)
        else:
            raise ValueError(uri)

        return Protocol(data=files_to_proto(files))

    def index(self) -> dict:
        """
        Generates TEZOS_PROTOCOL file
        :return: dict with protocol hash and modules
        """
        proto = self()
        data = {
            'hash': self.calculate_hash(),
            'modules': list(map(lambda x: x['name'], proto.get('components', [])))
        }
        return data

    def export_tar(self, output_path=None):
        """
        Creates a tarball and dumps to a file or returns bytes
        :param output_path: Path to the tarball [optional]. You can add .bz2 or .gz extension to make it compressed
        :return: bytes if path is None or nothing
        """
        files = proto_to_files(self())
        files.append(('TEZOS_PROTOCOL', json.dumps(self.index())))
        return files_to_tar(files, output_path)

    def diff(self, proto, context_lines=3):
        """
        Calculates file diff between two protocol versions
        :param proto: an instance of Protocol
        :param context_lines: number of context lines before and after the change
        :return: patch in proto format
        """
        assert isinstance(proto, Protocol)

        files = list()
        yours = proto_to_files(self())
        theirs = dict(iter(proto))

        for filename, text in yours:
            their_text = theirs.get(filename, '')
            diff_lines = unified_diff(
                a=their_text.split('\n'),
                b=text.split('\n'),
                n=context_lines,
                fromfile=filename,
                tofile=filename,
                lineterm=''
            )
            files.append((filename, '\n'.join(diff_lines)))

        return Protocol(data=files_to_proto(files))

    def apply(self, patch):
        """
        Applies unified diff and returns full-fledged protocol
        :param patch: an instance of Protocol containing diff of files
        :return: Protocol instance
        """
        assert isinstance(patch, Protocol)

        files = list()
        theirs = proto_to_files(patch())

        with TemporaryDirectory() as your_dir:
            for filename, text in self:
                with open(os.path.join(your_dir, filename), 'w') as f:
                    f.write(text)  # append newline (patch-apply workaround)

            for filename, text in theirs:
                if text:
                    patch_set = pypatch.fromstring(text.encode())
                    if not patch:
                        raise ValueError('Failed to load unified diff.')
                    if not patch_set.apply(root=your_dir):
                        raise ValueError(f'Failed to patch {filename}')

                with open(os.path.join(your_dir, filename), 'r') as f:
                    result = f.read()

                files.append((filename, result))  # remove newline (patch-apply workaround)

        return Protocol(data=files_to_proto(files))

    def calculate_hash(self):
        hash_digest = blake2b_32(proto_to_bytes(self())).digest()
        return base58_encode(hash_digest, b'P').decode()
