class SystemConstants:

    class Order:
        class Status:
            ACTIVE = 'Active'
            CANCELLED = 'Cancelled'
            STOPPED = 'Stopped'
            PAUSED = 'Paused'
            WAITING_RENEWAL = 'Waiting Renewal'

    class Setting:
        SYSTEM_SETTINGS = 'system_settings'

    class SupportStatus:
        OPEN = 'Open'
        CLOSE = 'Close'

    class DiscountCodeDuration:
        ONE_TIME = 'one time'
        MONTHLY = 'monthly'
        FIRST_THREE_MONTH = 'first 3 months'
        ANNUALLY = 'annually'
        MULTI = 'multi'
