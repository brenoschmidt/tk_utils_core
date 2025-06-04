""" 
API

         
"""
from __future__ import annotations

from tk_utils_core.core._typing import (
        UNSET,
        )

from tk_utils_core.options import options

pretty_errors = UNSET
if options.pretty_errors.pretty_errors is True:
    try:
        import pretty_errors
        pretty_errors.configure(
            separator_character = '*',
            filename_display = pretty_errors.FILENAME_EXTENDED,
            line_number_first = options.pretty_errors.line_number_first,
            display_link = options.pretty_errors.display_link,
            #lines_before = 5,
            #lines_after = 2,
            #line_color = pretty_errors.RED + '> ' + pretty_errors.default_config.line_color,
            code_color = '  ' + pretty_errors.default_config.line_color,
            #truncate_code = True,
            #display_locals = True
            local_name_color = pretty_errors.YELLOW,
            exception_file_color = pretty_errors.YELLOW,
        )
    except ModuleNotFoundError:
        pass

