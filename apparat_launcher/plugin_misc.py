#!/usr/bin/python
"""plugin: misc (optional)"""

## general
import os
import wx

## apparat
import ini
import tools



# -----------------------------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------------------------
TRIGGER = ('!open',)


# -----------------------------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------------------------
def parse(current_search_string, main_window):
    """Validates the misc command and calls the matching sub function"""
    tools.debug_output(__name__, 'parse', 'starting', 1)

    # Reset status notification back to OK
    main_window.status_notification_reset()

    icon_size = ini.read_single_ini_value('General', 'icon_size') # get preference value

    if current_search_string.startswith('!open'):
        tools.debug_output(__name__, 'parse', 'Case: Open', 1)
        prepare_plugin_misc_open(main_window, icon_size)

    else:
        tools.debug_output(__name__, 'parse', 'Error: Unexpected misc plugin command', 3)
        main_window.status_notification_display_error('Unexpected misc plugin command')

    tools.debug_output(__name__, 'parse', 'finished', 1)


def prepare_plugin_misc_open(main_window, icon_size):
    """Plugin Misc - Open - Opens file or location using xdg-open"""
    tools.debug_output(__name__, 'prepare_plugin_misc_open', 'starting', 1)
    main_window.plugin__update_general_ui_information('Misc (Open)') ## update plugin info

    ## command button & txt
    main_window.ui__bt_command_img = wx.Image('gfx/plugins/misc/'+icon_size+'/open.png', wx.BITMAP_TYPE_PNG)
    main_window.ui__bt_command.SetBitmap(main_window.ui__bt_command_img.ConvertToBitmap())
    main_window.ui__bt_command.SetToolTipString('Open')

    if(len(main_window.ui__cb_search.GetValue()) > 6) and  (main_window.ui__cb_search.GetValue()[6:] != ''):
        ## parameter button
        main_window.ui__bt_parameter.SetToolTipString('Open')
        main_window.ui__bt_parameter_img = wx.Image('gfx/core/'+icon_size+'/execute.png', wx.BITMAP_TYPE_PNG)
        main_window.ui__bt_parameter.SetBitmap(main_window.ui__bt_parameter_img.ConvertToBitmap())

        ## set parameter
        if (main_window.ui__cb_search.GetValue()[6:7] == '~'):
            tools.debug_output(__name__, 'prepare_plugin_misc_open', 'Replacing ~', 1)
            home = os.environ['HOME']
            main_window.ui__txt_parameter.SetValue(home+main_window.ui__cb_search.GetValue()[7:]) # possible parameter
        else:
            main_window.ui__txt_parameter.SetValue(main_window.ui__cb_search.GetValue()[6:]) # possible parameter

        ## set command
        main_window.ui__txt_command.SetValue('xdg-open')
    else:
        tools.debug_output(__name__, 'prepare_plugin_misc_open', 'Incomplete input, waiting for more...', 2)
