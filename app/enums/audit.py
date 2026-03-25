from enum import Enum 


class AuditActionType(str, Enum):
    CREATE        = "create"
    UPDATE        = "update"
    DELETE        = "delete"
    STATUS_CHANGE = "status_change"   # booking/payment lifecycle transitions
    LOGIN         = "login"
    LOGOUT        = "logout"
    EXPORT        = "export"          # data export events (GDPR traceability)
    IMPERSONATE   = "impersonate"     # admin acting on behalf of a client
