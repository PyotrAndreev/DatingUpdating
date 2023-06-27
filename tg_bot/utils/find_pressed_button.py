# find pressed button name via iterating over all inline buttons using callback_data (look inline_keyboard)
def find_pressed_button(attr) -> str:
    callback_data = attr.data
    for button_row in attr.message.reply_markup.inline_keyboard:
        for inline_button in button_row:
            if inline_button.callback_data == callback_data:
                pressed_button = inline_button.text  # is pressed_button
                break
    return pressed_button
