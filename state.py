import math
import copy
import random
import yaml
from flask_socketio import SocketIO, emit
from flask import Flask, render_template

app = Flask(__name__)
with open("config.yml") as f:
    config = yaml.load(f)
    app.config['SECRET_KEY'] = config["secret"]

sio = SocketIO(app)
game = None
joined_players = []

bad_roles = ["assassin", "mordred", "morgana", "badguy"]
good_roles = ["merlin", "percival", "goodguy", "goodguy", "goodguy", "goodguy"]

quests = {
    5:  [2, 3, 2, 3, 3],
    6:  [2, 3, 4, 3, 4],
    7:  [2, 3, 3, 4, 4],
    8:  [3, 4, 4, 5, 5],
    9:  [3, 4, 4, 5, 5],
    10: [3, 4, 4, 5, 5]
}

def dict_get_multi(d, keys):
    result = []
    for i in keys:
        if i in d:
            result.append(d[i])
    return result

def get_roles(n_players):
    n_bad = math.ceil(n_players / 3)
    n_good = n_players - n_bad
    return bad_roles[:n_bad] + good_roles[:n_good]

class AvalonGame:
    def __init__(self, players):
        self.players = copy.copy(players)
        self.roles = {}
        self.player_roles = {}
        self.teams = {"bad": [], "good": []}
        self.role_texts = {}
        self.state = "no_game"
        self.quest = -1
        self.current_quest_leader = 0
        self.questers = []
        self.questers_voted = []
        self.history = []
        self.votes = {}
        self.quest_fail_votes = 0
        self.successes = 0
        self.failures = 0

    def get_role_text(self, player):
        role = self.player_roles[player]
        team = "good" if role in good_roles else "bad"
        article = "a" if role.endswith("guy") else "the"
        yourrole_text = "You are {} {} ({}).".format(article, role.title(), team)
        extra_text = "You have no special information."
        if role in ["assassin", "mordred", "morgana", "merlin"]:
            extra_text = "The bad team is: {}.".format(", ".join(self.teams["bad"]))
        elif role == "percival":
            if "morgana" in self.roles:
                extra_text = "The Merlin and Morgana are: {}, {}.".format(self.roles["merlin"], self.roles["morgana"])
            else:
                extra_text = "The Merlin is: {}.".format(self.roles["merlin"])

        return "{} {}".format(yourrole_text, extra_text)

    def assign_roles(self):
        self.history.clear()
        random.shuffle(self.players)
        roles = get_roles(len(self.players))
        for idx, player in enumerate(self.players):
            self.roles[roles[idx]] = player
            self.player_roles[player] = roles[idx]
            self.teams["bad" if roles[idx] in bad_roles else "good"].append(player)

        for player in self.players:
            self.role_texts[player] = self.get_role_text(player)
            sio.emit('player role', [player, self.role_texts[player]], namespace='/private')

        self.current_quest_leader = random.randint(0, len(self.players))

    def quest_size(self):
        return quests[len(self.players)][self.quest]

    def next_quest_leader(self):
        self.current_quest_leader += 1
        self.current_quest_leader %= len(self.players)

        quest_size = quests[len(self.players)][self.quest]
        quest_leader = self.players[self.current_quest_leader]
        players_text = " ".join(["player{}".format(i + 1) for i in range(quest_size)])

        sio.emit('numeric history', [self.successes, self.failures], namespace='/public')
        sio.emit('history', self.history, namespace='/public')
        sio.emit('proposal request', [quest_leader, quest_size, players_text], namespace='/public')

        self.state = "propose_who"
        return self.players[self.current_quest_leader]

    def next_quest(self):
        self.quest += 1
        self.next_quest_leader()

    def propose(self, player, players):
        if self.state != "propose_who":
            return

        if len(set(players)) != quests[len(self.players)][self.quest]:
            sio.emit('proposal error', "SIKE, THAT'S THE WRONG NUMBER", namespace='/public')
        elif player != self.players[self.current_quest_leader]:
            sio.emit('proposal error', "{}: You're not the quest leader. Maybe next time.".format(player), namespace='/public')
        else:
            for player in players:
                if player not in self.players:
                    sio.emit('proposal error', "{} isn't playing.".format(player), namespace='/public')
                    return False

            self.questers = players
            sio.emit('proposed team', [self.players[self.current_quest_leader], players], namespace='/public')
            self.votes.clear()
            self.state = "vote_who"

    def tally_votes(self):
        return [i[0] for i in self.votes.items() if i[1]], [i[0] for i in self.votes.items() if not i[1]]

    def vote_on_questers(self, player, affirmative):
        if self.state != "vote_who":
            return

        if player not in self.players:
            sio.emit('vote error', [player, "You can't vote if you aren't in the game."], namespace='/private')
        else:
            self.votes[player] = affirmative
            sio.emit('vote confirmation', player, namespace='/public')

            if len(self.votes) == len(self.players):
                yes_votes, no_votes = self.tally_votes()
                success = len(yes_votes) > len(no_votes)
                sio.emit('vote finish', [success, yes_votes, no_votes], namespace='/public')
                if success:
                    self.state = "quester_vote"
                    self.do_quest()
                else:
                    self.next_quest_leader()

    def do_quest(self):
        self.quest_fail_votes = 0
        self.questers_voted = []
        for player in self.questers:
            if player in self.teams["good"]:
                sio.emit('qvote poke', [player, 'good'], namespace='/private')
            else:
                sio.emit('qvote poke', [player, 'bad'], namespace='/private')

    def do_quest_vote(self, player, affirmative):
        if self.state != "quester_vote":
            return

        if player not in self.questers:
            sio.emit('qvote error', [player, "You aren't on the quest."], namespace='/private')
        elif player in self.questers_voted:
            sio.emit('qvote error', [player, "You've already voted on this quest."], namespace='/private')
        elif player in self.teams["good"] and not affirmative:
            sio.emit('qvote error', [player, "You can't vote to fail, you're on the good team!"], namespace='/private')
        else:
            self.questers_voted.append(player)
            sio.emit('qvote placed', player, namespace='/public')
            if not affirmative:
                self.quest_fail_votes += 1
                sio.emit('qvote confirmation', [player, 'fail'], namespace='/private')
            else:
                sio.emit('qvote confirmation', [player, 'pass'], namespace='/private')

        if len(self.questers_voted) == len(self.questers):
            self.do_quest_complete()

    def do_quest_complete(self):
        if len(self.players) >= 7 and self.quest == 3:
            votes_to_fail = 2
        else:
            votes_to_fail = 1

        status = self.quest_fail_votes < votes_to_fail
        self.history.append("History: Quest with {}: {}ed with {} votes to fail.".format(", ".join(self.questers), "pass" if status else "fail", self.quest_fail_votes))
        sio.emit('qvote finish', ["pass" if status else "fail", self.quest_fail_votes], namespace='/public')

        if status:
            self.successes += 1
        else:
            self.failures += 1

        if self.failures == 3:
            self.do_evil_win()
        elif self.successes == 3:
            self.do_assassin_pick()
        else:
            self.next_quest()

    def do_evil_win(self):
        sio.emit('game over', 'bad', namespace='/public')
        self.do_game_over()

    def do_assassin_pick(self):
        self.state = "assassin_pick"
        sio.emit('pick target', self.roles['assassin'], namespace='/public')

    def do_assassin_kill(self, player, target):
        if self.state != "assassin_pick":
            return

        if player != self.roles["assassin"]:
            sio.emit('target error', "{} isn't the assassin.".format(player), namespace='/public')
        elif target not in self.teams["good"]:
            sio.emit('target error', "They're not on the good team. Pick again.", namespace='/public')
        else:
            if self.player_roles[target] == "merlin":
                self.do_evil_win()
            else:
                self.do_good_win()

    def do_good_win(self):
        sio.emit('game over', 'good', namespace='/public')
        self.do_game_over()

    def do_game_over(self):
        global joined_players
        self.state = "no_game"
        joined_players = []

