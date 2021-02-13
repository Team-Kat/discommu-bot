from os import listdir
from importlib import import_module


def search_files(
    base: str,
    end: str = '.py',
    ignore: list = ['__pycache___']
) -> list:
    files = [
        base + '/' + x
        for x in list(
            filter(
                lambda x: str(x).endswith(str(end)) and str(x) not in ignore,
                listdir(base)
            )
        )
    ]
    folders = list(
        filter(
            lambda x: '.' not in str(x) and str(x) not in ignore,
            listdir(base)
        )
    )
    for f in folders:
        files.extend(search_files(base + '/' + str(f)))
    return files


def gather_commands(
    bot,
    command_dir: str = 'commands',
    ignore: list = ['__pycache__']
) -> list:
    cmds = []
    try:
        files = search_files(command_dir)
    except FileNotFoundError:
        return []
    for f in files:
        name = f.replace('/', '.').replace('.py', '')
        cmd = import_module(name).Command(bot)
        cmd.__cog_name__ = cmd.name
        bot.add_cog(cmd)
    return cmds


def gather_events(
    bot,
    event_dir: str = 'events',
    ignore: list = ['__pycache__']
) -> None:
    files = search_files(event_dir)
    for f in files:
        name = f.replace('/', '.').replace('.py', '')
        ev = import_module(name).Event(bot)
        setattr(
            bot,
            f'on_{name[len(event_dir) + 1:]}',
            ev.trigger
        )
