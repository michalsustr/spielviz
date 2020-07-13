from typing import List, Callable

import gi.repository.Gtk as Gtk


class CompletingComboBoxText(Gtk.ComboBoxText):
    def __init__(self, static_options: List[str],
          dynamic_condition: Callable[[str], bool],
          dynamic_populator: Callable[[str], List[str]], **kwargs):
        # Set up the ComboBox with the Entry
        Gtk.ComboBoxText.__init__(self, has_entry=True, **kwargs)

        # Store the populator reference in the object
        self.dynamic_condition = dynamic_condition
        self.dynamic_populator = dynamic_populator

        # Create the completion
        completion = Gtk.EntryCompletion(inline_completion=True)

        # Specify that we want to use the first col of the model for completion
        completion.set_text_column(0)
        completion.set_minimum_key_length(2)

        # Set the completion model to the combobox model such that we can
        # also autocomplete these options
        self.static_options_model = self.get_model()
        completion.set_model(self.static_options_model)

        # The child of the combobox is the entry if 'has_entry' was set to True
        entry = self.get_child()
        entry.set_completion(completion)

        # Set the active option of the combobox to 0 (which is an empty field)
        self.set_active(0)

        # Fill the model with the static options (could also be used for a
        # history or something)
        for option in static_options:
            self.append_text(option)

        # Connect a listener to adjust the model when the user types something
        entry.connect("changed", self.update_completion, True)

    def update_completion(self, entry, editable):
        # Get the current content of the entry
        text = entry.get_text()

        # Get the completion which needs to be updated
        completion = entry.get_completion()

        long_enough = len(text) >= completion.get_minimum_key_length()
        if long_enough and self.dynamic_condition(text):
            # Fetch the options from the populator for a given text
            completion_options = self.dynamic_populator(text)

            # Create a temporary model for the completion and fill it
            dynamic_model = Gtk.ListStore.new([str])
            for completion_option in completion_options:
                dynamic_model.append([completion_option])
            completion.set_model(dynamic_model)
        else:
            # Restore the default static options
            completion.set_model(self.static_options_model)
