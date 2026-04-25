# multiAgents.py
# --------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from ..model.util import manhattanDistance
from ..model.game import Directions
import random
from ..model import util

from ..model.game import Agent
from ..controller.pacman import GameState

class ReflexAgent(Agent):
    """
    A reflex agent chooses an action at each choice point by examining
    its alternatives via a state evaluation function.

    The code below is provided as a guide.  You are welcome to change
    it in any way you see fit, so long as you don't touch our method
    headers.
    """


    def getAction(self, gameState: GameState):
        """
        You do not need to change this method, but you're welcome to.

        getAction chooses among the best options according to the evaluation function.

        Just like in the previous project, getAction takes a GameState and returns
        some Directions.X for some X in the set {NORTH, SOUTH, WEST, EAST, STOP}
        """
        # Collect legal moves and successor states
        legalMoves = gameState.getLegalActions()

        # Choose one of the best actions
        scores = [self.evaluationFunction(gameState, action) for action in legalMoves]
        bestScore = max(scores)
        bestIndices = [index for index in range(len(scores)) if scores[index] == bestScore]
        chosenIndex = random.choice(bestIndices) # Pick randomly among the best

        # TODO Q1: Improve the reflex agent evaluation if you want a stronger
        #          local decision rule for this question.

        return legalMoves[chosenIndex]

    def evaluationFunction(self, currentGameState: GameState, action):
        """
        Design a better evaluation function here.

        The evaluation function takes in the current and proposed successor
        GameStates (pacman.py) and returns a number, where higher numbers are better.

        The code below extracts some useful information from the state, like the
        remaining food (newFood) and Pacman position after moving (newPos).
        newScaredTimes holds the number of moves that each ghost will remain
        scared because of Pacman having eaten a power pellet.

        Print out these variables to see what you're getting, then combine them
        to create a masterful evaluation function.
        """
        # Useful information you can extract from a GameState (pacman.py)
        successorGameState = currentGameState.generatePacmanSuccessor(action)
        newPos = successorGameState.getPacmanPosition()
        newFood = successorGameState.getFood()
        newGhostStates = successorGameState.getGhostStates()
        newScaredTimes = [ghostState.scaredTimer for ghostState in newGhostStates]

        # TODO Q1: Implement the reflex evaluation function for this question.
        return successorGameState.getScore()

def scoreEvaluationFunction(currentGameState: GameState):
    """
    This default evaluation function just returns the score of the state.
    The score is the same one displayed in the Pacman GUI.

    This evaluation function is meant for use with adversarial search agents
    (not reflex agents).
    """
    return currentGameState.getScore()

class MultiAgentSearchAgent(Agent):
    """
    This class provides some common elements to all of your
    multi-agent searchers.  Any methods defined here will be available
    to the MinimaxPacmanAgent, AlphaBetaPacmanAgent & ExpectimaxPacmanAgent.

    You *do not* need to make any changes here, but you can if you want to
    add functionality to all your adversarial search agents.  Please do not
    remove anything, however.

    Note: this is an abstract class: one that should not be instantiated.  It's
    only partially specified, and designed to be extended.  Agent (game.py)
    is another abstract class.
    """

    def __init__(self, evalFn = 'scoreEvaluationFunction', depth = '2'):
        self.index = 0 # Pacman is always agent index 0
        self.evaluationFunction = util.lookup(evalFn, globals())
        self.depth = int(depth)

