from enum import Enum


class SugRechev(Enum):
    UNKNOWN = 0  # לא ידוע
    PRIVATE = 1  # רכב פרטי
    COMMERCIAL = 2  # רכב מסחרי
    TRACTOR = 3  # טרקטור
    WORK_VEHICLE = 4  # רכב עבודה (שופל)
    BUS = 5  # אוטובוס
    TAXI = 6  # מונית
    CARRY = 7  # משא
    CARRIED = 8  # גרור
    MOTORCYCLE = 9  # אופנוע


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
    'M': SugRechev.COMMERCIAL,
    '0': SugRechev.MOTORCYCLE,
    '1': SugRechev.PRIVATE,
    '2': SugRechev.CARRY,
    '3': SugRechev.PRIVATE,
    '4': SugRechev.CARRIED,
    '5': SugRechev.CARRIED,
    '6': SugRechev.BUS,
    '7': SugRechev.WORK_VEHICLE,
    '8': SugRechev.TRACTOR
}
