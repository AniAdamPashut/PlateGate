from enum import Enum


class SugDelek(Enum):
    UNKNOWN = 0,
    BENZIN = 1,
    LPG = 2,
    DIESEL = 3,
    ELECTRIC = 4,
    BENZIN_ELECTRIC = 5,
    DIESEL_ELECTRIC = 7


fuel_map = {
    'בנזין': SugDelek.BENZIN,
    'גפ"מ': SugDelek.LPG,
    'דיזל': SugDelek.DIESEL,
    'חשמל': SugDelek.ELECTRIC,
    'חשמל/בנזין': SugDelek.BENZIN_ELECTRIC,
    'חשמל/דיזל': SugDelek.DIESEL_ELECTRIC,
    'גז טבעי דחוס': SugDelek.UNKNOWN,
    'לא ידוע קוד 0': SugDelek.UNKNOWN
}

