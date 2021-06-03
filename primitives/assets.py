from enum import Enum
from crypto.hashing import dsha256


class AssetType(Enum):
    """Implemented asset types.

        - integer means can be calculated
        - boolean means can be only in (0, 1)
    """
    integer = '00'
    boolean = '01'


class AssetStatus(Enum):
    """Implemented asset statuses.

        - active means can be transfered
        - inactive means can not be transfered

        Will be updated later
    """
    active = '00'
    inactive = '10'


class AssetOwnershipType(Enum):
    """Implemented asset ownership types.

        - owner
        - commision
        - agent
    """
    owner = '00'
    comission = '01'
    agent = '02'


class Asset(object):
    """Represents unique asset on blockchain.

    Public attributes:
        name — asset unique identifier
        type — asset type
        status — asset status
        state_hash — asset state hash

    Asset state is represented by name + type + active
    """
    name: str = None
    type: AssetType = None
    status: AssetStatus = None

    @property
    def state_hash(self) -> bytes:
        """Computes and returns asset state hash.

        Unique (in respect to collisions) for every possible asset state.

        :return: hash of current asset state
        :rtype: str
        """
        return dsha256(self.name + self.type.value + self.status.value).encode('utf-8')  # noqa

    def __init__(self, name: str, _type: AssetType, status: AssetStatus) -> None:
        """Initialization of object.

        :param name: name of asset
        :type name: str
        :param _type: type of asset
        :type _type: AssetType
        :param status: is asset active?
        :type status: bool
        """
        self.name = name
        self.type = _type
        self.status = status


# predefined Assets for _assets_trie

CREATE_ASSET = Asset('0' * 64, AssetType.boolean, AssetStatus.active)  # role to create new assets
UPDATE_ASSET = Asset('0' * 63 + '1', AssetType.boolean, AssetStatus.active)  # role to update assets (basically — asst.active)
CURRENCY_ASSET = Asset('f' * 64, AssetType.integer, AssetStatus.active)  # main currency asset
