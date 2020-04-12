from kivy import Config
from kivy.utils import platform
from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.behaviors import RectangularElevationBehavior
from kivymd.theming import ThemableBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.list import ILeftBodyTouch, IRightBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.picker import MDThemePicker
from kivymd.uix.list import ThreeLineRightIconListItem
from kivymd.uix.list import OneLineRightIconListItem
from kivymd.uix.picker import MDDatePicker
from kivymd.uix.label import MDLabel
from kivymd.toast.kivytoast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivy.properties import BooleanProperty, StringProperty, ListProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from functools import partial
from datetime import datetime
from plyer import filechooser
import sqlite3
import shutil
import os
import re
from damper import Damper

# Turn on android keyboard
# Config.set("kivy", "keyboard_mode", "system")
Config.set("kivy", "keyboard_mode", "systemanddock")
# The current target TextInput widget requesting the keyboard
# is presented just above the soft keyboard.
Window.softinput_mode = "below_target"


class Container(BoxLayout):  # root widget
    pass


class MyToolbar(ThemableBehavior,
                RectangularElevationBehavior,
                MDBoxLayout):
    # Property for each toolbar could change its own title.
    toolbar_title = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = self.theme_cls.primary_color


class ChooseDate(ButtonBehavior, MDLabel):
    pass


class MyRightCheckbox(IRightBodyTouch, MDCheckbox):
    pass


class MyLeftIcon(ILeftBodyTouch, MDIconButton):
    pass


class DamperListItem(ThreeLineRightIconListItem):
    pass


class TypeListItem(OneLineRightIconListItem):
    pass


class HomeScreen(Screen):
    pass


class AddTypeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def add_type(self, d_type):
        """Add d_type into DB."""
        if not d_type:  # if empty string.
            toast("Fill the field")
        else:
            damper = Damper()
            try:
                is_exists = damper.is_the_d_type_exists(d_type)
            except sqlite3.DatabaseError:
                toast("IsTypeExistsError")
            else:
                if is_exists:
                    toast("{} already exists".format(d_type))
                else:
                    try:
                        damper.add_type(d_type)
                    except sqlite3.DatabaseError:
                        toast("AddTypeError")
                    else:
                        toast("Added new type: {}".format(d_type))


class EditTypeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.old_type = ""

    def on_enter(self):
        self.old_type = self.tf_type.text

    def edit_type(self, new_type):
        if self.old_type == new_type:
            toast("Nothing to change")
        elif not new_type:  # if empty string.
            toast("Fill the field")
        else:
            damper = Damper()
            try:
                is_exists = damper.is_the_d_type_exists(new_type)
            except sqlite3.DatabaseError:
                toast("IsTypeExistsError")
            else:
                if is_exists:
                    toast("{} already exists".format(new_type))
                else:
                    try:
                        damper.edit_type(self.old_type, new_type)
                    except sqlite3.DatabaseError:
                        toast("EditTypeError")
                    else:
                        toast("Edited")


class DeleteEditTypeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.toolbar_menu_items = []
        self.selected_types = []  # Every TypeListItem selected by MyRightCheckbox add to this list.
        self.all_types_in_container = []  # Consists of all adding TypeListItem.
        self.d_types = []  # All d_types from the DB.
        self.menu_dots = None
        self.menu_items_dots = [
            {"text": "Select all",
             "icon": "select-all"},

            {"text": "Cancel all selection",
             "icon": "select-off"},

            {"text": "Edit selected type",
             "icon": "square-edit-outline"},

            {"text": "Delete selected types",
             "icon": "delete-outline"}
        ]
        # Dict to process callback_menu_dots.
        self.dict_menu_dots_funcs = {
            "Select all": self.select_all,
            "Cancel all selection": self.cancel_all_selection,
            "Edit selected type": self.edit_selected_type,
            "Delete selected types": self.show_deleting_dialog,
        }

    def callback_menu_dots(self, instance):
        """
        Check what item in the menu_dots pressed and
        do the action according pressed menu item.
        Actions are in the self.dict_menu_dots_funcs.
        """
        self.dict_menu_dots_funcs.get(instance.text)()

    def on_enter(self):
        """Read DB and output data into types_container."""

        # Creating DeleteEditTypeToolbar dots menus.
        self.menu_dots = MDDropdownMenu(
            caller=self.ids["tb_deleteedittype"].ids["ibtn_dots"],
            items=self.menu_items_dots,
            callback=self.callback_menu_dots,
            # position="auto",
            width_mult=5
        )
        damper = Damper()
        try:
            self.d_types = damper.get_types()
        except sqlite3.DatabaseError:
            toast("GetTypesError")
        else:  # Read DB and output data into dampers_container.
            if not self.d_types:
                toast("No Types in the DB")
            else:
                for d_type in self.d_types:
                    a_type_list_item = TypeListItem(text=d_type)
                    self.ids["types_container"].add_widget(a_type_list_item)
                    # Add all adding TypeListItem to the list for
                    # getting access to right_checkbox_types in the future.
                    self.all_types_in_container.append(a_type_list_item)

    def on_leave(self):
        """
        Call clear_screen to avoid duplicate
        when screen will be called next time.
        """
        self.clear_screen()
        self.d_types.clear()
        self.selected_types.clear()

    def clear_screen(self):
        """
        Clear screen: deletes all TypeListItems from MDList.
        """
        if self.all_types_in_container:
            for item in self.all_types_in_container:
                self.types_container.remove_widget(item)

    def show_deleting_dialog(self, *args):
        """Show delete type dialog."""
        if self.selected_types:
            dialog = MDDialog(
                title="Delete damper type",
                size_hint=(.7, .4),
                text_button_ok="Delete",
                text_button_cancel="Cancel",
                auto_dismiss=False,
                events_callback=self.delete_selected_types,
                text="This action will delete selected types"
                     "\nand all records in the dampers"
                     "\nwhere these types are from the Database."
                     "\nDo you really want to do this?"
            )

            dialog.open()

    def delete_selected_types(self, text_of_selection, *args):
        """
        Delete selected d_types
        from DB and types_container.
        """
        if text_of_selection == "Delete":
            # if self.selected_types:
            for d_type in self.selected_types:
                damper = Damper()
                try:
                    damper.delete_type(d_type.text)
                except sqlite3.DatabaseError:
                    toast("DeleteTypeError")
                else:
                    self.types_container.remove_widget(d_type)
                    self.d_types.remove(d_type.text)
                    toast("Deleted")
            # After all deleting clear self.selected_types.
            self.selected_types.clear()

    def edit_selected_type(self, *args):
        """Edit selected type."""
        if self.selected_types:  # if self.selected_types is not empty.
            if len(self.selected_types) > 1:
                toast("Select one for editing")
            else:
                MDApp.get_running_app().root.ids["edit_type_screen"].ids["tf_type"].text = self.selected_types[0].text
                MDApp.get_running_app().screen_manager.current = "edit_type_screen"

    def select_all(self, *args):
        """Select all elements."""
        for type_list_item in self.all_types_in_container:
            type_list_item.ids["right_checkbox_types"].active = True

    def cancel_all_selection(self, *args):
        """Cancel selection of all elements."""
        for type_list_item in self.all_types_in_container:
            type_list_item.ids["right_checkbox_types"].active = False

    def add_into_selected_types(self, instance):
        """Add selected item into the list: selected_types."""
        self.selected_types.append(instance)

    def del_from_selected_types(self, instance):
        """Delete selected item from the list: selected_types."""
        self.selected_types.remove(instance)


class AddDamperScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.d_types = []
        # MDDropdownMenu
        self.menu = None

    def on_enter(self):
        """Get damper types and put them into self.d_types."""
        damper = Damper()
        try:
            self.d_types = damper.get_types()
        except sqlite3.DatabaseError:
            toast("GetTypesError")
        else:  # Read DB and output data into dampers_container.
            if not self.d_types:
                toast("No Types in the DB")
            else:
                menu_items = [{"text": d_type} for d_type in self.d_types]
                self.menu = MDDropdownMenu(
                    caller=self.ids["dditm_type"],
                    items=menu_items,
                    position="center",
                    width_mult=4,
                    callback=self.set_item
                )
                self.ids["dditm_type"].text = self.d_types[0]
                # self.dditm_type.items = self.types

    def set_item(self, instance):
        """Set chosen item text in the MDDropdownMenu."""
        self.ids["dditm_type"].set_item(instance.text)

    def add_damper(self, number, d_type, check_date, location, is_released=False, notes=""):
        """Add new damper into the MDList and DB."""
        # Delete [u][/u] from the check_date.
        check_date_regex = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{1,2}")
        mo = check_date_regex.search(check_date)
        if mo is not None:
            check_date = mo.group()

        if not self.d_types:
            toast("First add damper types into the DB")
        else:
            if not number or not location:
                toast("Fill all needed fields")
            else:
                damper = Damper()
                try:
                    is_exists = damper.is_the_number_exists(number)
                except sqlite3.DatabaseError:
                    toast("IsNumberExistsError")
                else:
                    if is_exists:
                        toast("{} already exists".format(number))
                    else:
                        try:
                            is_exists = damper.is_the_location_exists(location)
                        except sqlite3.DatabaseError:
                            toast("IsLocationExistsError")
                        else:
                            if is_exists:
                                toast("{} already exists".format(location))
                            else:
                                try:
                                    damper.add_damper(number, d_type, check_date, location, is_released, notes)
                                except sqlite3.DatabaseError:
                                    toast("AddDamperError")
                                else:
                                    toast("Added new damper: {}".format(number))

    def show_datepicker(self, *args):
        picker = MDDatePicker(callback=self.got_date)
        picker.open()

    def got_date(self, the_date):
        """
        Get the date from the datepicker
        and output it into lbl_choose_date
        """
        date = "{}-{}-{}".format(the_date.year, str(the_date.month).zfill(2), str(the_date.day).zfill(2))
        self.lbl_choose_date.text = "[u]{}[/u]".format(date)


class EditDamperScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.d_types = []
        # Fill these fields when app.edit_selected_damper (MainApp) called.
        self.old_number = ""
        self.old_d_type = ""
        self.old_check_date = ""
        self.old_location = ""
        self.old_is_released = False
        self.old_notes = ""
        # MDDropdownMenu
        self.menu = None

        self.is_the_number_exists = False
        self.is_the_location_exists = False

    def on_enter(self):
        """
        Put parsed damper info into the EditDamperScreen fields.
        """
        damper = Damper()
        try:
            self.d_types = damper.get_types()
        except sqlite3.DatabaseError:
            toast("GetTypesError")
        else:  # Read DB and output data into dampers_container.
            if not self.d_types:
                toast("No Types in the DB")
            else:
                menu_items = [{"text": d_type} for d_type in self.d_types]
                self.menu = MDDropdownMenu(
                    caller=self.ids["dditm_type"],
                    items=menu_items,
                    position="center",
                    width_mult=4,
                    callback=self.set_item
                )
                self.tf_number.text = self.old_number
                # To show correct current_item in the MDDropDownItem (dditm_type).
                self.dditm_type.current_item = self.old_d_type
                self.dditm_type.ids["label_item"].text = self.old_d_type

                self.lbl_choose_date.text = "[u]{}[/u]".format(self.old_check_date)
                self.tf_location.text = self.old_location
                self.chbx_isreleased.active = self.old_is_released
                self.tf_notes.text = self.old_notes

    def set_item(self, instance):
        """Set chosen item text in the MDDropdownMenu."""
        self.ids["dditm_type"].set_item(instance.text)

    def edit_damper(self, new_number, new_d_type, new_check_date, new_location, new_is_released=False, new_notes=""):
        """Edit the damper."""
        # Delete [u][/u] from the check_date.
        check_date_regex = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{1,2}")
        mo = check_date_regex.search(new_check_date)
        if mo is not None:
            new_check_date = mo.group()

        self.is_the_number_exists = False
        self.is_the_location_exists = False
        if not self.d_types:  # TODO: delete if doesn't need.
            toast("First add damper types into the DB")
        else:
            if not new_number or not new_location:
                toast("Fill all needed fields")
            else:
                damper = Damper()
                if new_number != self.old_number:  # if equal (the same damper) can be updated!
                    try:
                        self.is_the_number_exists = damper.is_the_number_exists(new_number)
                    except sqlite3.DatabaseError:
                        toast("IsNumberExistsError")
                    else:
                        if self.is_the_number_exists:
                            toast("{} already exists".format(new_number))
                # To avoid itersetion of toasts already exists for number and location
                # added (and not self.is_the_number_exists).
                if new_location != self.old_location and not self.is_the_number_exists:  # if equal (the same damper) can be updated!
                    try:
                        self.is_the_location_exists = damper.is_the_location_exists(new_location)
                    except sqlite3.DatabaseError:
                        toast("IsLocationExistsError")
                    else:
                        if self.is_the_location_exists:
                            toast("{} already exists".format(new_location))

                if not self.is_the_number_exists and not self.is_the_location_exists:
                    try:
                        damper.edit_damper(self.old_number, new_number, new_d_type,
                                           new_check_date, new_location, new_is_released, new_notes)
                    except sqlite3.DatabaseError:
                        toast("EditDamperError")
                    else:
                        toast("Edited")

    def show_datepicker(self, *args):
        picker = MDDatePicker(callback=self.got_date)
        picker.open()

    def got_date(self, the_date):
        """
        Get the date from the datepicker
        and output it into lbl_choose_date
        """
        date = "{}-{}-{}".format(the_date.year, str(the_date.month).zfill(2), str(the_date.day).zfill(2))
        self.lbl_choose_date.text = "[u]{}[/u]".format(date)


