#!/usr/bin/env python
from pyrcb import IRCBot
from socketIO_client import SocketIO, BaseNamespace
import threading
import sys
import yaml
<<<<<<< HEAD
import subprocess as sp
import os

state = sp.Popen(['python','state.py'])
=======
>>>>>>> a6106fd1ccba846ef77576dcb1333761a1488f46

conf_file = sys.argv[1] if len(sys.argv) > 1 else "config.yml"
with open(conf_file) as f:
    config = yaml.load(f)

admins = ["fwilson", "sdrodge", "okulkarni"]
denied = {}

def plural(n, thing, interptext="", plural_form=None):
    if not interptext:
        interptext = " "
    else:
        interptext = " " + interptext + " "
    if n == 1:
        return "1{}{}".format(interptext, thing)
    if not plural_form:
        return "{}{}{}s".format(n, interptext, thing)
    return "{}{}{}".format(n, interptext, plural_form)

def lf(l):
    if len(l) == 1:
        return l[0]
    if len(l) == 2:
        return "{} and {}".format(*l)
    return "{}, and {}".format(", ".join(l[:-1]), l[-1])

class AvalonBot(IRCBot):

    def on_message(self, message, nickname, channel, is_query):
        if message.startswith("!"):
            if nickname in denied:
                for i in denied[nickname]:
                    if i in message:
                        bot.send(channel, "{}: lol nope".format(nickname))
                        return
        if not is_query:
            if message.startswith("!propose ") or message.startswith("!pick "):
                private_ns.emit('propose players', [nickname, message.split()[1:]])
            elif message.startswith("!kill "):
                private_ns.emit('kill player request', [nickname, message.split()[1]])
            elif message == "!join":
                private_ns.emit('join game request', nickname)
            elif message.startswith("!fjoin ") and nickname in admins:
                private_ns.emit('join game request', message.split()[1])
            elif message == "!leave":
                private_ns.emit("leave game request", nickname)
            elif message.startswith("!kick ") and nickname in admins:
                private_ns.emit("leave game request", message.split()[1])
            elif message == "!start":
                private_ns.emit('game start request', nickname)
            elif message == "!help":
                bot.send(channel, "Rules are at https://github.com/fwilson42/avalon/blob/master/rules.md | During a game: \x02!propose\x02 a quest team, \x02!kill\x02 a player as assassin, vote \x02yes\x02 or \x02no\x02 on a proposed quest team in PM, \x02pass\x02 or \x02fail\x02 a quest. | Before a game: \x02!join\x02 the game or \x02!leave\x02 it. \x02!start\x02 once you have enough players.")
            elif message.startswith("!deny ") and nickname in admins:
                args = message.split()
                if args[1] not in denied:
                    denied[args[1]] = []
                denied[args[1]].append(args[2])
                bot.send(channel, "{} is now denied {}".format(args[1], lf(denied[args[1]])))
            elif message.startswith("!allowall ") and nickname in admins:
                args = message.split()
                denied[args[1]] = []
                bot.send(channel, "ok!")
<<<<<<< HEAD
            elif message == '!restart':
                sp.Popen.terminate(state)
                os.execl(sys.executable, sys.executable, *sys.argv)
=======
>>>>>>> a6106fd1ccba846ef77576dcb1333761a1488f46
        else:
            message = message.lower()
            if message == "yes":
                private_ns.emit('vote request', [nickname, True])
            elif message == "no":
                private_ns.emit('vote request', [nickname, False])
            elif message == "pass":
                private_ns.emit('qvote request', [nickname, True])
            elif message == "fail":
                private_ns.emit('qvote request', [nickname, False])


class PublicNamespace(BaseNamespace):

    def on_game_start_error(self, message):
        bot.send(channel, message)

    def on_game_start(self, args):
        bot.send(channel, "The game is starting.")

    def on_join_game_error(self, message):
        bot.send(channel, message)

    def on_leave_game_error(self, message):
        bot.send(channel, message)

    def on_join_game(self, args):
        player, players = args
        bot.send(channel, "Welcome to the game, {}! {}.".format(player, plural(len(players), "player")))

    def on_leave_game(self, args):
        player, players = args
        bot.send(channel, "Bye, {}! {} left.".format(player, plural(len(players), "player")))

    def on_numeric_history(self, args):
        successes, failures = args
        bot.send(channel, "There have been {} and {}.".format(plural(successes, "quest", "successful"), plural(failures, "quest", "failed")))

    def on_history(self, history):
        for questers, status, votes, proposed in history:
            bot.send(channel, "History: Quest with {}: {}ed with {} to fail. Proposed by {}.".format(lf(questers), status, plural(votes, "vote"), proposed))

    def on_proposal_request(self, args):
        quest_leader, quest_size, players_text = args
        bot.send(channel, "The quest leader is {0}. {0}, please propose a quest with {1} players by using !propose {2}".format(quest_leader, quest_size, players_text))

    def on_proposal_error(self, message):
        bot.send(channel, message)

    def on_proposed_team(self, args):
        player, players = args
        bot.send(channel, "The proposed quest team is: {}. Vote by /msg'ing me 'yes' or 'no'.".format(lf(players)))

    def on_vote_confirmation(self, player):
        bot.send(player, "Okay, your vote has been recorded.")
        bot.send(channel, "{} has voted.".format(player))

    def on_vote_finish(self, args):
        success, yes_votes, no_votes = args
        bot.send(channel, "The votes are in! The vote was{} successful.".format("" if success else " not"))
        if yes_votes:
            bot.send(channel, "Yes votes: {}".format(lf(yes_votes)))
        if no_votes:
            bot.send(channel, "No votes: {}".format(lf(no_votes)))

    def on_qvote_placed(self, player):
        bot.send(channel, "{} has completed the quest.".format(player))

    def on_qvote_finish(self, args):
        res, fail_votes = args
        bot.send(channel, "The votes are in! The quest {}ed with {} to fail.".format(res, plural(fail_votes, "vote")))

    def on_game_over(self, result):
        bot.send(channel, result)

    def on_pick_target(self, player):
        bot.send(channel, "{}, please choose a target with !kill player.".format(player))

    def on_target_error(self, message):
        bot.send(channel, message)

    def on_game_over(self, message):
        bot.send(channel, message)

    def on_current_quest_failed_votes(self, message):
        bot.send(channel, "{} have failed for this quest.".format(plural(message, "proposal")))


class PrivateNamespace(BaseNamespace):

    def on_player_role(self, args):
        player, role_text = args
        bot.send(player, role_text)

    def on_vote_error(self, args):
        player, message = args
        bot.send(player, message)

    def on_qvote_poke(self, args):
        player, role = args
        bot.send(player, "Please vote with 'pass' or '{}'.".format("pass" if role == "good" else "fail"))

    def on_qvote_error(self, args):
        player, message = args
        bot.send(player, message)

    def on_qvote_confirmation(self, args):
        player, vote = args
        bot.send(player, "You voted to {} the quest.".format(vote))

# FIXME: kill globals

channel = config["irc"]["channel"]
sio = SocketIO(config["state"]["host"], config["state"]["port"], headers={"Authentication":config["secret"]})

bot = AvalonBot()
public_ns = sio.define(PublicNamespace, '/public')
private_ns = sio.define(PrivateNamespace, '/private')


def main():
    sio_t = threading.Thread(target=sio.wait)
    sio_t.start()

    bot.connect(config["irc"]["server"], config["irc"]["port"])
    bot.register(config["irc"]["nick"])
    bot.join(channel)

    bot.listen()

if __name__ == '__main__':
    main()
