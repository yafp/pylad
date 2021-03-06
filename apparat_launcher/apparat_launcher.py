#!/usr/bin/python
"""Core script of apparat_launcher"""

# NAME:         apparat_launcher
# DESCRIPTION:  an application launcher for linux
# AUTHOR:       yafp
# URL:          https://github.com/yafp/apparat_launcher

# -----------------------------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------------------------
import sys                          # to show python version used

if sys.version_info >= (3, 0):
    sys.stdout.write('Python version used: '+sys.version) ## show python version
    sys.stdout.write('Sorry, requires Python 2.x, not Python 3.x. Code might not work on Python3. Aborting now...\n')
    sys.exit(1)

else: # python 2.x
    ## general
    import difflib                      # for intelligent list sort
    import fnmatch                      # for searching applications
    import os                           # for searching applications
    import platform                     # check platform & linux distribution
    import webbrowser                   # for opening urls (example: github project page)
    import subprocess                   # for checking if cmd_exists
    import wx                           # for all the WX GUI items
    import xdg                          # for icon & icon-theme handling
    import xdg.IconTheme                # for icon & icon-theme handling

    ## apparat
    import constants                    # contains some constants
    import ini                          # ini file handling
    import prefs                        # preference window
    import plugin_core
    import plugin_kill
    import plugin_misc
    import plugin_nautilus
    import plugin_passwordgen
    import plugin_screenshot
    import plugin_search_internet
    import plugin_search_local
    import plugin_session
    import plugin_shell
    import tools                        # contains helper-tools
    import tray_icon                    # tray icon and menu
    import version                      # defines the appat version


# -----------------------------------------------------------------------------------------------
# CONFIG (DEVELOPER)
# -----------------------------------------------------------------------------------------------
is_combobox_open = 0
is_resetted = True
icon_size = 128

