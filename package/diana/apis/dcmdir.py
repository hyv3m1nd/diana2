import os, logging, hashlib
from typing import Union
import attr
from ..dixel import Dixel
from . import Redis
from ..utils import Endpoint, Serializable
from ..utils.gateways import DcmFileHandler


@attr.s
class DcmDir(Endpoint, Serializable):

    name = attr.ib(default="DcmDir")
    path = attr.ib(default=".")
    subpath_width = attr.ib(default=2)
    subpath_depth = attr.ib(default=0)

    gateway = attr.ib(init=False, repr=False)
    @gateway.default
    def setup_gateway(self):
        return DcmFileHandler(path=self.path,
                              subpath_width = self.subpath_width,
                              subpath_depth = self.subpath_depth)

    def put(self, item: Dixel, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP PUT")
        if not item.file:
            raise ValueError("Dixel has no file attribute, can only save file data")
        self.gateway.write_file(item.fn(), item.file)

    def update(self, fn: str, item: Dixel, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP UPDATE")
        if not item.file:
            raise ValueError("Dixel has no file attribute, can only save file data")
        self.gateway.write_file(fn, Dixel.file)

    def get(self, item: Union[str, Dixel], get_pixels=False, get_file=False, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP GET")
        if isinstance(item, str):
            fn = item
        elif isinstance(item, Dixel) or hasattr(item, 'fn'):
            fn = item.fn()
        else:
            raise ValueError("Item has no fn attribute, so it requires an explicit filename")

        if not self.exists(fn):
            raise FileNotFoundError

        ds = self.gateway.get(fn, get_pixels=get_pixels)
        result = Dixel.from_pydicom(ds, fn)

        if get_file:
            result.file = self.gateway.read_file(fn)

        return result


    def delete(self, item: Union[str, Dixel], **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP DELETE")
        if isinstance(item, str):
            fn = item
        elif isinstance(item, Dixel) or hasattr(item, 'fn'):
            fn = item.fn()
        else:
            raise ValueError("Item has no fn attribute, so it requires an explicit filename")
        return self.gateway.delete(fn)

    def exists(self, fn: str):
        logger = logging.getLogger(self.name)
        logger.debug("EP EXISTS")
        return self.gateway.exists(fn)

    def check(self):
        logger = logging.getLogger(self.name)
        logger.debug("EP CHECK")
        return os.path.exists(self.path)

    def index_to(self, R: Redis):
        """If indexing Orthanc dir, use subpath width/depth = 2"""

        prefix = hashlib.md5(self.path.encode("UTF-*")).hexdigest()[0:4] + "-"

        for root, dirs, fns in os.walk(self.path, topdown = False):
            for fn in fns:
                try:
                    ds = self.gateway.get(fn=fn)
                    d = Dixel.from_pydicom(ds, fn)
                    R.register(d, prefix=prefix)
                except:
                    # logging.warning("Failed to read file {}".format(fn))
                    pass

    def indexed_studies(self, R: Redis):
        prefix = hashlib.md5(self.path.encode("UTF-*")).hexdigest()[0:4] + "-"
        result = R.registry_items(prefix)
        return result

    def get_indexed_study(self, item: str, R: Redis):
        prefix = hashlib.md5(self.path.encode("UTF-*")).hexdigest()[0:4] + "-"
        result = R.registry_item_data(item, prefix=prefix)
        return result