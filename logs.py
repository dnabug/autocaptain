import json
import subprocess
import os
import math

class GameData:

    def __init__(self, logs_txt, batched, update=False):
        self.player_info_table = {}
        self.logscore_table = {
            'pocket_scout': {'value': 0, 'entries': 0, 'value_sqr': 0},
            'flank_scout': {'value': 0, 'entries': 0, 'value_sqr': 0},
            'roamer': {'value': 0, 'entries': 0, 'value_sqr': 0},
            'pocket': {'value': 0, 'entries': 0, 'value_sqr': 0},
            'demoman': {'value': 0, 'entries': 0, 'value_sqr': 0},
            'medic': {'value': 0, 'entries': 0, 'value_sqr': 0}
        }

        if update or not os.path.isfile(batched):
            print('FETCHING ALL LOGS FROM', logs_txt)
            logslist = open(logs_txt, 'r')
            for logfile in logslist:
                log_json = read_log_json(logfile.rstrip())
                self.add_log_data(parse_log(log_json))

            logslist.close()

            batched_data = open(batched, 'w')
            batched_data.write(json.dumps(self.player_info_table))
            batched_data.close()
        else:
            batched_data = open(batched, 'r')
            self.player_info_table = json.loads(batched_data.read())
            batched_data.close()

        self.fill_logscore_table()

    def get_players(self):
        players = []

        for player in self.player_info_table:
            players.append(player)

        return players

    def get_avg_logscore(self, player, role):
        if player not in self.player_info_table:
            return -1

        plobjrole = self.player_info_table[player][role]
        if 'games' not in plobjrole:
            return -1

        if plobjrole['games'] < 1:
            return -1

        return round(plobjrole['raw_log_score'] / plobjrole['games'], 3)

    def get_roles_played(self, player):
        roles = []
        if player not in self.player_info_table:
            return roles
        for role in self.player_info_table[player]:
            plobjrole = self.player_info_table[player][role]
            if 'games' in plobjrole:
                if plobjrole['games'] < 1: continue
                roles.append(role)
        return roles

    def get_games(self, player, role='None'):
        if player not in self.player_info_table:
            return 0

        if role != 'None':
            if 'games' not in self.player_info_table[player][role]: return 0
            return self.player_info_table[player][role]['games']

        total_games = 0
        for role in get_roles_played(self.player_info_table, player):
            total_games += get_games(self.player_info_table, player, role)

        return total_games

    def get_winrate(self, player, role='None'):
        if player not in self.player_info_table:
            return 0.5

        if role != 'None':
            if 'games' not in self.player_info_table[player][role]: return 0.5
            return round(self.player_info_table[player][role]['result'] /
                         self.get_games(player, role), 3)

        total_result = 0
        for role in get_roles_played(player_info_table, player):
            total_result += player_info_table[player][role]['result']

        return round(total_result / get_games(player_info_table, player), 3)

    def fill_logscore_table(self):
        for player in self.player_info_table:
            plobj = self.player_info_table[player]
            for role in self.get_roles_played(player):
                logscore = self.get_avg_logscore(player, role)
                oldval = self.logscore_table[role]['value']
                oldentries = self.logscore_table[role]['entries']
                oldvalsq = self.logscore_table[role]['value_sqr']
                self.logscore_table[role]['value'] = oldval + logscore
                self.logscore_table[role]['value_sqr'] = oldvalsq + math.pow(logscore, 2)
                self.logscore_table[role]['entries'] = oldentries + 1

    def get_rel_avg_logscore(self, player, role):
        ls = self.get_avg_logscore( player, role)
        if ls < 0: return 1
        overall_avg = self.logscore_table[role]['value'] / self.logscore_table[role]['entries']

        return round(ls / overall_avg, 3)

    def get_stddev_rel_logscore(self, role):
        n = self.logscore_table[role]['entries']
        aggr = self.logscore_table[role]['value']
        aggr_sqr = self.logscore_table[role]['value_sqr']
        mu = aggr / n

        return math.sqrt((aggr_sqr - (2 * mu * aggr) + n * math.pow(mu, 2)) / n) / mu

    def rating(self, player, role):
        games = self.get_games(player, role)
        if games < 1: return 1

        ls_weight = 1
        wr_weight = 1 * (1 / (1 + math.exp(0.2 * (17.5 - games))))

        ls = self.get_rel_avg_logscore(player, role)
        wr = self.get_winrate(player, role) / 0.5
        return round((ls_weight * ls + wr_weight * wr) / (ls_weight + wr_weight), 3)

    def avg_rating(self, player):
        roles = ['pocket_scout', 'flank_scout', 'roamer', 'pocket', 'demoman', 'medic']
        num = 0
        den = 0
        for role in roles:
            g = self.get_games(player, role)
            if g < 1: g = 1
            num = num + g * self.rating(player, role)
            den = den + g

        return num / den

    def get_player_ranking_rating(self, player_rating):
        return player_rating.get('rating')

    def sort_ratings(self, players, pick_classes=False, include_all=False):
        picks = []
        for player in players:
            if not pick_classes:
                picks.append({'player': player, 'rating': self.avg_rating(player)})
            elif include_all:
                for role in ['demoman', 'pocket_scout', 'pocket', 'medic', 'roamer', 'flank_scout']:
                    picks.append({'player': player, 'role': role,
                              'rating': self.rating(player, role)
                             })
            else:
                for role in self.get_roles_played(player):
                    picks.append({'player': player, 'role': role,
                              'rating': self.rating(player, role)
                             })

        picks.sort(key=self.get_player_ranking_rating, reverse=True)
        return picks

    def add_log_data(self, log_data):
        teams = ['red', 'blu']

        winning_team = 'none'
        red_score = log_data['red']['score']
        blu_score = log_data['blu']['score']

        if red_score > blu_score:
            winning_team = 'red'
        elif blu_score > red_score:
            winning_team = 'blu'

        for team in teams:
            for player in log_data[team]['players']:
                plobj = {}

                if player not in self.player_info_table:
                    self.player_info_table[player] = {}
                    self.player_info_table[player]['pocket'] = {}
                    self.player_info_table[player]['roamer'] = {}
                    self.player_info_table[player]['medic'] = {}
                    self.player_info_table[player]['flank_scout'] = {}
                    self.player_info_table[player]['pocket_scout'] = {}
                    self.player_info_table[player]['demoman'] = {}

                plobj = self.player_info_table[player]
                role = log_data[team]['players'][player]['role']
                jsobj = plobj[role]

                result = 0
                if team == winning_team: result = 1
                elif red_score == blu_score: result = 0.5

                raw_log_score = log_data[team]['players'][player]['logscore']

                if 'games' in self.player_info_table[player][role]:
                    oldrls = jsobj['raw_log_score']
                    oldres = jsobj['result']
                    oldgms = jsobj['games']
                    jsobj['raw_log_score'] = oldrls + raw_log_score
                    jsobj['result'] = oldres + result
                    jsobj['games'] = oldgms + 1
                else:
                    jsobj['raw_log_score'] = raw_log_score
                    jsobj['result'] = result
                    jsobj['games'] = 1


