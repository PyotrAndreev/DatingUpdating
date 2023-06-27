from tg_bot.data_structure import bot
from tg_bot.utils.find_pressed_button import find_pressed_button


async def del_and_log_user_action(attr, not_empty_attr_names: list, event_type: str, update_id: [int, str], users: dict,
                                  from_user_tg) -> None | str:
    tg_data: [str, int] = users[from_user_tg.id]
    # TODO: make write logging, not print
    if event_type == 'callback_query':
        message = attr.message
        message_id = message.message_id

        event_data: str = find_pressed_button(attr)

    elif event_type == 'message':
        message = attr
        message_id = message.message_id

        if 'text' not in not_empty_attr_names:  # if sent something, but not a text
            await bot.delete_message(chat_id=message.chat.id,
                                     message_id=message_id)
            event_type = not_empty_attr_names.pop()  # take the last list value (=event_type)
            # logging user action
            await tg_data.DBUser.log_user_action(update_id=update_id, event_type=event_type, message_id=message_id,
                                                 event_data=None)
            return 'message is deleted'

        event_data = message.text  # sent text

        if 'entities' in not_empty_attr_names:  # entities exist only(?) for bot commands, not for simple text
            event_type = message.entities[0].type

    elif event_type == 'edited_message':
        message = attr
        message_id = message.message_id
        event_data = attr.text

    else:
        await tg_data.DBUser.log_user_action(update_id=update_id, event_type=event_type, message_id=None, event_data=None)
        print('middleware: bot should send something to notify user about something (what have you done?)')
        return None  # if event_type is not in ['message', 'edit_message']

    print(f"{message.date}, update_id: {update_id}, event_type: {event_type}, message_id: {message_id}, "
          f"user_name: {from_user_tg.first_name}, data: {event_data}")

    # logging user action
    await tg_data.DBUser.log_user_action(update_id=update_id, event_type=event_type, message_id=message_id,
                                       event_data=event_data)