@app.route('/')
def index():
    return render_template('index.html')

#@sio.on('connected', namespace='/private')
#@sio.on('connected', namespace='/public')
#def connect():
#    emit('connect')

@sio.on('game start request', namespace='/private')
def start_game(player):
    global game, joined_players
    if player not in joined_players:
        emit('game start error', "You have to join the game before you can start it.", broadcast=True, namespace='/public')
    elif len(joined_players) < 5:
        emit('game start error', "The game must have at least five players.", broadcast=True, namespace='/public')
    else:
        emit('game start', joined_players, broadcast=True, namespace='/public')
        game = AvalonGame(joined_players)
        game.assign_roles()
        game.next_quest()

@sio.on('force game start request', namespace='/private')
def force_start_game(args):
    global game
    player, players = args
    if len(players) < 5:
        emit('game start error', "The game must have at least five players.", broadcast=True, namespace='/public')
    else:
        emit('game start', players, broadcast=True, namespace='/public')
        game = AvalonGame(players)
        game.assign_roles()
        game.next_quest()


@sio.on('join game request', namespace='/private')
def join_game(player):
    if player in joined_players:
        emit('join game error', "You're already in the game, {}.".format(player), broadcast=True, namespace='/public')
    elif len(joined_players) >= 10:
        emit('join game error', "There are too many players.", broadcast=True, namespace='/public')
    else:
        joined_players.append(player)
        emit('join game', player, broadcast=True, namespace='/public')

@sio.on('kill player request', namespace='/private')
def kill_player(args):
    player, target = args
    game.do_assassin_kill(player, target)

@sio.on('propose players', namespace='/private')
def propose_players(args):
    player, players = args
    game.propose(player, players)

@sio.on('vote request', namespace='/private')
def vote(args):
    player, truefalse = args
    game.vote_on_questers(player, truefalse)

@sio.on('qvote request', namespace='/private')
def qvote(args):
    player, truefalse = args
    game.do_quest_vote(player, truefalse)

if __name__ == '__main__':
    sio.run(app, host="0.0.0.0")

