#!/usr/bin/env python
from pyrcb import IRCBot
from socketIO_client import SocketIO, BaseNamespace
import threading
import sys
import yaml


class AvalonBot(IRCBot):
    def __init__(self, private_ns):
        self.private_ns = private_ns

    def on_message(self, message, nickname, channel, is_query):
        if not is_query:
            if message.startswith("!propose "):
                self.private_ns.emit('propose players', [nickname, message.split()[1:]])
            elif message.startswith("!kill "):
                self.private_ns.emit('kill player request', [nickname, message.split()[1]])
            elif message == "!join":
                self.private_ns.emit('join game request', nickname)
            elif message == "!start":
                self.private_ns.emit('game start request', nickname)
            elif message.startswith("!tarts "):
                self.private_ns.emit('force game start request', [nickname, message.split()[1:]])
        else:
            if message == "yes":
                self.private_ns.emit('vote request', [nickname, True])
            elif message == "no":
                self.private_ns.emit('vote request', [nickname, False])
            elif message == "pass":
                self.private_ns.emit('qvote request', [nickname, True])
            elif message == "fail":
                self.private_ns.emit('qvote request', [nickname, False])


class PublicNamespace(BaseNamespace):

    def on_game_start_error(self, message):
        PublicNamespace.bot.send(PublicNamespace.channel, message)

    def on_game_start(self, args):
        PublicNamespace.bot.send(PublicNamespace.channel, "The game is starting.")

    def on_join_game_error(self, message):
        PublicNamespace.bot.send(PublicNamespace.channel, message)

    def on_join_game(self, player):
        PublicNamespace.bot.send(PublicNamespace.channel, "Welcome to the game, {}!".format(player))

    def on_numeric_history(self, args):
        successes, failures = args
        PublicNamespace.bot.send(PublicNamespace.channel, "There have been {} successful quests and {} failed quests.".format(successes, failures))

    def on_history(self, history):
        for element in history:
            PublicNamespace.bot.send(PublicNamespace.channel, element)

    def on_proposal_request(self, args):
        quest_leader, quest_size, players_text = args
        PublicNamespace.bot.send(PublicNamespace.channel, "The quest leader is {0}. {0}, please propose a quest with {1} players by using !propose {2}".format(quest_leader, quest_size, players_text))

    def on_proposal_error(self, message):
        PublicNamespace.bot.send(PublicNamespace.channel, message)

    def on_proposed_team(self, args):
        player, players = args
        PublicNamespace.bot.send(PublicNamespace.channel, "The proposed quest team is: {}. Vote by /msg'ing me 'yes' or 'no'.".format(", ".join(players)))

    def on_vote_confirmation(self, player):
        PublicNamespace.bot.send(player, "Okay, your vote has been recorded.")
        PublicNamespace.bot.send(PublicNamespace.channel, "{} has voted.".format(player))

    def on_vote_finish(self, args):
        success, yes_votes, no_votes = args
        PublicNamespace.bot.send(PublicNamespace.channel, "The votes are in! The vote was{} successful.".format("" if success else " not"))
        if yes_votes:
            PublicNamespace.bot.send(PublicNamespace.channel, "Yes votes: {}".format(", ".join(yes_votes)))
        if no_votes:
            PublicNamespace.bot.send(PublicNamespace.channel, "No votes: {}".format(", ".join(no_votes)))

    def on_qvote_placed(self, player):
        PublicNamespace.bot.send(PublicNamespace.channel, "{} has completed the quest.".format(player))

    def on_qvote_finish(self, args):
        res, fail_votes = args
        PublicNamespace.bot.send(PublicNamespace.channel, "The votes are in! The quest {}ed with {} votes to fail.".format(res, fail_votes))

    def on_game_over(self, result):
        PublicNamespace.bot.send(PublicNamespace.channel, "Game over! The {} guys win!".format(result))

    def on_pick_target(self, player):
        PublicNamespace.bot.send(PublicNamespace.channel, "{}, please choose a target with !kill player.".format(player))

    def on_target_error(self, message):
        PublicNamespace.bot.send(PublicNamespace.channel, message)


class PrivateNamespace(BaseNamespace):

    def on_player_role(self, args):
        player, role_text = args
        PrivateNamespace.bot.send(player, role_text)

    def on_vote_error(self, args):
        player, message = args
        PrivateNamespace.bot.send(player, message)

    def on_qvote_poke(self, args):
        player, role = args
        PrivateNamespace.bot.send(player, "Please vote with 'pass' or '{}'.".format("pass" if role == "good" else "fail"))

    def on_qvote_error(self, args):
        player, message = args
        PrivateNamespace.bot.send(player, message)

    def on_qvote_confirmation(self, args):
        player, vote = args
        PrivateNamespace.bot.send(player, "You voted to {} the quest.".format(vote))


def main():
    conf_file = sys.argv[1] if len(sys.argv) > 1 else "config.yml"
    with open(conf_file) as f:
        config = yaml.load(f)

    channel = config["irc"]["channel"]
    sio = SocketIO(config["state"]["host"], config["state"]["port"])

    public_ns = sio.define(PublicNamespace, '/public')
    private_ns = sio.define(PrivateNamespace, '/private')

    bot = AvalonBot(private_ns)
    # TODO: figure out a less hacky solution.
    public_ns.bot = bot
    public_ns.channel = channel
    private_ns.bot = bot

    sio_t = threading.Thread(target=sio.wait)
    sio_t.start()

    bot.connect(config["irc"]["server"], config["irc"]["port"])
    bot.register(config["irc"]["nick"])
    bot.join(channel)

    bot.listen()

if __name__ == '__main__':
    main()
