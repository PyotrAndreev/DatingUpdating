numeric_system_level = dict(root_admin=30, admin=25, assistant_admin=20, client=15, speaker=10, user=5)


defined_users: dict[int: str] = {266152771: 'root_admin'}  # Anna I.


def define_status(tg_id: [int, str]) -> str:
    user_status: str = defined_users.get(int(tg_id), 'user')
    return user_status


if __name__ == '__main__':
    print([name for name, num_level in numeric_system_level.items()
                                if 'admin' in name and num_level <= 25])