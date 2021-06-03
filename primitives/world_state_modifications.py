from enum import Enum


class WorldStateModificationType(Enum):
    add_asset_to_account = '00'
    sub_asset_from_account = '01'
    create_asset = 'f0'
    update_asset = 'f1'

