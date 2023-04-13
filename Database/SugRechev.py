from enum import Enum


class SugRechev(Enum):
    UNKNOWN = 0,
    PRIVATE = 1,
    COMMERCIAL = 2,
    TRACTOR = 3,
    WORK_VEHICLE = 4,
    BUS = 5,
    TAXI = 6,
    CARRY = 7,
    CARRIED = 8,
    MOTORCYCLE = 9


rechev_map = {
    'פרטי': SugRechev.PRIVATE,
    'מסחרי': SugRechev.COMMERCIAL,
    'רכב עבודה': SugRechev.WORK_VEHICLE,
    'אוטובוס': SugRechev.BUS,
    'מונית': SugRechev.TAXI,
    'טרקטור': SugRechev.TRACTOR,
    'משא': SugRechev.CARRY,
    'גרור נתמך': SugRechev.CARRIED,
    'P': SugRechev.PRIVATE,
    'M': SugRechev.COMMERCIAL
}