class MainApp(MDApp):
    title = "Dampers"
    # For showing/hiding search widget.
    is_search_focused = BooleanProperty(False)
    is_first_started = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_dampers = []  # Every damper selected by MyRightCheckbox add to this list.
        self.all_dampers_in_container = []  # Consists of all adding DamperListItem.
        self.damper = None
        self.dampers = []  # Has all getting dampers (class Damper) from the DB.
        self.found_dampers = []  # Has all found in searching dampers.
        self.menu_sort = None
        self.menu_dots = None

        self.menu_items_dots = [
            {"text": "Select all",
             "icon": "select-all"},

            {"text": "Cancel all selection",
             "icon": "select-off"},

            {"text": "Add type",
             "icon": "plus"},

            {"text": "Delete/Edit type",
             "icon": "delete-outline"},

            {"text": "Add damper",
             "icon": "plus"},

            {"text": "Edit selected damper",
             "icon": "square-edit-outline"},

            {"text": "Delete selected dampers",
             "icon": "delete-outline"},

            {"text": "Backup Database",
             "icon": "content-save-outline"},

            {"text": "Restore Database",
             "icon": "backup-restore"},

            {"text": "Clear DB",
             "icon": "delete-forever-outline"},

            {"text": "Change theme",
             "icon": "theme-light-dark"},

            {"text": "Exit",
             "icon": "exit-to-app"}
        ]
        # Dict to process callback_menu_dots.
        self.dict_menu_dots_funcs = {
            "Select all": self.select_all,
            "Cancel all selection": self.cancel_all_selection,
            "Add type": partial(self.change_screen, "add_type_screen"),
            "Delete/Edit type": partial(self.change_screen, "delete_edit_type_screen"),
            "Add damper": partial(self.change_screen, "add_damper_screen"),
            "Edit selected damper": self.edit_selected_damper,
            "Delete selected dampers": self.show_delete_dampers_dialog,
            "Backup Database": self.choose,
            "Restore Database": partial(self.choose, False),
            "Clear DB": self.show_clear_db_dialog,
            "Change theme": self.show_themepicker,
            "Exit": self.stop
        }

        self.menu_items_sort = [
            {"text": "Sort by 'number'",
             "icon": "sort-numeric"},

            {"text": "Sort by 'location'",
             "icon": "format-columns"},

            {"text": "Sort by 'check date'",
             "icon": "calendar-month"},

            {"text": "Sort by 'is released'",
             "icon": "check-outline"},

            {"text": "Sort by 'no order'",
             "icon": "sort-variant-remove"}
        ]
        # Dict to process callback_menu_sort.
        self.dict_menu_sort_funcs = {
            "Sort by 'number'": partial(self.get_dampers, "by number"),
            "Sort by 'location'": partial(self.get_dampers, "by location"),
            "Sort by 'check date'": partial(self.get_dampers, "by check date"),
            "Sort by 'is released'": partial(self.get_dampers, "by is released"),
            "Sort by 'no order'": self.get_dampers
        }

    def build(self):
        self.theme_cls.primary_palette = "Teal"

        return Container()

    def on_start(self):
        if platform == "android":
            # Runtime permissions.
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE,
                                 Permission.READ_EXTERNAL_STORAGE])

        self.screen_manager = self.root.ids["screen_manager"]
        self.home_screen = self.root.ids["home_screen"]
        self.dampers_container = self.home_screen.ids["dampers_container"]
        self.tf_search = self.home_screen.ids["tf_search"]
        self.container = self.home_screen.ids["container"]
        # For passing old_damper info into the EditDamperScreen.
        self.edit_damper_screen = self.root.ids["edit_damper_screen"]
        # Creating MyToolbar dots and sort menus.
        self.menu_dots = MDDropdownMenu(
            caller=self.home_screen.ids["tb_home"].ids["ibtn_dots"],
            items=self.menu_items_dots,
            callback=self.callback_menu_dots,
            # position="auto",
            width_mult=5
        )
        self.menu_sort = MDDropdownMenu(
            caller=self.home_screen.ids["tb_home"].ids["ibtn_sort"],
            items=self.menu_items_sort,
            callback=self.callback_menu_sort,
            # position="bottom",
            width_mult=5
        )
        self.get_dampers()
        self.is_first_started = False

    def callback_menu_sort(self, instance):
        """
        Check what item in the menu_sort pressed and
        do the action according pressed menu item.
        Actions are in the self.dict_menu_sort.
        """
        self.dict_menu_sort_funcs.get(instance.text)()

    def callback_menu_dots(self, instance):
        """
        Check what item in the menu_dots pressed and
        do the action according pressed menu item.
        Actions are in the self.dict_menu_dots.
        """
        self.dict_menu_dots_funcs.get(instance.text)()

    def get_dampers(self, order="no order", *args):
        """
        Get all dampers from the DB and store them into self.dampers.
        :param order: str for sorting can be:
                                    "by number", "by location",
                                    "by check date", by is released",
                                    "no order"
        """
        self.damper = Damper()
        try:
            self.dampers = self.damper.get_dampers(order)
        except sqlite3.DatabaseError:
            toast("Can't get dampers from the DB")
        else:
            # Not to show_dampers in the first start
            # because it'll be done in change_screen.
            if not self.is_first_started:
                self.show_dampers()

    def show_dampers(self, is_search=False, *args):
        """
        Get all dampers from the DB and show them.
        :param args: for Clock.schedule_once(self.set_field_focus, 1) in self.clear_db
        :param is_search: if True show only found dampers in self.found_dampers.
        """
        # Hide search if not search.
        if not is_search:
            self.hide_search()

        if self.all_dampers_in_container:
            for damper in self.all_dampers_in_container:
                self.dampers_container.remove_widget(damper)

        # Clear all selections.
        self.selected_dampers.clear()
        self.all_dampers_in_container.clear()

        # If search show only found dampers in self.found_dampers.
        dampers = self.found_dampers if is_search else self.dampers
        if self.dampers:
            for self.damper in dampers:
                # Format for output damper data.
                released = "Released" if self.damper.is_released else "Not released"
                text = "{}        {}".format(self.damper.number, self.damper.location)
                secondary_text = "{}       {}".format(self.damper.check_date, released)
                tertiary_text = "{}          {}".format(self.damper.d_type, self.damper.notes)

                a_damper_list_item = DamperListItem(
                                        text=text,
                                        secondary_text=secondary_text,
                                        tertiary_text=tertiary_text
                                        )
                self.dampers_container.add_widget(a_damper_list_item)
                # Add all adding DamperListItem to the list for
                # getting access to right_checkbox_dampers in the future.
                self.all_dampers_in_container.append(a_damper_list_item)
        else:
            # Clock.schedule_once(lambda x: (toast("No dampers in the DB")), 4)
            toast("No dampers in the DB")

    def show_search(self, *args):
        """Show search."""
        self.tf_search.focused = True
        self.is_search_focused = True
        # Slide tf_search top down from .96 to .9
        anim_search = Animation(top_hint_search=.9)
        anim_search.start(self.tf_search)

        # Slide container(GridLayout) top down from .9 to .84
        anim_container = Animation(top_hint_container=.84)
        anim_container.start(self.container)

    def hide_search(self, *args):
        """Hide search."""
        self.is_search_focused = False
        # Clear tf_search when hiding.
        self.tf_search.text = ""
        # Slide tf_search top up from .9 to .96
        anim_search = Animation(top_hint_search=.96)
        anim_search.start(self.tf_search)

        # Slide container(GridLayout) top up from .84 to .9
        anim_container = Animation(top_hint_container=.9)
        anim_container.start(self.container)

    def search_text_changed(self, finding_text):
        """
        Search dampers by finding_text,
        add filtered dampers to the self.found_dampers
        and output them in self.show_dampers.
        :param finding_text:
        """
        self.found_dampers = []
        for self.damper in self.dampers:
            if (finding_text in self.damper.number or
                    finding_text in self.damper.location or
                    finding_text in self.damper.check_date):
                self.found_dampers.append(self.damper)
        self.show_dampers(is_search=True)

    def choose(self, is_backup=True, *args):
        """
        Call plyer filechooser API to run a filechooser Activity.
        """
        from android.permissions import request_permissions, Permission, check_permission
        # Check if the permissions still granted.
        if not check_permission(Permission.WRITE_EXTERNAL_STORAGE):
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
        else:
            filechooser.open_file(on_selection=self.backup_db if is_backup else self.restore_db)

    def backup_db(self, selection):
        """Backup Database."""
        # chosen_dir = filechooser.choose_dir(title="Choose directory")  # Doesn't work on Android (why?).
        chosen_dirname = os.path.dirname(selection[0])
        now = datetime.now()
        now_datetime = (
            "{}-{}-{}_{}-{}-{}".format(
                now.year,
                str(now.month).zfill(2),
                str(now.day).zfill(2),
                str(now.hour).zfill(2),
                str(now.minute).zfill(2),
                str(now.second).zfill(2)
            )
        )
        # dirname = os.path.dirname(__file__)  # doesn't work on Android.
        dirname = os.getcwd()
        src_db_path = "{}{}dampers.db".format(dirname, os.sep)
        dst_filename = "{}{}{}_{}".format(chosen_dirname, os.sep, now_datetime, "dampers.db")
        try:
            shutil.copyfile(src_db_path, dst_filename)
        except OSError as err:
            toast(str(err))
            # toast("SaveBackupError")
        else:
            toast("Backup file saved")

    def restore_db(self, selection):
        """Restore Database."""
        # dst_db_path = os.path.dirname(__file__)   # doesn't work on Android.
        dst_db_path = os.getcwd()
        try:
            shutil.copyfile(selection[0], "{}{}{}".format(dst_db_path, os.sep, "dampers.db"))
        except OSError as err:
            toast(str(err))
            # toast("RestoreBackupError")
        else:
            toast("Backup file restored")
            # Get and show dampers after restoring.
            self.get_dampers()

    def show_themepicker(self, *args):
        picker = MDThemePicker()
        picker.open()

    def change_screen(self, screen_name, *args):
        if screen_name == "home_screen":
            self.tf_search.focused = False
            self.tf_search.text = ""
            self.get_dampers()

        self.screen_manager.current = screen_name

    def show_delete_dampers_dialog(self, *args):
        """Show delete damper dialog."""
        if self.selected_dampers:
            dialog = MDDialog(
                title="Delete damper",
                size_hint=(.7, .4),
                text_button_ok="Delete",
                text_button_cancel="Cancel",
                auto_dismiss=False,
                events_callback=self.delete_selected_dampers,
                text="This action will delete selected dampers"
                     "\nfrom the Database."
                     "\nDo you really want to do this?"
            )

            dialog.open()

    def delete_selected_dampers(self, text_of_selection, *args):
        """
        Delete selected items
        from DB and _item_container.
        """
        if text_of_selection == "Delete":
            # if self.selected_dampers:
            for selected_damper in self.selected_dampers:
                # Get the damper the_number.
                damper_number = selected_damper.text.split()[0]
                damper = Damper()
                try:
                    damper.delete_damper(damper_number)
                except sqlite3.DatabaseError:
                    toast("DeleteDamperError")
                else:
                    self.dampers_container.remove_widget(selected_damper)
            toast("Deleted")

    def edit_selected_damper(self, *args):
        """Edit selected damper."""
        if self.selected_dampers:  # if self.selected_dampers is not empty.
            if len(self.selected_dampers) > 1:
                toast("Select one for editing")
            else:
                number_location = self.selected_dampers[0].text.split()
                checkdate_isreleased = self.selected_dampers[0].secondary_text.split()
                dtype_notes = self.selected_dampers[0].tertiary_text.split()

                self.edit_damper_screen.old_number = number_location[0]
                self.edit_damper_screen.old_location = number_location[1]
                self.edit_damper_screen.old_check_date = checkdate_isreleased[0]
                self.edit_damper_screen.old_is_released = True if checkdate_isreleased[1] == "Released" else False
                self.edit_damper_screen.old_d_type = dtype_notes[0]
                self.edit_damper_screen.old_notes = dtype_notes[1] if len(dtype_notes) == 2 else ""

                self.change_screen("edit_damper_screen")

    def show_clear_db_dialog(self, *args):
        """Show clear DB dialog."""
        dialog = MDDialog(
            title="Clear Database",
            size_hint=(.7, .4),
            text_button_ok="Clear",
            text_button_cancel="Cancel",
            auto_dismiss=False,
            events_callback=self.clear_db,
            text="[color={}]This action will delete "
                 "\n[b]ALL[/b] data from the Database."
                 "\nDo you really want to do this?[/color]".format("#FF0000"))

        dialog.open()

    def clear_db(self, text_of_selection, *args):
        """Delete ALL date from the DB."""
        if text_of_selection == "Clear":
            damper = Damper()
            try:
                damper.clear_db()
            except sqlite3.DatabaseError:
                toast("ClearDBError")
            else:
                toast("Cleared")
                # Delay for showing toast("Cleared")
                Clock.schedule_once(self.show_dampers, 1)

    def select_all(self, *args):
        """Select all elements."""
        for damper_list_item in self.all_dampers_in_container:
            damper_list_item.ids["right_checkbox_dampers"].active = True

    def cancel_all_selection(self, *args):
        """Cancel selection of all elements."""
        for damper_list_item in self.all_dampers_in_container:
            damper_list_item.ids["right_checkbox_dampers"].active = False

    def add_into_selected_dampers(self, instance):
        """Add selected item into the list: selected_dampers."""
        self.selected_dampers.append(instance)

    def del_from_selected_dampers(self, instance):
        """Delete selected item from the list: selected_dampers."""
        self.selected_dampers.remove(instance)


MainApp().run()
