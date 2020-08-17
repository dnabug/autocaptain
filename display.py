import nicknames as nicknames
import logs as logs

class Display:
    def __init__(self, gamedata, name_json):
        self.gamedata = gamedata
        self.name_json = name_json

    def team_rating(self, player_list):
        teamrating = 0
        for player in player_list:
            pr = self.gamedata.rating(player, player_list[player])
            print('Player ', nicknames.get_name(self.name_json, player), 'rating:', pr)
            teamrating += pr

        return round(teamrating/len(player_list), 3)

    def player_synopsis(self, player):
        print('Player', nicknames.get_name(self.name_json, player))
        print('===========')

        for role in self.gamedata.get_roles_played(player):
            print(role, 'rating:',
                  self.gamedata.rating(player, role),
                  'winrate:', self.gamedata.get_winrate(player, role),
                  'relative logscore:', self.gamedata.get_rel_avg_logscore(player, role),
                  'games:', self.gamedata.get_games(player, role))

    def list_players(self, players):
        plist = self.gamedata.sort_ratings(players)
        for entry in plist:
            print('Player', nicknames.get_name(self.name_json, entry['player']),
                  'on', entry['role'], ':', entry['rating'])

    def leaderboard(self, role='None'):
        plname = ''
        rlname = ''
        rating = 0
        for player in self.gamedata.get_players():
            if role != 'None':
                if role not in self.gamedata.get_roles_played(player):
                    continue

            for role in self.gamedata.get_roles_played(player):
                r = self.gamedata.rating(player, role)
                if r > rating:
                    rating = r
                    plname = nicknames.get_name(self.name_json, player)
                    rlname = role

        print('Highest rating:', plname, 'with a rating of', rating, 'on', role)

    def pick_dmix_teams(self, players):
        player_list = self.gamedata.sort_ratings(players, True, True)

        blue_roles = ['medic']
        red_roles = ['medic']
        players_picked = []

        # TODO: add weights
        players_max = 10
        picks = 0
        team_picking = blue_roles
        team_name = 'BLUE'
        looking = True

        while picks < 10:
            looking = True
            player_picked = ''

            for pick in player_list:
                if pick['role'] not in team_picking and looking and pick['player'] not in players_picked:
                    looking = False
                    team_picking.append(pick['role'])
                    players_picked.append(pick['player'])
                    print(team_name, 'picks',
                          nicknames.get_name(self.name_json, pick['player']), 'on',
                                             pick['role'])

            if team_picking == blue_roles:
                team_picking = red_roles
                team_name = 'RED'
            else:
                team_picking = blue_roles
                team_name = 'BLUE'
            picks = picks + 1

    def pick_dmix_teams_noroles(self, players):
        player_list = self.gamedata.sort_ratings(players, False)

        players_picked = []
        players_max = 10
        picks = 0

        team_name = 'BLUE'
        looking = True

        while picks < 10:
            looking = True
            player_picked = ''

            for pick in player_list:
                if looking and pick['player'] not in players_picked:
                    looking = False
                    players_picked.append(pick['player'])
                    print(team_name, 'picks',
                          nicknames.get_name(self.name_json, pick['player']))

            if team_name == 'BLUE':
                team_name = 'RED'
            else:
                team_name = 'BLUE'
            picks = picks + 1

