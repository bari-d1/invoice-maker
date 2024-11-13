# Importing the main functions and utility functions from your module
from .main import (
    main,
    get_list_of_calendars,
    get_events,
    check_completed,
    check_cancelled,
    check_durartion,
    lessons_per_student,
    checkin_per_student,
    list_of_checkin,
    get_students,
    get_student_events,
    create_invoice
)

# The __init__.py file makes these functions directly available when importing the module.