class MinimaxAgent(MultiAgentSearchAgent):
    """
    Your minimax agent (question 2)
    """
    # TODO Q2: Implement minimax search and return the best action.
    def getAction(self, gameState: GameState):
        """
        Returns the minimax action from the current gameState using self.depth
        and self.evaluationFunction.

        Here are some method calls that might be useful when implementing minimax.

        gameState.getLegalActions(agentIndex):
        Returns a list of legal actions for an agent
        agentIndex=0 means Pacman, ghosts are >= 1

        gameState.generateSuccessor(agentIndex, action):
        Returns the successor game state after an agent takes an action

        gameState.getNumAgents():
        Returns the total number of agents in the game

        gameState.isWin():
        Returns whether or not the game state is a winning state

        gameState.isLose():
        Returns whether or not the game state is a losing state
        """
        def minimax(state, depth, agentIndex):
            # 1.Base case
            if depth == self.depth or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            # 2.Get the next agent
            nextAgent = (agentIndex + 1) % state.getNumAgents()

            # 3.Increase depth but only when back to Pacman
            # Depth is not total move but Pacman's moves
            if nextAgent == 0:
                nextDepth = depth + 1
            else: 
                nextDepth = depth

            # 4.Get all legal actions of the current agent
            actions = state.getLegalActions(agentIndex)

            # 5.MAX (Pacman)
            if agentIndex == 0:
                values = []
                for action in actions:
                    successor = state.generateSuccessor(agentIndex, action)
                    values.append(minimax(successor, nextDepth, nextAgent))
                return max(values)
            # 6.MIN (Ghosts)
            else:
                values = []
                for action in actions:
                    successor = state.generateSuccessor(agentIndex, action)
                    values.append(minimax(successor, nextDepth, nextAgent))
                return min(values)

        # Best score and action for Pacman (MAX)
        bestScore = float('-inf')
        bestAction = None

        # Get Pacman legal moves at the time (current state)
        actions = gameState.getLegalActions(0)

        # Examinating all actions then generate all outcomes
        # Return the best action for Pacman
        for action in actions: 
            successor = gameState.generateSuccessor(0, action)
            score = minimax(successor, 0, 1)
            if score > bestScore:
                bestScore = score
                bestAction = action
        return bestAction

class AlphaBetaAgent(MultiAgentSearchAgent):
    """
    Your minimax agent with alpha-beta pruning (question 3)
    """
    def getAction(self, gameState: GameState):
        """
        Returns the minimax action using self.depth and self.evaluationFunction
        """
        # TODO Q3: Implement alpha-beta pruning on top of minimax search.
        # util.raiseNotDefined()
        def alphaBetaValue(state, depth, agentIndex, alpha, beta):
            # 1.Base case
            if depth == self.depth or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            # 2.Get the next agent
            nextAgent = (agentIndex + 1) % state.getNumAgents()

            # 3.Increase depth but only when back to Pacman
            # Depth is not total move but Pacman's moves
            if nextAgent == 0:
                nextDepth = depth + 1
            else: 
                nextDepth = depth

            # 4.Get all legal actions of the current agent
            actions = state.getLegalActions(agentIndex)

            # 5.MAX (Pacman)
            if agentIndex == 0:
                value = float('-inf')
                for action in actions:
                    successor = state.generateSuccessor(agentIndex, action)
                    score = alphaBetaValue(successor, nextDepth, nextAgent, alpha, beta)
                    value = max(value, score)
                    alpha = max(alpha, value)
                    # Pruning
                    if alpha >= beta:
                        break
                return value
            # 6.MIN (Ghosts)
            else:
                value = float('inf')
                for action in actions:
                    successor = state.generateSuccessor(agentIndex, action)
                    score = alphaBetaValue(successor, nextDepth, nextAgent, alpha, beta)
                    value = min(value, score)
                    beta = min(beta, value)
                    # Pruning
                    if beta <= alpha:
                        break
                return value

        # Best score and action for Pacman (MAX)
        bestScore = float('-inf')
        bestAction = None

        # Get Pacman legal moves at the time (current state)
        actions = gameState.getLegalActions(0)

        # Examinating all actions then generate all outcomes
        # Return the best action for Pacman
        for action in actions: 
            successor = gameState.generateSuccessor(0, action)
            score = alphaBetaValue(successor, 0, 1, float('-inf'), float('+inf'))
            if score > bestScore:
                bestScore = score
                bestAction = action
        return bestAction
        # TODO: fix all bugs and pass all test

class ExpectimaxAgent(MultiAgentSearchAgent):
    """
      Your expectimax agent (question 4)
    """

    def getAction(self, gameState: GameState):
        """
        Returns the expectimax action using self.depth and self.evaluationFunction

        All ghosts should be modeled as choosing uniformly at random from their
        legal moves.
        """
        # TODO Q4: Implement expectimax with uniformly random ghost actions.
        util.raiseNotDefined()

def betterEvaluationFunction(currentGameState: GameState):
    """
    Your extreme ghost-hunting, pellet-nabbing, food-gobbling, unstoppable
    evaluation function (question 5).

    DESCRIPTION: <write something here so we know what you did>
    """
    # TODO Q5: Implement the improved state evaluation function for this question.
    util.raiseNotDefined()

# Abbreviation
better = betterEvaluationFunction
