import math
import copy
import random
import sys
from pyrcb import IRCBot

default_bad_roles = ["assassin", "mordred", "morgana", "badguy"]
default_good_roles = ["merlin", "percival", "goodguy", "goodguy", "goodguy", "goodguy"]
channel = "#tjcsl-avalon" if len(sys.argv) < 2 else sys.argv[1]
nick = "cslavalon" if len(sys.argv) < 2 else "avalonbot"

quests = {
    5:  [2, 3, 2, 3, 3],
    6:  [2, 3, 4, 3, 4],
    7:  [2, 3, 3, 4, 4],
    8:  [3, 4, 4, 5, 5],
    9:  [3, 4, 4, 5, 5],
    10: [3, 4, 4, 5, 5]
}

def pluralize(number, thing):
    if number == 1:
        return "{} {}".format(number, thing)
    return "{} {}s".format(number, thing)

def list_format(l):
    if len(l) == 1:
        return l[0]
    return ", ".join(l[:-1]) + ", and " + l[-1]

class AvalonGame:
    def __init__(self, bot, players, bad_roles, good_roles):
        self.players = copy.copy(players)
        self.bot = bot
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
        self.bad_roles = bad_roles
        self.good_roles = good_roles

    def get_role_text(self, player):
        role = self.player_roles[player]
        team = "good" if role in self.good_roles else "bad"
        article = "a" if role.endswith("guy") else "the"
        yourrole_text = "You are {} {} ({}).".format(article, role.title(), team)
        extra_text = "You have no special information."
        if role in ["assassin", "mordred", "morgana", "merlin"]:
            extra_text = "The bad team is: {}.".format(list_format(self.teams["bad"]))
        elif role == "percival":
            if "morgana" in self.roles:
                extra_text = "The Merlin and Morgana are: {} and {}.".format(self.roles["merlin"], self.roles["morgana"])
            else:
                extra_text = "The Merlin is: {}.".format(self.roles["merlin"])

        return "{} {}".format(yourrole_text, extra_text)

    def assign_roles(self):
        self.history.clear()
        random.shuffle(self.players)
        roles = get_roles(len(self.players), self.bad_roles, self.good_roles)
        for idx, player in enumerate(self.players):
            self.roles[roles[idx]] = player
            self.player_roles[player] = roles[idx]
            self.teams["bad" if roles[idx] in self.bad_roles else "good"].append(player)

        for player in self.players:
            self.role_texts[player] = self.get_role_text(player)
            self.bot.send(player, self.role_texts[player])

        self.current_quest_leader = random.randint(0, len(self.players))

    def quest_size(self):
        return quests[len(self.players)][self.quest]

    def next_quest_leader(self):
        self.current_quest_leader += 1
        self.current_quest_leader %= len(self.players)

        quest_size = quests[len(self.players)][self.quest]
        quest_leader = self.players[self.current_quest_leader]
        players_text = " ".join(["player{}".format(i + 1) for i in range(quest_size)])

        self.bot.send(channel, "There have been {} successful quests and {} failed quests.".format(self.successes, self.failures))
        for hist in self.history:
            self.bot.send(channel, hist)
        self.bot.send(channel, "The quest leader is {}. Please propose a quest with {} players by using !propose {}".format(quest_leader, quest_size, players_text))

        self.state = "propose_who"
        return self.players[self.current_quest_leader]

    def next_quest(self):
        self.quest += 1
        self.next_quest_leader()

    def propose(self, player, players):
        if self.state != "propose_who":
            return

        if len(set(players)) != quests[len(self.players)][self.quest]:
            self.bot.send(channel, "SIKE, THAT'S THE WRONG NUMBER")
        elif player != self.players[self.current_quest_leader]:
            self.bot.send(channel, "Maybe next time.")
        else:
            for player in players:
                if player not in self.players:
                    self.bot.send(channel, "{} isn't playing.".format(player))
                    return False

            self.questers = players
            self.bot.send(channel, "The proposed quest team is: {}. Vote by /msg'ing me 'yes' or 'no'.".format(list_format(players)))
            self.votes.clear()
            self.state = "vote_who"

    def tally_votes(self):
        return [i[0] for i in self.votes.items() if i[1]], [i[0] for i in self.votes.items() if not i[1]]

    def vote_on_questers(self, player, affirmative):
        if self.state != "vote_who":
            return

        if player not in self.players:
            self.bot.send(player, "You can't vote if you aren't in the game.")
        else:
            self.votes[player] = affirmative
            self.bot.send(player, "Okay, your vote has been recorded.")
            self.bot.send(channel, "{} has voted.".format(player))

            if len(self.votes) == len(self.players):
                yes_votes, no_votes = self.tally_votes()
                success = len(yes_votes) > len(no_votes)
                self.bot.send(channel, "The votes are in! The vote was{} successful.".format("" if success else " not"))
                if yes_votes:
                    self.bot.send(channel, "Yes votes: {}".format(list_format(yes_votes)))
                if no_votes:
                    self.bot.send(channel, "No votes: {}".format(list_format(no_votes)))
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
                self.bot.send(player, "Please vote with 'pass' or 'pass'.")
            else:
                self.bot.send(player, "Please vote with 'pass' or 'fail'.")

    def do_quest_vote(self, player, affirmative):
        if self.state != "quester_vote":
            return

        if player not in self.questers:
            self.bot.send(player, "You aren't on the quest.")
        elif player in self.questers_voted:
            self.bot.send(player, "You've already voted.")
        else:
            self.questers_voted.append(player)
            self.bot.send(channel, "{} has completed the quest.".format(player))
            if not affirmative:
                self.quest_fail_votes += 1
                self.bot.send(player, "You voted to fail the quest.")
            else:
                self.bot.send(player, "You voted to pass the quest.")

        if len(self.questers_voted) == len(self.questers):
            self.do_quest_complete()

    def do_quest_complete(self):
        if len(self.players) >= 7 and self.quest == 3:
            votes_to_fail = 2
        else:
            votes_to_fail = 1

        status = self.quest_fail_votes < votes_to_fail
        self.history.append("History: Quest with {}: {}ed with {} to fail.".format(", ".join(self.questers), "pass" if status else "fail", pluralize(self.quest_fail_votes, "vote")))
        self.bot.send(channel, "The votes are in! The quest {}ed with {} to fail.".format("pass" if status else "fail", pluralize(self.quest_fail_votes, "vote")))

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
        self.bot.send(channel, "Game over! The bad guys win!")
        self.do_game_over()

    def do_assassin_pick(self):
        self.state = "assassin_pick"
        self.bot.send(channel, "{}, please choose a target with !kill player.".format(self.roles["assassin"]))

    def do_assassin_kill(self, player, target):
        if self.state != "assassin_pick":
            return

        if player != self.roles["assassin"]:
            self.bot.send(channel, "{} isn't the assassin.".format(player))
        elif target not in self.teams["good"]:
            self.bot.send(channel, "Are you dumb?")
        else:
            if self.player_roles[target] == "merlin":
                self.do_evil_win()
            else:
                self.do_good_win()

    def do_good_win(self):
        self.bot.send(channel, "Game over! The good guys win!")
        self.do_game_over()

    def do_game_over(self):
        self.state = "no_game"
        self.bot.players.clear()