# -----------------------------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------------------------

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# MAIN-WINDOW
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class MyFrame(wx.Frame): # pylint:disable=too-many-instance-attributes,too-many-public-methods

    """Class for MainWindow"""

    def __init__(self, parent, title): # pylint:disable=too-many-statements
        """Initialize the MainWindow"""
        ## Update Statistics (ini) - Apparat launched
        tools.debug_output(__name__, '__init__', 'Updating statistics (apparat_started)', 1)
        cur_app_start_count = ini.read_single_ini_value('Statistics', 'apparat_started') # get current value from ini
        ini.write_single_ini_value('Statistics', 'apparat_started', int(cur_app_start_count)+1) # update ini +1

        global icon_size
        icon_size = ini.read_single_ini_value('General', 'icon_size') # update preference value

        ## Define the style of the frame
        main_ui_style = (wx.MINIMIZE_BOX | wx.CLIP_CHILDREN | wx.NO_BORDER | wx.FRAME_SHAPED | wx.FRAME_NO_TASKBAR) # wx.NO_BORDER = no window decoration & not moveable
        self.mainUI = wx.Frame.__init__(self, parent, title=title, size=(constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT), style=main_ui_style) # Custom Frame

        self.SetSizeHintsSz(wx.Size(constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT), wx.Size(constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT)) # forcing min and max size to same values - prevents resizing option
        self.tbicon = tray_icon.TaskBarIcon(self)
        self.Bind(wx.EVT_CLOSE, self.on_close_application)

        ## define and set an application icon
        app_icon = wx.Icon('gfx/core/16/appIcon.png', wx.BITMAP_TYPE_PNG)
        self.SetIcon(app_icon)

        # color of main window
        self.SetBackgroundColour(wx.Colour(237, 237, 237))

        ## Define UI Elements
        ##
        ## Some general bitmaps which might be needed for some button states
        self.ui__bt_img_search = wx.Bitmap('gfx/core/'+icon_size+'/search.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_img_blank = wx.Bitmap('gfx/core/'+icon_size+'/blank.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_img_execute_black = wx.Bitmap('gfx/core/'+icon_size+'/execute_black.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_img_appicon = wx.Bitmap('gfx/core/'+icon_size+'/appIcon.png', wx.BITMAP_TYPE_PNG)

        ## Button: status
        self.ui__bt_status_img = wx.Bitmap('gfx/core/16/blank.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_status = wx.BitmapButton(self, id=wx.ID_ANY, style=wx.NO_BORDER, bitmap=self.ui__bt_status_img, size=(self.ui__bt_status_img.GetWidth()+16, self.ui__bt_status_img.GetHeight()+16))
        self.ui__bt_status.SetBitmapFocus(wx.NullBitmap)
        self.ui__bt_status.SetBitmapHover(wx.NullBitmap)
        self.ui__bt_status.SetLabel('Status')
        self.ui__bt_status.Enable(False)

        ## Text: Plugin Information
        self.ui__txt_plugin_information = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_CENTRE | wx.BORDER_NONE | wx.TE_RICH | wx.TE_MULTILINE)
        self.ui__txt_plugin_information.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Sans'))
        self.ui__txt_plugin_information.SetMinSize(wx.Size(586, 18))
        self.ui__txt_plugin_information.SetMaxSize(wx.Size(586, 18))
        self.ui__txt_plugin_information.Enable(False)
        self.ui__txt_plugin_information.SetLabel('Plugin Information')
        self.ui__txt_plugin_information.SetBackgroundColour(wx.Colour(237, 237, 237))

        ## Button: Preferences
        self.ui__bt_prefs_img = wx.Bitmap('gfx/core/16/prefs.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_prefs_img_focus = wx.Bitmap('gfx/core/16/prefs_black.png', wx.BITMAP_TYPE_PNG) # #c0392b
        self.ui__bt_prefs = wx.BitmapButton(self, id=wx.ID_ANY, style=wx.NO_BORDER, bitmap=self.ui__bt_prefs_img, size=(self.ui__bt_prefs_img.GetWidth()+16, self.ui__bt_prefs_img.GetHeight()+16))
        self.ui__bt_prefs.SetBitmapFocus(self.ui__bt_prefs_img_focus)
        self.ui__bt_prefs.SetBitmapHover(self.ui__bt_prefs_img_focus)
        self.ui__bt_prefs.SetLabel('Preferences')
        self.ui__bt_prefs.SetToolTipString(u'Preferences')
        self.ui__bt_prefs.Enable(True)

        ## Text: result counter
        self.ui__txt_result_counter = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_CENTRE)
        self.ui__txt_result_counter.SetFont(wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Sans'))
        self.ui__txt_result_counter.SetMinSize(wx.Size(50, 50))
        self.ui__txt_result_counter.SetMaxSize(wx.Size(50, 50))
        self.ui__txt_result_counter.SetEditable(False)
        self.ui__txt_result_counter.Enable(False)
        self.ui__txt_result_counter.SetValue('0')

        ## Search & Results as comboBox
        search_results = []
        combo_box_style = wx.TE_PROCESS_ENTER
        self.ui__cb_search = wx.ComboBox(self, wx.ID_ANY, u'', wx.DefaultPosition, wx.Size(550, 50), search_results, style=combo_box_style)
        self.ui__cb_search.SetFont(wx.Font(24, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Sans'))
        self.ui__cb_search.SetLabel('Search')

        ## Button: command
        self.ui__bt_command_img = wx.Image('gfx/core/'+icon_size+'/blank.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_command = wx.BitmapButton(self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.Size(300, 300), wx.BU_AUTODRAW)
        self.ui__bt_command.SetBitmapHover(wx.NullBitmap)
        self.ui__bt_command.SetBitmapDisabled(self.ui__bt_img_appicon)
        self.ui__bt_command.SetBitmap(self.ui__bt_command_img.ConvertToBitmap())
        self.ui__bt_command.SetLabel('Applications')
        self.ui__bt_command.Enable(False)

        ## Button: parameter
        self.ui__bt_parameter_img = wx.Image('gfx/core/'+icon_size+'/blank.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_parameter = wx.BitmapButton(self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.Size(300, 300), wx.BU_AUTODRAW)
        self.ui__bt_parameter.SetBitmapFocus(self.ui__bt_img_execute_black) # image when in focus
        self.ui__bt_parameter.SetBitmapHover(wx.NullBitmap) # image on hover
        self.ui__bt_parameter.SetBitmapDisabled(self.ui__bt_img_search)
        self.ui__bt_parameter.SetBitmap(self.ui__bt_parameter_img.ConvertToBitmap())
        self.ui__bt_parameter.SetLabel('Options')
        self.ui__bt_parameter.Enable(False)

        ## Text: command
        self.ui__txt_command = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_CENTRE | wx.BORDER_NONE | wx.TE_RICH | wx.TE_MULTILINE) # rich & multiline for coloring
        self.ui__txt_command.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Sans'))
        self.ui__txt_command.SetMinSize(wx.Size(300, 18))
        self.ui__txt_command.SetMaxSize(wx.Size(300, 18))
        self.ui__txt_command.Enable(False)
        self.ui__txt_command.SetLabel('Applications String')
        self.ui__txt_command.SetBackgroundColour(wx.Colour(237, 237, 237))

        ## Text: parameter
        self.ui__txt_parameter = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_CENTRE | wx.BORDER_NONE | wx.TE_RICH | wx.TE_MULTILINE )
        self.ui__txt_parameter.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Sans'))
        self.ui__txt_parameter.SetMinSize(wx.Size(300, 18))
        self.ui__txt_parameter.SetMaxSize(wx.Size(300, 18))
        self.ui__txt_parameter.Enable(False)
        self.ui__txt_parameter.SetLabel('Parameter String')
        self.ui__txt_parameter.SetBackgroundColour(wx.Colour(237, 237, 237))

        ## Text: Version Information
        self.ui__txt_version_information = wx.StaticText(self, wx.ID_ANY, ' v'+version.APP_VERSION, wx.DefaultPosition, wx.DefaultSize, 0)
        self.ui__txt_version_information.SetFont(wx.Font(8, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Sans'))
        self.ui__txt_version_information.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

        ## Layout/Sizer
        b_sizer = wx.BoxSizer(wx.VERTICAL) # define layout container

        ## line 1: status - plugin-info - preferences
        box0 = wx.BoxSizer(wx.HORIZONTAL)
        box0.Add(self.ui__bt_status, 0, wx.ALIGN_LEFT, 100) # status icon button
        box0.Add(self.ui__txt_plugin_information, 0, wx.CENTRE) # plugin info
        box0.Add(self.ui__bt_prefs, 0, wx.ALIGN_RIGHT, 100) # preferences icon button
        b_sizer.Add(box0, 0, wx.EXPAND)

        ## line 2: search
        box1 = wx.BoxSizer(wx.HORIZONTAL)
        box1.Add(self.ui__txt_result_counter, 0, wx.CENTRE) # result counter
        box1.Add(self.ui__cb_search, 0, wx.CENTRE) # combobox
        b_sizer.Add(box1, 0, wx.CENTRE)
        b_sizer.AddSpacer(2)

        ## line 3: buttons
        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box2.Add(self.ui__bt_command, 0, wx.CENTRE) # application button
        box2.Add(self.ui__bt_parameter, 0, wx.CENTRE) # parameter button
        b_sizer.Add(box2, 0, wx.CENTRE)

        ## line 4: text command and parameter
        box3 = wx.BoxSizer(wx.HORIZONTAL)
        box3.Add(self.ui__txt_command, 0, wx.CENTRE) # command
        box3.Add(self.ui__txt_parameter, 0, wx.CENTRE) # parameter
        b_sizer.Add(box3, 0, wx.CENTRE)
        b_sizer.AddSpacer(10)

        ## line 5: version
        b_sizer.Add(self.ui__txt_version_information, 0, wx.CENTRE) # version
        self.SetSizer(b_sizer)


        ## Bind/Connect Events
        ##
        ## Button: status
        self.ui__bt_status.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

        ## Button: preference
        self.ui__bt_prefs.Bind(wx.EVT_KEY_DOWN, self.on_key_down) # on key -> back to search
        self.ui__bt_prefs.Bind(wx.EVT_BUTTON, self.on_clicked) # open preferences

        ## combobox
        self.ui__cb_search.Bind(wx.EVT_KEY_UP, self.on_combobox_key_press)                  # Released any key
        self.ui__cb_search.Bind(wx.EVT_TEXT, self.on_combobox_text_changed)                 # combobox text changes.
        self.ui__cb_search.Bind(wx.EVT_TEXT_ENTER, self.on_combobox_enter)                  # Pressed Enter
        self.ui__cb_search.Bind(wx.EVT_COMBOBOX, self.on_combobox_select_item)              # Item selected
        self.ui__cb_search.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.on_combobox_popup_open)      # Popup opened
        self.ui__cb_search.Bind(wx.EVT_COMBOBOX_CLOSEUP, self.on_combobox_popup_close)      # Popup closed
        self.ui__cb_search.Bind(wx.EVT_KEY_DOWN, self.on_key_down)                          # Pressed any key

        ## Button: command
        self.ui__bt_parameter.Bind(wx.EVT_KEY_DOWN, self.on_key_down) # on key -> back to

        ## Button: parameter
        self.ui__bt_parameter.Bind(wx.EVT_KEY_DOWN, self.on_key_down) # on key -> back to
        self.ui__bt_parameter.Bind(wx.EVT_BUTTON, self.on_clicked_parameter_button)

        #self.Bind(wx.EVT_KEY_DOWN, self.on_key_down) ## Handle clicks outside of the expected area main ui or none

        ## Bind mouse in & out of main window events
        #wx.EVT_ENTER_WINDOW(self, self.OnEnter)
        #wx.EVT_LEAVE_WINDOW(self, self.OnLeave)

        ## Finish setting up the main UI & show it
        transparency = ini.read_single_ini_value('General', 'transparency') # get preference value
        self.SetTransparent(int(transparency))       # 0-255
        self.ui__cb_search.SetFocus()     # set focus to search
        self.Center()                   # open window centered
        self.Show(True)                 # show main UI


    def on_key_down(self, event):
        """On Key Down in main ui"""
        tools.debug_output(__name__, 'on_key_down', 'starting with event: '+str(event), 1)
        tools.debug_output(__name__, 'on_key_down', 'Currently focus is at: '+str(self.FindFocus()), 1)
        focused_object = self.FindFocus()
        tools.debug_output(__name__, 'on_key_down', str(focused_object), 1)
        if focused_object is None or focused_object == 'None':
            tools.debug_output(__name__, 'on_key_down', 'Focused object is empty', 2)
            self.ui__bt_command.SetFocus()
            tools.debug_output(__name__, 'on_key_down', 'Set focus to command button, ending function here.', 1)
            return

        tools.debug_output(__name__, 'on_key_down', focused_object.GetLabel(), 1)

        if focused_object.GetLabel() == 'Status' or focused_object.GetLabel() == 'Preferences':
            self.ui__cb_search.SetFocus() # set focus to search
            self.ui__cb_search.SetInsertionPointEnd() # set cursor to end of string
            tools.debug_output(__name__, 'on_key_down', 'Set focus back to search.', 1)
            return

        if focused_object.GetLabel() == 'Search':
            event.Skip() # to jump to next possible event: here: key_up (on_combobox_key_press) to start actual search
            return

        if focused_object.GetLabel() == 'Applications':
            self.ui__bt_parameter.SetFocus()
            tools.debug_output(__name__, 'on_key_down', 'Set focus to parameter button', 1)
            return

        if focused_object.GetLabel() == 'Options':
            self.ui__cb_search.SetFocus() # set focus to search
            self.ui__cb_search.SetInsertionPointEnd() # set cursor to end of string
            tools.debug_output(__name__, 'on_key_down', 'Set focus back to search.', 1)
            return

        else:
            tools.debug_output(__name__, 'on_key_down', 'Focus in on an unexpected place', 2)
            tools.debug_output(__name__, 'on_key_down', focused_object.GetLabel(), 1)
            self.ui__cb_search.SetFocus() # set focus to search
            self.ui__cb_search.SetInsertionPointEnd() # set cursor to end of string
            tools.debug_output(__name__, 'on_key_down', 'Set focus back to search.', 1)


    def on_close_application(self, event):
        """Method to close the app"""
        tools.debug_output(__name__, 'on_close_application', 'starting with event: '+str(event), 1)
        self.tbicon.RemoveIcon()
        self.tbicon.Destroy()
        self.Destroy()
        wx.GetApp().ExitMainLoop()
        event.Skip()


    def on_clicked_parameter_button(self, event):
        """If the parameter button was clicked"""
        tools.debug_output(__name__, 'on_clicked_parameter_button', 'starting with event: '+str(event), 1)
        self.do_execute()
        self.ui__cb_search.SetFocus()


    def on_clicked(self, event):
        """General click handler - using label to find source"""
        tools.debug_output(__name__, 'on_clicked', 'starting with event: '+str(event), 1)
        btn = event.GetEventObject().GetLabel()
        if btn == 'Preferences':
            self.open_preference_window()
        else:
            tools.debug_output(__name__, 'on_clicked', 'Something else got clicked', 2)


    # method exists in apprat_launcher & tray_icon right now - Baustelle
    def open_preference_window(self):
        """Opens the preference window"""
        tools.debug_output(__name__, 'open_preference_window', 'starting', 1)
        self.prefWindow = prefs.PreferenceWindow(parent=None, idd=-1)
        self.prefWindow.Show()


    def on_combobox_text_changed(self, event):
        """Triggered if the combobox text changes"""
        tools.debug_output(__name__, 'on_combobox_text_changed', 'starting with event:'+str(event), 1)
        if self.ui__cb_search.GetValue() == '': #searchstring is empty
            tools.debug_output(__name__, 'on_combobox_text_changed', 'Searchstring: <empty>. Nothing do to', 1)
        else:
            tools.debug_output(__name__, 'on_combobox_text_changed', 'Searchstring: '+self.ui__cb_search.GetValue().lower(), 1)
            global is_resetted
            is_resetted = False


    def on_combobox_enter(self, event):
        """Triggered if Enter was pressed in combobox"""
        tools.debug_output(__name__, 'on_combobox_enter', 'starting with event: '+str(event), 1)
        if len(self.ui__cb_search.GetValue()) > 0:
            global is_resetted
            is_resetted = False

            global is_combobox_open
            if is_combobox_open == 0:
                self.do_execute()

            else: ## enter was pressed to close the combobox
                tools.debug_output(__name__, 'on_combobox_enter', 'Pressed enter to close the open combobox', 1)
                is_combobox_open = 0 # global var to keep track if dropdown is open or closed

                ## run search again after selecting the desired search string from dropdown
                self.parse_user_input(self.ui__cb_search.GetValue().lower())
        else:
            tools.debug_output(__name__, 'on_combobox_enter', 'Combobox is empty, nothing to do here.', 1)


    def on_combobox_select_item(self, event):
        """If an item of the result-list was selected"""
        tools.debug_output(__name__, 'on_combobox_select_item', 'starting with event: '+str(event), 1)

        if(self.ui__txt_plugin_information.GetValue() == 'Plugin: Local Search'): # Local search is always using xdg open - special case
            self.ui__txt_parameter.SetValue(self.ui__cb_search.GetValue().lower()) # write command to command text field
        else: ## default-case
            self.ui__txt_command.SetValue(self.ui__cb_search.GetValue().lower()) # write command to command text field
            self.get_icon(self.ui__cb_search.GetValue().lower()) # get icon for selected executable

        self.ui__cb_search.SetInsertionPointEnd() # set cursor to end of string
        tools.debug_output(__name__, 'on_combobox_select_item', 'finished', 1)


    def on_combobox_popup_open(self, event):
        """If the popup of the combobox gets opened"""
        tools.debug_output(__name__, 'on_combobox_popup_open', 'starting with event: '+str(event), 1)
        global is_combobox_open
        is_combobox_open = True

        ## select the first item from list
        self.ui__cb_search.SetSelection(0) # is default
        if 'Ubuntu' in platform.linux_distribution():
            subprocess.Popen(["xdotool", "key", "Down"]) # simulate key press to highlight the choosen value as well
        tools.debug_output(__name__, 'on_combobox_popup_open', 'finished', 1)


    def on_combobox_popup_close(self, event):
        """If the popup of the combobox is closed"""
        tools.debug_output(__name__, 'on_combobox_popup_close', 'starting with event: '+str(event), 1)
        tools.debug_output(__name__, 'on_combobox_popup_close', 'combobox just got closed', 1)
        self.get_icon(self.ui__cb_search.GetValue().lower()) # get icon for selected executable
        global is_combobox_open
        is_combobox_open = False
        tools.debug_output(__name__, 'on_combobox_popup_close', 'finished', 1)


    def on_combobox_key_press(self, event): # pylint:disable=too-many-branches
        """If content of the searchfield of the combobox changes"""
        tools.debug_output(__name__, 'on_combobox_key_press', 'starting with event: '+str(event), 1)
        global is_combobox_open

        current_keycode = event.GetKeyCode()
        tools.debug_output(__name__, 'on_combobox_key_press', 'KeyCode: '+str(current_keycode), 1)

        if current_keycode == 27: # Key: ESC
            tools.debug_output(__name__, 'on_combobox_key_press', 'ESC in combobox', 1)
            if(is_resetted is False):
                tools.debug_output(__name__, 'on_combobox_key_press', 'Launch reset method', 1)
                self.reset_ui()
            else: # hide main window
                tools.debug_output(__name__, 'on_combobox_key_press', 'UI is already resetted', 1)
                self.tbicon.execute_tray_icon_left_click() # click tray-icon to hide main-ui

        elif current_keycode == wx.WXK_BACK: # Key: Backspace
            tools.debug_output(__name__, 'on_combobox_key_press', 'Pressed Backspace', 1)
            current_search_string = self.ui__cb_search.GetValue().lower()
            if(current_search_string.startswith('!')) and (self.ui__txt_result_counter.GetValue() != '0'): # if user is correcting a wrong input - dont autocomplete again
                self.get_enabled_plugin_trigger(current_search_string, autocomplete=False) # False to prevent re-autocomplete after user tried to revert the former autocomplete
            else: # most likely a normal search for executables
                self.parse_user_input(current_search_string)

        elif current_keycode == wx.WXK_TAB: # Key: Tab
            event.Skip()

        elif current_keycode == 317:    # Key: Arrow Down
            tools.debug_output(__name__, 'on_combobox_key_press', 'ARROW DOWN in combobox', 1)
            if(self.ui__txt_result_counter.GetValue() != '0'):
                self.ui__cb_search.Popup()
                tools.debug_output(__name__, 'on_combobox_key_press', 'Opening dropdown', 1)
                is_combobox_open = 1
            else:
                tools.debug_output(__name__, 'on_combobox_key_press', 'No result, so no need to open the dropdown', 1)
                is_combobox_open = 0

        elif current_keycode == 13: # Key: Enter
            tools.debug_output(__name__, 'on_combobox_key_press', 'ENTER was pressed - ignoring it because of "on_combobox_enter"', 1)
            self.parse_user_input(self.ui__cb_search.GetValue().lower())
            is_combobox_open = 0

        else:
            current_search_string = self.ui__cb_search.GetValue().lower()
            if (current_search_string) == "":
                tools.debug_output(__name__, 'on_combobox_key_press', 'Searchstring: <empty>. Trigger reset_ui method', 1)
                self.reset_ui()
            else:
                tools.debug_output(__name__, 'on_combobox_key_press', 'Searching: '+current_search_string, 1)
                self.parse_user_input(current_search_string)


    def get_icon(self, full_executable_name): # pylint:disable=too-many-branches,too-many-statements
        """Tries to get an icon for an executable by name"""
        tools.debug_output(__name__, 'get_icon', 'Starting icon search for: '+full_executable_name, 1)

        ## Abort if a plugin is activated
        if(self.ui__txt_plugin_information.GetValue() != '') or self.ui__cb_search.GetValue().startswith('!'):
            tools.debug_output(__name__, 'get_icon', 'Aborted as everything points into plugin direction', 2)
            return

        global icon_size
        icon_size = ini.read_single_ini_value('General', 'icon_size') # update preference value

        # detect users current icontheme-name
        theme = os.popen('gsettings get org.gnome.desktop.interface icon-theme').read() # via: https://ubuntuforums.org/showthread.php?t=2100795
        theme = theme.partition("'")[-1].rpartition("'")[0] # build substring

        if theme is None: # fallback to hicolor icon theme if none was detected
            theme = xdg.Config.icon_theme # hicolor
            tools.debug_output(__name__, 'get_icon', 'Using fallback icon theme hicolor', 2)

        tools.debug_output(__name__, 'get_icon', 'Using icon theme: '+theme, 1)
        icon = xdg.IconTheme.getIconPath(full_executable_name, size=int(icon_size), theme=theme, extensions=['png'])

        if(icon is None) or (icon is "") or '.svg' in icon: # use default icon
            new_app_icon = wx.Image('gfx/core/'+icon_size+'/missingAppIcon.png', wx.BITMAP_TYPE_PNG)
            tools.debug_output(__name__, 'get_icon', 'Selected icon: DEFAULT', 2)
        else:
            tools.debug_output(__name__, 'get_icon', 'Selected icon: '+icon, 1)
            new_app_icon = wx.Image(icon, wx.BITMAP_TYPE_ANY)    # define new image
            new_app_icon.Rescale(int(icon_size), int(icon_size)) # rescale image

        ## command button
        self.ui__bt_command.SetBitmap(new_app_icon.ConvertToBitmap()) # set icon to button
        self.ui__bt_command.Enable(True) # Enable the button

        ## parameter button
        self.ui__bt_parameter_img = wx.Image('gfx/core/'+icon_size+'/execute.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_parameter.SetBitmap(self.ui__bt_parameter_img.ConvertToBitmap())
        self.ui__bt_parameter.Enable(True) # Enable parameter button
        self.ui__bt_parameter.SetToolTipString('Launch') # set tooltip


    def plugin__update_general_ui_information(self, plugin_name):
        """set some general UI values after having a plugin triggered"""
        tools.debug_output(__name__, 'plugin__update_general_ui_information', 'started', 1)
        if(plugin_name != ''):
            self.ui__bt_command.Enable(True) # enable command button
            self.ui__bt_parameter.Enable(True) # Enable parameter button
            self.ui__txt_result_counter.SetValue('1') ## set result-count
            self.ui__txt_command.SetValue(self.ui__cb_search.GetValue().lower()[:3]) ## update command (Example: !g)
            self.ui__txt_plugin_information.SetValue('Plugin: '+plugin_name) # Plugin Name in specific field
            tools.debug_output(__name__, 'plugin__update_general_ui_information', 'Plugin '+plugin_name+' activated', 1)

            self.status_notification_got_distinct_result()
        else:
            ## command button
            self.ui__bt_command.SetBitmap(self.ui__bt_command_img.ConvertToBitmap())
            self.ui__bt_command.Enable(False)

            ## parameter button
            self.ui__bt_parameter_img = wx.Image('gfx/core/'+icon_size+'/blank.png', wx.BITMAP_TYPE_PNG)
            self.ui__bt_parameter.SetBitmap(self.ui__bt_parameter_img.ConvertToBitmap())
            self.ui__bt_parameter.SetToolTipString('')
            self.ui__bt_parameter.Enable(False) # Enable parameter button

            ## result-count
            self.ui__txt_result_counter.SetValue('0')

            ## Plugin information
            self.ui__txt_plugin_information.SetValue(plugin_name)

            ## reset command and parameter
            self.ui__txt_command.SetValue('')
            self.ui__txt_parameter.SetValue('')


    def get_enabled_plugin_trigger(self, current_search_string, autocomplete=True):
        """Fill result list with all triggers from the enabled plugins"""
        tools.debug_output(__name__, 'get_enabled_plugin_trigger', 'starting', 1)

        ## collect all plugin commands from the enabled plugins and add them to the dropdown
        plugin_commands = plugin_core.TRIGGER # add core commands

        for current_plugin in plugin_core.PLUGINS:
            if current_plugin != 'plugin_search_local': # plugin_search_local gets ignored
                ## check if plugin is currently enabled
                tools.debug_output(__name__, 'get_enabled_plugin_trigger', 'Checking if '+current_plugin+' is enabled', 1)
                ini_value_for_current_plugin = ini.read_single_ini_value('Plugins', current_plugin) # get current value from ini
                ## if plugin is enabled - add plugin commands/trigger to tuple
                if ini_value_for_current_plugin == 'True':
                    tools.debug_output(__name__, 'get_enabled_plugin_trigger', 'Adding commands of '+current_plugin+' to enabled plugin command list', 1)
                    plugin_commands = plugin_commands + eval(current_plugin).TRIGGER # add plugin commands to plugin_commands tuple

        tools.debug_output(__name__, 'get_enabled_plugin_trigger', 'Got '+str(len(plugin_commands))+' enabled plugin commands', 1)

        ## filter out those plugin-commands which dont match the searchstring
        #
        # fnmatch return a list, while apparat is using tuple. Any idea how to improve this section?
        plugin_commands = fnmatch.filter(plugin_commands, '*'+current_search_string+'*') # search for executables matching users searchstring
        plugin_commands = sorted(plugin_commands)

        ## update ui
        self.ui__cb_search.SetItems(plugin_commands) # update combobox

        self.ui__txt_result_counter.SetValue(str(len(plugin_commands))) # update result count

        ## update command
        self.ui__bt_command_img = wx.Image('gfx/core/'+icon_size+'/plugins.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_command.Enable(True)
        self.ui__bt_command.SetBitmap(self.ui__bt_command_img.ConvertToBitmap())
        self.ui__bt_command.SetToolTipString("Plugin-Search") # set tooltip
        self.ui__txt_command.SetValue('') # set command

        ## depending on amount of results
        if(len(plugin_commands) == 0):
            self.status_notification_display_error('Invalid input')

        elif(len(plugin_commands) == 1): # there is only 1 matching plugin commands
            self.status_notification_got_distinct_result()

            if(autocomplete is True): # lets autocomplete
                self.ui__cb_search.SetSelection(0)
                self.parse_user_input(self.ui__cb_search.GetValue().lower()) # to parse the new command and adopt the UI to it

            self.ui__cb_search.SetInsertionPointEnd() # set cursor to end of string

        else: # > 1 plugin command
            self.status_notification_reset() # reset status
            self.ui__txt_plugin_information.SetValue('') # reset plugin information

        tools.debug_output(__name__, 'get_enabled_plugin_trigger', 'found '+str(len(plugin_commands))+' plugin trigger for current user input: '+current_search_string, 1)


    def parse_user_input(self, current_search_string): # pylint:disable=too-many-return-statements, too-many-branches, too-many-statements
        """Takes the current user input and parses it for matching plugins or general application search"""
        tools.debug_output(__name__, 'parse_user_input', 'starting', 1)

        current_search_string = self.ui__cb_search.GetValue().lower()

        if current_search_string != '': # if there is a search string

            ## Search for executables
            if current_search_string[:1] != '!' and current_search_string[:1] != '?':
                self.search_executables(current_search_string)
                return

            else: # Looks like it is a plugin call then

                ## Reset UI partly if search is just !
                if current_search_string == '!':
                    tools.debug_output(__name__, 'parse_user_input', 'Case: !', 1)
                    self.plugin__update_general_ui_information('')

                ## Plugin: Core (can not be disabled)
                if  current_search_string.startswith(plugin_core.TRIGGER):
                    plugin_core.parse(current_search_string, self)
                    return

                ## Plugin: Kill
                cur_ini_value_for_plugin_kill = ini.read_single_ini_value('Plugins', 'plugin_kill') # get current value from ini
                if cur_ini_value_for_plugin_kill == 'True':
                    if current_search_string in plugin_kill.TRIGGER:
                        plugin_kill.parse(self)
                        return

                ## Plugin: Misc
                cur_ini_value_for_plugin_misc = ini.read_single_ini_value('Plugins', 'plugin_misc') # get current value from ini
                if cur_ini_value_for_plugin_misc == 'True':
                    if current_search_string.startswith(plugin_misc.TRIGGER):
                        plugin_misc.parse(current_search_string, self)
                        return

                ## Plugin: Nautilus
                cur_ini_value_for_plugin_nautilus = ini.read_single_ini_value('Plugins', 'plugin_nautilus') # get current value from ini
                if cur_ini_value_for_plugin_nautilus == 'True':
                    if current_search_string in plugin_nautilus.TRIGGER or current_search_string.startswith('!goto'): # goto = special case as it accepts parameter
                        plugin_nautilus.parse(current_search_string, self)
                        return

                ## Plugin: PasswordGen
                cur_ini_value_for_plugin_passwordgen = ini.read_single_ini_value('Plugins', 'plugin_passwordgen') # get current value from ini
                if cur_ini_value_for_plugin_passwordgen == 'True':
                    if current_search_string in plugin_passwordgen.TRIGGER:
                        plugin_passwordgen.parse(current_search_string, self)
                        return

                ## Plugin: Screenshot
                cur_ini_value_for_plugin_screenshot = ini.read_single_ini_value('Plugins', 'plugin_screenshot') # get current value from ini
                if cur_ini_value_for_plugin_screenshot == 'True':
                    if current_search_string in plugin_screenshot.TRIGGER:
                        plugin_screenshot.parse(current_search_string, self)
                        return

                ## Plugin: Internet-Search
                cur_ini_value_for_plugin_internet_search = ini.read_single_ini_value('Plugins', 'plugin_search_internet') # get current value from ini
                if cur_ini_value_for_plugin_internet_search == 'True':
                    if current_search_string[0:3] in plugin_search_internet.TRIGGER:
                        plugin_search_internet.parse(self, current_search_string)
                        return

                ## Plugin: Local Search
                cur_ini_value_for_plugin_local_search = ini.read_single_ini_value('Plugins', 'plugin_search_local') # get current value from ini
                if cur_ini_value_for_plugin_local_search == 'True':
                    if current_search_string.startswith(plugin_search_local.TRIGGER):
                        plugin_search_local.search_user_files(self, current_search_string)
                        return

                ## Plugin: Session
                cur_ini_value_for_plugin_session = ini.read_single_ini_value('Plugins', 'plugin_session') # get current value from ini
                if cur_ini_value_for_plugin_session == 'True':
                    if current_search_string in plugin_session.TRIGGER:
                        plugin_session.parse(current_search_string, self)
                        return

                ## Plugin: Shell
                cur_ini_value_for_plugin_shell = ini.read_single_ini_value('Plugins', 'plugin_shell') # get current value from ini
                if cur_ini_value_for_plugin_shell == 'True':
                    if  current_search_string.startswith(plugin_shell.TRIGGER):
                        plugin_shell.parse(current_search_string, self)
                        return


                ## Most likely a wrong plugin command as nothing matches so far in this case
                tools.debug_output(__name__, 'parse_user_input', 'User input didnt match any plugin trigger', 2)

                ## reset plugin information
                self.ui__txt_plugin_information.SetValue('')

                ## reset status icon as we got no hit
                self.status_notification_reset()

                ## reset result-count
                self.ui__txt_result_counter.SetValue('0')

                ## reset command ui items
                self.ui__bt_command.Enable(False)
                self.ui__txt_command.SetValue('')

                ## reset parameter ui items
                self.ui__bt_parameter.Enable(False)
                self.ui__txt_parameter.SetValue('')

                self.get_enabled_plugin_trigger(current_search_string, autocomplete=True) # collect all enabled plugin-commands for plugin-command-search and filtering

                return

            ## Nothing matched (no plugin and no executable -> display error)
            self.status_notification_display_error('Invalid or incomplete input')
            tools.debug_output(__name__, 'parse_user_input', 'User input didnt match any trigger at all', 2)

        else: ## search string is empty

            if is_resetted is True:
                tools.debug_output(__name__, 'parse_user_input', 'Empty search string and UI is already resetted. Nothing to do.', 1)
            else:
                tools.debug_output(__name__, 'parse_user_input', 'Empty search string, but UI is not yet resetted. Triggering it now.', 1)
                self.reset_ui()


    def search_executables(self, current_search_string):
        """Searches for executables"""
        self.plugin__update_general_ui_information('') # get rid of all plugin UI-artefacts

        tools.debug_output(__name__, 'search_executables', 'Searching executables for the following string: '+current_search_string, 1)
        search_results = fnmatch.filter(os.listdir('/usr/bin'), '*'+current_search_string+'*')     # search for executables matching users searchstring
        search_results = sorted(search_results, key=lambda x: difflib.SequenceMatcher(None, x, current_search_string).ratio(), reverse=True) # better sorting

        self.ui__txt_result_counter.SetValue(str(len(search_results))) # update result count
        self.ui__cb_search.SetItems(search_results) # update combobox

        tools.debug_output(__name__, 'search_executables', 'Found '+str(len(search_results))+' matching application', 1)
        if len(search_results) == 0: # 0 results
            ## update status button
            self.status_notification_display_error('No executables found')

            ## update command button & txt
            self.ui__bt_command.Enable(False)
            self.ui__bt_command_img = wx.Image('gfx/core/'+icon_size+'/blank.png', wx.BITMAP_TYPE_PNG)
            self.ui__bt_command.SetBitmap(self.ui__bt_command_img.ConvertToBitmap())
            self.ui__bt_command.SetToolTipString("") # set tooltip
            self.ui__txt_command.SetValue('') # set command

            ## update parameter button & txt
            self.ui__bt_parameter_img = wx.Image('gfx/core/'+icon_size+'/blank.png', wx.BITMAP_TYPE_PNG)
            self.ui__bt_parameter.SetBitmap(self.ui__bt_parameter_img.ConvertToBitmap())
            self.ui__txt_parameter.SetValue('') # set parameter

        elif len(search_results) == 1: # 1 result
            ## status notification
            self.status_notification_got_distinct_result()

            ## command button & txt
            self.ui__bt_command.Enable(True) # Enable command button
            self.ui__bt_command.SetToolTipString(search_results[0]) # set tooltip
            self.ui__txt_command.SetValue(search_results[0]) # update command txt

            ## colorize command
            self.colorize_txt_command(current_search_string, search_results[0])

            ## parameter button & txt
            self.ui__bt_parameter_img = wx.Image('gfx/core/'+icon_size+'/execute.png', wx.BITMAP_TYPE_PNG)
            self.ui__bt_parameter.SetBitmap(self.ui__bt_parameter_img.ConvertToBitmap()) # change button image
            self.ui__bt_parameter.Enable(True) # Enable parameter button
            self.ui__bt_parameter.SetToolTipString('Launch') # set tooltip
            self.ui__txt_parameter.SetValue('') # update parameter txt

            self.get_icon(str(search_results[0])) ## Icon search

            ## check if application is already running - should offer an option to change to this instance besides starting a new one
            tools.check_running_processes_by_name(search_results[0])

        else: # > 1 results
            self.status_notification_reset() # reset status
            self.get_icon(search_results[0]) # get icon for primary search result

            ## command button & txt
            self.ui__bt_command.SetToolTipString(search_results[0])
            self.ui__txt_command.SetValue(search_results[0])             # assume first search result is the way to go

            ## colorize txt command
            self.colorize_txt_command(current_search_string, search_results[0])

            ## parameter button & txt
            self.ui__bt_parameter_img = wx.Image('gfx/core/'+icon_size+'/execute.png', wx.BITMAP_TYPE_PNG)
            self.ui__bt_parameter.SetBitmap(self.ui__bt_parameter_img.ConvertToBitmap())
            self.ui__bt_parameter.Enable(True) # Enable parameter button
            self.ui__bt_parameter.SetToolTipString('Launch')
            self.ui__txt_parameter.SetValue('')             ## update parameter

            ## check if application is already running - should offer an option to change to this instance besides starting a new one
            tools.check_running_processes_by_name(search_results[0])


    def colorize_txt_command(self, current_search_string, primary_result):
        """Colorize or highlight the current search string (substring) in the currently selected search result/command"""
        highlightStartPos = primary_result.find(current_search_string) # start position
        highlightLength = highlightStartPos + len(current_search_string) # length
        self.ui__txt_command.SetStyle(highlightStartPos, highlightLength, wx.TextAttr(wx.BLACK, wx.Colour(38, 156, 88)))


    def do_execute(self): # pylint:disable=too-many-branches, too-many-statements
        """Launches the actual task"""
        command = self.ui__txt_command.GetValue() ## get command
        parameter = self.ui__txt_parameter.GetValue() ## get parameter

        if(command == ''): # Executing with empty command is non-sense
            tools.debug_output(__name__, 'do_execute', 'Command is empty, nothing to do. Aborting', 3)
            return

        # show plugin information if it is a plugin
        if(self.ui__txt_plugin_information.GetValue() != ''):
            tools.debug_output(__name__, 'do_execute', self.ui__txt_plugin_information.GetValue(), 1)

        # show command and parameter
        tools.debug_output(__name__, 'do_execute', 'starting with command: "'+command+'" and parameter: "'+parameter+'"', 1)

        ## Plugin: Misc
        if self.ui__txt_plugin_information.GetValue() == 'Plugin: Misc (Open)':
            if parameter == '':
                self.status_notification_display_error('No parameter supplied for !open')
                return
            else: # check if parameter-path exists
                tools.debug_output(__name__, 'do_execute', '!open - check if parameter is valid', 1)
                # is parameter a file or folder
                if os.path.isfile(parameter) or os.path.isdir(parameter):
                    tools.debug_output(__name__, 'do_execute', '!open - parameter is valid', 1)
                else:
                    tools.debug_output(__name__, 'do_execute', '!open - parameter is not valid', 3)
                    self.status_notification_display_error('Invalid parameter')
                    return

        ## Plugin: PasswordGen
        if command in plugin_passwordgen.TRIGGER or command == '!pa':
            plugin_passwordgen.execute_password_generation(self)
            return

        ## Plugin: Internet-Search
        if command in plugin_search_internet.TRIGGER:
            plugin_search_internet.execute_internet_search(self, command, parameter)
            return

        ## Plugin: Session/Screenshot/Nautilus/Shell/X/Y OR normal application/executable
        if command is not None: # Check if the dropdown contains something at all or not
            tools.debug_output(__name__, 'do_execute', 'Should execute: "'+command+'" with parameter: "'+parameter+'"', 1)

            ## check if name exists and is executable
            executable_exists = tools.cmd_exists(command)
            if executable_exists is True:
                tools.debug_output(__name__, 'do_execute', 'Executable: "'+command+'" exists', 1)

                ## usage-statistics: commands executed
                tools.debug_output(__name__, 'do_execute', 'Updating statistics (command_executed)', 1)
                current_commands_executed_count = ini.read_single_ini_value('Statistics', 'command_executed')          # get current value from ini
                ini.write_single_ini_value('Statistics', 'command_executed', int(current_commands_executed_count)+1) # update ini +1

                ## usage-statistics: plugin execution count
                if self.ui__txt_plugin_information != '':
                    tools.debug_output(__name__, 'do_execute', 'Updating statistics (plugins_executed)', 1)
                    current_plugin_executed_count = ini.read_single_ini_value('Statistics', 'plugin_executed')          # get current value from ini
                    ini.write_single_ini_value('Statistics', 'plugin_executed', int(current_plugin_executed_count)+1) # update ini +1

                ## Start subprocess
                if parameter == '':
                    subprocess.Popen([command])
                    tools.debug_output(__name__, 'do_execute', 'Executed: "'+command+'"', 1)
                else: # there is at least 1 parameter
                    if(' ' in parameter): # if parameter contains at least 1 space, there are most likely several parameters
                        subprocess.Popen([command+" "+parameter], shell=True) # using shell=True as hack for handling several parameters (i.e. for !fs)
                        tools.debug_output(__name__, 'do_execute', 'Executed: "'+command+'" with parameter: "'+parameter+'" (with shell=True)', 1)
                    else: # assuming: single parameter
                        subprocess.Popen([command, parameter])
                        tools.debug_output(__name__, 'do_execute', 'Executed: "'+command+'" with parameter: "'+parameter+'"', 1)

                self.reset_ui()

                ## Optional: if enabled in ini - hide the Main UI after executing the command
                cur_ini_value_for_hide_ui_after_command_execution = ini.read_single_ini_value('General', 'hide_ui_after_command_execution') # get current value from ini
                if cur_ini_value_for_hide_ui_after_command_execution == 'True':
                    tools.debug_output(__name__, 'do_execute', 'Hide Main UI after executing a command', 1)
                    self.tbicon.execute_tray_icon_left_click()
            else:
                tools.debug_output(__name__, 'do_execute', 'ERROR >> Checking the "'+command+'" executable failed', 3)
                self.status_notification_display_error('Checking the executable failed')
        else:
            tools.debug_output(__name__, 'do_execute', 'WARNING >> command is "None", aborting now', 3)


    def status_notification_display_error(self, error_string):
        """displays an error string and symbol in the status area"""
        tools.debug_output(__name__, 'status_notification_display_error', 'Error: '+error_string, 3)
        self.ui__bt_status.Enable(True)
        self.ui__bt_status.SetToolTipString(error_string)
        self.ui__bt_status_img = wx.Bitmap('gfx/core/16/status_error_red.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_status.SetBitmap(self.ui__bt_status_img)
        self.Refresh()


    def status_notification_reset(self):
        """resets the status notification back to default"""
        tools.debug_output(__name__, 'status_notification_reset', 'Reset notification area back to blank', 1)
        self.ui__bt_status.Enable(False)
        self.ui__bt_status.SetToolTipString('')
        self.ui__bt_status_img = wx.Bitmap('gfx/core/16/blank.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_status.SetBitmap(self.ui__bt_status_img)


    def status_notification_got_distinct_result(self):
        """sets status notification to distinct result -> green color"""
        tools.debug_output(__name__, 'status_notification_got_distinct_result', 'Got 1 distinct result - show green status', 1)
        self.ui__bt_status.Enable(True)
        self.ui__bt_status.SetToolTipString('Valid command')
        self.ui__bt_status_img = wx.Bitmap('gfx/core/16/status_ok_green.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_status.SetBitmap(self.ui__bt_status_img)
        self.Refresh()


    def open_app_url(self):
        """Method to open the application URL  (GitHub project)"""
        tools.debug_output(__name__, 'open_app_url', 'Opening '+constants.APP_URL+' in default browser', 1)
        webbrowser.open(constants.APP_URL+'#top')  # Go to github


    def reset_ui(self):
        """Method to reset the User-Interface of the Apps main-window"""
        tools.debug_output(__name__, 'reset_ui', 'Starting UI reset', 1)

        global icon_size
        icon_size = ini.read_single_ini_value('General', 'icon_size') # update preference value

        global is_resetted
        is_resetted = True

        ## Some general bitmaps which might be needed for some button states
        self.ui__bt_img_search = wx.Bitmap('gfx/core/'+icon_size+'/search.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_img_blank = wx.Bitmap('gfx/core/'+icon_size+'/blank.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_img_execute_black = wx.Bitmap('gfx/core/'+icon_size+'/execute_black.png', wx.BITMAP_TYPE_PNG)
        self.ui__bt_img_appicon = wx.Bitmap('gfx/core/'+icon_size+'/appIcon.png', wx.BITMAP_TYPE_PNG)

        ## reset the combobox
        self.ui__cb_search.Clear() # clear all list values
        self.ui__cb_search.SetValue('') # clear search field
        self.ui__cb_search.SetFocus() # set focus to search

        ## reset command button & txt
        self.ui__bt_command.SetBitmapDisabled(self.ui__bt_img_appicon)
        self.ui__bt_command.Enable(False) # reset primary button by disabling it
        self.ui__bt_command.SetToolTipString("") # set tooltip
        self.ui__txt_command.SetValue('') # reset txt command

        ## reset parameter button & txt
        self.ui__bt_parameter.SetBitmapDisabled(self.ui__bt_img_search)
        self.ui__bt_parameter.Enable(False)
        self.ui__bt_parameter.SetToolTipString('')
        self.ui__txt_parameter.SetValue('') # reset txt parameter

        ## reset other stuff
        self.ui__txt_plugin_information.SetValue('') # reset plugin name field
        self.ui__txt_result_counter.SetValue('0') # reset the result counter
        self.status_notification_reset() # reset the status

        tools.debug_output(__name__, 'reset_ui', 'Finished UI reset', 1)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# INSTANCE CHECK ON INIT
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class App(wx.App):

    """Class App"""

    def __init__(self, *args, **kwargs):
        """Init"""
        self.app_name = constants.APP_NAME+'.lock'
        self.apparat_instance = wx.SingleInstanceChecker(self.app_name)
        wx.App.__init__(self, *args)
        #print kwargs


    def OnInit(self): # pylint:disable=invalid-name
        """While starting the app (checks for already running instances)"""
        if self.apparat_instance.IsAnotherRunning(): # allow only 1 instance of apparat
            tools.debug_output(__name__, 'OnInit', 'An instance is already running. Aborting', 3)
            wx.MessageBox(constants.APP_NAME+' is already running. Aborting startup', 'Error', wx.OK | wx.ICON_WARNING)
            return False
        return True


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# MAIN
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():
    """main"""
    app = App(False)
    tools.check_arguments() # check launch parameter / arguments
    tools.check_platform() # Check if platform is supported at all, otherwise abort
    tools.check_general_requirements() # check if needed linux packages are available/installed
    ini.validate() # validate ini file

    frame = MyFrame(None, constants.APP_NAME) # Main UI window
    tools.debug_output(__name__, 'main', 'Frame: '+str(frame), 1)
    app.MainLoop()

if __name__ == '__main__':
    tools.debug_output(__name__, '__main__', 'starting', 1)
    main()
