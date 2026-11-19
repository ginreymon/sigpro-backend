"""Menu option keys ("<module url>/<option url>") used to gate write endpoints.

Single source of truth: views import these constants instead of typing strings.
A new option needs its row in `core_option` and a grant to the admin role (see database/).
"""

# configuration
APP_SETTINGS = "configuration/app-settings"

# admin
ROLES = "admin/roles"
USERS = "admin/users"
MODULES = "admin/modules"
WORK_SHIFTS = "admin/work-shifts"
WORK_BREAKS = "admin/work-breaks"
GENERAL_CONFIG = "admin/general-config"
ORDER_EDITION = "admin/order-edition"
WORK_SESSIONS_ADMIN = "admin/work-sessions"

# production
PROD_DAY_OPERATION = "production/day-operation"
PROD_SHIFT_CYCLES = "production/shift-cycles"
SEWING_CONFIG = "production/sewing-config"

# stamping
STAMP_DAY_OPERATION = "stamping/day-operation"
STAMP_SHIFT_CYCLES = "stamping/shift-cycles"
MACHINES_CONFIG = "stamping/machines-config"
AUDITORY = "stamping/auditory"

# integration
MANUAL_INTEGRATION = "integration/manual-integration"
SIESA_OUTBOUND = "integration/siesa-outbound"

# Shared groups of options
SESSION_EDITORS_ADMIN = (ORDER_EDITION, WORK_SESSIONS_ADMIN)
INTEGRATION = (MANUAL_INTEGRATION, SIESA_OUTBOUND)