class AvalonBot(IRCBot):
    def on_message(self, message, nickname, channel, is_query):
        if not is_query:
            if message.startswith("!propose "):
                self.game.propose(nickname, message.split()[1:])
            elif message.startswith("!kill "):
                args = message.split()[1:]
                if not args:
                    self.send(channel, "You need to specify someone to kill.")
                else:
                    self.game.do_assassin_kill(nickname, args[0])
            elif message == "!join":
                if self.game.state != "no_game":
                    self.send(channel, "You can't join while a game is running.")
                elif nickname in self.players:
                    self.send(channel, "You're already in the game, {}.".format(nickname))
                elif len(self.players) == 10:
                    self.send(channel, "There are too many players.")
                else:
                    self.players.append(nickname)
                    self.send(channel, "Welcome to the game, {}! {}.".format(nickname, pluralize(len(self.players), "player")))
            elif message == "!leave":
                if self.game.state != "no_game":
                    self.send(channel, "You can't leave a game while it is running.")
                elif nickname not in self.players:
                    self.send(channel, "You're not in the game, {}.".format(nickname))
                else:
                    self.players.remove(nickname)
                    self.send(channel, "Bye, {}. {}.".format(nickname, pluralize(len(self.players), "player")))
            elif message == "!start":
                if self.game.state != "no_game":
                    self.send(channel, "Seriously?")
                elif nickname not in self.players:
                    self.send(channel, "You have to join the game before you can start it.")
                elif len(self.players) < 5:
                    self.send(channel, "The game must have at least five players.")
                else:
                    self.game = AvalonGame(self, self.players, *self.roles)
                    self.game.assign_roles()
                    self.game.next_quest()
        else:
            if self.game.state != "no_game":
                if message == "yes":
                    self.game.vote_on_questers(nickname, True)
                elif message == "no":
                    self.game.vote_on_questers(nickname, False)
                elif message == "pass":
                    self.game.do_quest_vote(nickname, True)
                elif message == "fail":
                    self.game.do_quest_vote(nickname, False)

def get_roles(n_players, bad_roles, good_roles):
    n_bad = math.ceil(n_players / 3)
    n_good = n_players - n_bad
    return bad_roles[:n_bad] + good_roles[:n_good]

bot = AvalonBot()
bot.game = AvalonGame(bot, [], default_bad_roles, default_good_roles)
bot.players = []
bot.roles = [default_bad_roles, default_good_roles]

bot.connect("chat.freenode.net", 6667)
bot.register(nick)
bot.join(channel)

bot.listen()
