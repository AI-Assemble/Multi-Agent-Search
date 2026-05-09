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
        # TODO Q2: Implement minimax search and return the best action.
        util.raiseNotDefined()

class AlphaBetaAgent(MultiAgentSearchAgent):
    """
    Your minimax agent with alpha-beta pruning (question 3)
    """

    def getAction(self, gameState: GameState):
        """
        Returns the minimax action using self.depth and self.evaluationFunction
        """
        # TODO Q3: Implement alpha-beta pruning on top of minimax search.
        util.raiseNotDefined()

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
        def expectimax(state, depth, agentIndex):
            # Dừng duyệt cây lại nếu đã đạt đến độ sâu nhất định hoặc game state là win hoặc over
            if state.isWin() or state.isLose() or depth == self.depth:
                return self.evaluationFunction(state)

            legalActions = state.getLegalActions(agentIndex)
            if not legalActions:
                return self.evaluationFunction(state)

            nextAgent = agentIndex + 1
            nextDepth = depth

            # nếu đã duyệt đủ các trạng thái của agent ghost và pacman thì độ sâu của thuật toán sẽ tăng lên 1 và tiếp tục duyệt tiếp
            if nextAgent == state.getNumAgents():
                nextAgent = 0
                nextDepth += 1

            # Đối tượng duyệt hiện tại là pacman thì ta sẽ lấy kết quả max từ hàm đánh giá các trạng thái của pacman
            if agentIndex == 0:
                return max(
                    expectimax(state.generateSuccessor(agentIndex, action), nextDepth, nextAgent)
                    for action in legalActions
                )

            # nếu đối tượng hiện tại là ghost thì ta sẽ lấy kết quả trung bình từ hàm đánh giá các trạng thái của ghost
            totalValue = 0
            for action in legalActions:
                successor = state.generateSuccessor(agentIndex, action)
                totalValue += expectimax(successor, nextDepth, nextAgent)
            return totalValue / len(legalActions)

        bestAction = None
        bestValue = float("-inf")
        
        #Bắt đầu duyệt cây expectimax đã được thiết kế trên để tìm ra hướng đi cho pacman    
        for action in gameState.getLegalActions(0):
            successor = gameState.generateSuccessor(0, action)
            value = expectimax(successor, 0, 1)
            if value > bestValue:
                bestValue = value
                bestAction = action

        return bestAction

def betterEvaluationFunction(currentGameState: GameState):
    """
    Your extreme ghost-hunting, pellet-nabbing, food-gobbling, unstoppable
    evaluation function (question 5).

    DESCRIPTION: <write something here so we know what you did>
    """
    # TODO Q5: Implement the improved state evaluation function for this question.
    
    #Lấy ra các thông tin về trạng thái hiện tại của game:
    pacmanPos = currentGameState.getPacmanPosition()
    foodGrid = currentGameState.getFood()
    ghostStates = currentGameState.getGhostStates()
    capsules = currentGameState.getCapsules()
    foodList = foodGrid.asList()
    score = currentGameState.getScore()
    print("origin score: ", score )

    #Cơ chế thưởng phạt để pacman ưu tiên ăn quả nhằm đạt được điểm cao
    if len(foodList) > 0:
        foodDistances = [
            manhattanDistance(pacmanPos, food)
            for food in foodList
        ]

        closestFoodDist = min(foodDistances)

        # thưởng khi gần food
        score += 10.0 / (closestFoodDist + 1)

        # phạt khi còn nhiều food
        score -= 4 * len(foodList)

    #Cơ chế thưởng phạt để pacman tránh ghost có hướng di chuyển random một cách ổn định nhất
    for ghost in ghostStates:
        ghostPos = ghost.getPosition()
        ghostDist = manhattanDistance(pacmanPos, ghostPos)

        # ghost đang sợ
        if ghost.scaredTimer > 0:
            score += 200 / (ghostDist + 1)

        # ghost nguy hiểm
        else:
            if ghostDist <= 1:
                score -= 500
            else:
                score -= 2.0 / ghostDist
    
    #Phạt nặng khi còn nhiều capsules
    score -= 20 * len(capsules)

    return score

# Abbreviation
better = betterEvaluationFunction


def riskAwareEvaluationFunction(currentGameState: GameState):
    """
    Q6: evaluate a state by balancing progress with local survival risk.

    DESCRIPTION: <write something here so we know what you did>
    """
    # TODO Q6: Implement a risk-aware state evaluation function.
    util.raiseNotDefined()
    
# Abbreviation
riskAware = riskAwareEvaluationFunction
