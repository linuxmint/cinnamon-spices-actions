from typing import Iterable

from aui import DialogWindow
from gi.repository import Gtk


class _SelectDropdownDialog(Gtk.Dialog):
    """
    A dialog window with a dropdown menu for selecting options.

    Attributes:
        title (str): The title of the dialog window.
        label (str): The label displayed above the dropdown menu.
        choices (Iterable[str]): The list of choices displayed in the dropdown menu.
        default_choice (str): The default choice selected in the dropdown menu.
        width (int): The width of the dialog window.
        height (int): The height of the dialog window.
        **kwargs: Additional keyword arguments to be passed to the Gtk.Dialog constructor.

    Methods:
        __init__: Initializes the _SelectDropdownDialog with the provided parameters.
    """

    def __init__(
        self,
        title: str = None,
        label: str = None,
        choices: Iterable[str] = None,
        default_choice: str = None,
        width: int = 360,
        height: int = 120,
        **kwargs
    ):
        if choices is None:
            choices = []
        super().__init__(title=title, **kwargs)
        self.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK,
        )

        self._box = Gtk.VBox(spacing=0)

        if label is not None:
            self._label = Gtk.Label(xalign=0)
            self._label.set_markup(label)
            self._box.pack_start(self._label, False, False, 10)

        self._dropdown = Gtk.ComboBoxText()
        self._dropdown.set_margin_bottom(5)
        self._dropdown.set_margin_start(5)
        self._dropdown.set_margin_end(5)

        for choice in choices:
            self._dropdown.append_text(choice)

        # TODO: fix default choice
        if default_choice is not None:
            self._dropdown.set_active_id(default_choice)

        self._box.pack_start(self._dropdown, True, True, 0)

        self._content_area = self.get_content_area()
        self._content_area.add(self._box)
        self.set_default_size(width, height)
        self.show_all()


class SelectDropdownDialogWindow(DialogWindow):
    """
    A dialog window that extends the functionality of DialogWindow by adding a dropdown menu for selecting options.

    Attributes:
        title (str): The title of the dialog window.
        label (str): The label displayed above the dropdown menu.
        choices (Iterable[str]): The list of choices displayed in the dropdown menu.
        default_choice (str): The default choice selected in the dropdown menu.
        window_icon_path (str): The path to the icon for the dialog window.
        width (int): The width of the dialog window.
        height (int): The height of the dialog window.

    Methods:
        __init__: Initializes the SelectDropdownDialogWindow with the provided parameters.
        run: Runs the dialog window and returns the selected option if 'OK' is clicked.
        get_selected: Returns the currently selected option in the dropdown menu.
    """

    def __init__(
        self,
        title: str = None,
        label: str = None,
        choices: Iterable[str] = None,
        default_choice: str = None,
        window_icon_path: str = None,
        width: int = 360,
        height: int = 120,
    ) -> None:
        if choices is None:
            choices = []
        super().__init__(title=title, icon_path=window_icon_path)
        self.dialog = _SelectDropdownDialog(
            flags=0,
            transient_for=self,
            title=title,
            label=label,
            choices=choices,
            default_choice=default_choice,
            width=width,
            height=height,
        )

    def run(self) -> str | None:
        response = super().run()
        if response == Gtk.ResponseType.OK:
            return self.dialog._dropdown.get_active_text()
        return None

    def get_selected(self) -> str | None:
        return self.dialog._dropdown.get_active_text()