# Returns the JSON of a logs.tf log
#
# log_id - ID of the log in URL
def read_log_json(log_id):
    arg = 'http://logs.tf/json/' + log_id
    print('Reading log: ', log_id)
    log_json = json.loads(subprocess.check_output(['curl', arg, '-s']).decode("utf-8"))
    return log_json

# Get the class played by a player, returns 'None' if not a normal 6s class
def get_class(player_json):
    tf_class = 'None'
    index = 0

    for class_played in player_json['class_stats']:
        tfc = player_json['class_stats'][index]['type']

        if (tfc == 'soldier' or tfc == 'scout' or tfc == 'medic' or
            tfc == 'demoman'):
            tf_class = tfc
        index = index + 1

    return tf_class

# Calculate log score for player given class
def log_score(log_json, tf_class, player_json, player):
    raw_log_score = 0

    if tf_class == 'medic':
        hpm = player_json['heal'] / log_json['length'] * 60.0
        deaths = player_json['deaths']
        if deaths == 0: deaths = 0.5

        raw_log_score = hpm - 15 * deaths
    else:
        dmg = player_json['dmg']
        dmgtaken = player_json['dt']
        deaths = player_json['deaths']
        totalhealpc = 0
        healers = 0
        for medic in log_json['healspread']:
            medichealjson = log_json['healspread'][medic]
            medicplayerjson = log_json['players'][medic]

            if player in medichealjson:
                healers += 1
                totalhealpc += (medichealjson[player] / medicplayerjson['heal'])
                break

        healpc = totalhealpc / healers
        raw_log_score = (dmg / (dmgtaken + 25 * deaths + 5 * healpc))

    return raw_log_score


def parse_log(log_json):
    log_data = {
        'red': {'score': 0, 'players': {}},
        'blu': {'score': 0, 'players': {}}
    }

    log_data['red']['score'] = log_json['teams']['Red']['score']
    log_data['blu']['score'] = log_json['teams']['Blue']['score']

    for player in log_json['players']:
        pljson = log_json['players'][player]

        tf_class = get_class(pljson)

        if tf_class == 'None':
            continue

        role = ''
        raw_log_score = 0
        medichealjson = {}

        for medic in log_json['healspread']:
            medichealjson = log_json['healspread'][medic]
            if player in medichealjson: break

        raw_log_score = log_score(log_json, tf_class, pljson, player)

        if tf_class == 'soldier':
            for otherplayer in medichealjson:
                if otherplayer == player: continue

                tfc_other = get_class(log_json['players'][otherplayer])

                if tfc_other == 'soldier':
                    if medichealjson[otherplayer] > medichealjson[player]:
                        role = 'roamer'
                    else:
                        role = 'pocket'

            if role == '': role = 'pocket'
        elif tf_class == 'scout':
            for otherplayer in medichealjson:
                if otherplayer == player: continue

                tfc_other = get_class(log_json['players'][otherplayer])

                if tfc_other == 'scout':
                    if medichealjson[otherplayer] > medichealjson[player]:
                        role = 'flank_scout'
                    else:
                        role = 'pocket_scout'

            if role == '':  role = 'pocket_scout'
        else:
            role = tf_class

        if pljson['team'] == 'Red':
            log_data['red']['players'][player] = { 'role': role,
                                                   'logscore': raw_log_score }
        else:
            log_data['blu']['players'][player] = { 'role': role,
                                                  'logscore': raw_log_score }

    return log_data
