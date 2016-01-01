# Avalon gameplay with cslavalon
Avalon is a game traditionally played using cards, but it can also be played
over IRC. This guide will teach you how to play over IRC.

## Teams
There are two teams in the game: the bad/evil team and the good team. The bad
team will consist of approximately one-third of the players playing. The rest
of the players are assigned to the good team.

## Roles
As part of team assignment, some players are assigned special roles. These
roles have additional information which can be helpful to the team.

## Bad Team
- The **Assassin** chooses who to assassinate at the end of the game. They
  also know the identities of the other bad team members.
- **Mordred** knows the identities of other bad team members, but is invisible
  to Merlin.
- **Morgana** knows the identities of other bad team members, and can be seen
  by Percival.

## Good Team
- **Merlin** knows the identitites of everyone on the bad team, except for
  Mordred.
- **Percival** knows the identitites of Morgana and Merlin, but not which player
  has which role (i.e. "Morgana and Merlin are player1 and player2, but not
  necessarily in this order").

## Objective
The bad team can win in several ways:
- By deducing the identity of Merlin
- By failing three quests

The good team can only win if:
- Three quests succeed, and
- the bad team does not deduce the identity of Merlin

## Gameplay
Gameplay consists of five "quests." On each quest, a quest leader is chosen.
The quest leader must pick a certain number of players to go on the quest.
They may include themselves. The number of players that will go on the quest
varies based on how many quests have occurred so far, and how many players are
in the game.

After the quest leader chooses who will go on the quest, players vote on the
team. If a majority votes in the affirmative, the players will start the quest.
Otherwise, a new quest leader is chosen.

Once the players are on their quest, they will vote for the quest to succeed or
fail. Players on the good team must vote to pass, but players on the bad team
can vote for the quest to pass or fail. In most cases, only one vote is required
for the quest to fail. However, if the game has seven or more players, the
fourth quest will require two votes to fail.

If three quests fail, the bad team wins. If three quests succeed, the Assassin
may pick a target to kill. If this target is Merlin, the bad team will win.
If it is not, the good team will win.

## Using the bot
The bot accepts several commands:

### Before a game
- Use **!join** to join a game.
- Use **!leave** to leave a game.
- Use **!start** to start a game.

### During quest team formation stage
- If you are the quest leaader, use **!propose player1 player2 ... playern** to
  propose a quest team.
- Once the quest team has been proposed, private message the bot with **yes** or
  **no** to vote.

## During a quest
- If you are on the quest, private message the bot with **pass** or **fail** to
  vote.
