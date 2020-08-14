import json
import subprocess
import sys
import nicknames as nicknames
import logs as logs
import os
import display as display

def main():
    name_json = nicknames.load_names('players.json')

    updated = False
    for arg in sys.argv[1:]:
        if arg == 'update':
            updated = True

    gamedata = logs.GameData('logs.txt', 'batched.json', updated)
    disp = display.Display(gamedata, name_json)

    disp.player_synopsis(nicknames.get_steamid(name_json, 'eqstaz'))

    player_pool = [
        nicknames.get_steamid(name_json, 'Monkey'),
        nicknames.get_steamid(name_json, 'Mike Doe'),
        nicknames.get_steamid(name_json, 'gatsan'),
        nicknames.get_steamid(name_json, 'zambz'),
        nicknames.get_steamid(name_json, 'Harrow'),
        nicknames.get_steamid(name_json, 'ross'),
        nicknames.get_steamid(name_json, 'eqstaz'),
        nicknames.get_steamid(name_json, 'pesky'),
        nicknames.get_steamid(name_json, 'baron'),
        nicknames.get_steamid(name_json, 'anonimo')
    ]

    disp.pick_dmix_teams(player_pool)

if __name__ == "__main__":
    main()
