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
        
        # Check for active ghosts nearby
        for ghostState in newGhostStates:
            ghostPos = ghostState.getPosition()
            # If a ghost is active (not scared) and is too close, this is a very bad state
            if ghostState.scaredTimer == 0 and manhattanDistance(newPos, ghostPos) <= 1:
                return -float('inf')

        # Find distance to closest food
        foodList = newFood.asList()
        minFoodDist = float('inf')
        for foodPos in foodList:
            dist = manhattanDistance(newPos, foodPos)
            if dist < minFoodDist:
                minFoodDist = dist
                
        score = successorGameState.getScore()
        if minFoodDist != float('inf'):
            score += 1.0 / minFoodDist
            
        return score

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
    # util.raiseNotDefined()

# Abbreviation
better = betterEvaluationFunction


def riskAwareEvaluationFunction(currentGameState: GameState):
    """
    Q6: evaluate a state by balancing progress with local survival risk.

    DESCRIPTION:
    Builds on Q5's food/capsule/ghost features and adds two new Q6-specific
    components:

    1. Degrees of Freedom (DoF) — a BFS flood fill from Pacman's position
       counts how many cells are reachable within DOF_RADIUS steps.  A low
       DoF value means Pacman is in a dead-end or tight corridor.

    2. Entrapment Risk — ghost threat (summed over nearby active ghosts) is
       *amplified* by the inverse of DoF.  Being cornered near a ghost is
       penalised far more heavily than being cornered in open space.

       entrapment_risk = ghost_threat * (1 / dof) * WEIGHT

    3. Escape Bonus — a small reward proportional to DoF so Pacman prefers
       open intersections over narrow corridors, all else being equal.
    """
    if currentGameState.isWin():
        return float('inf')
    if currentGameState.isLose():
        return -float('inf')

    pos         = currentGameState.getPacmanPosition()
    foodList    = currentGameState.getFood().asList()
    ghostStates = currentGameState.getGhostStates()
    capsules    = currentGameState.getCapsules()
    walls       = currentGameState.getWalls()

    score = currentGameState.getScore()

    # Food features (inherited from Q5)
    if len(foodList) > 0:
        foodDistances = [manhattanDistance(pos, food) for food in foodList]
        closestFoodDist = min(foodDistances)
        score += 10.0 / (closestFoodDist + 1)
        score -= 4 * len(foodList)

    # Capsule features (inherited from Q5)
    score -= 20 * len(capsules)

    # Ghost features (inherited from Q5)
    for ghost in ghostStates:
        ghostDist = manhattanDistance(pos, ghost.getPosition())
        if ghost.scaredTimer > 0:
            score += 200.0 / (ghostDist + 1)
        else:
            if ghostDist <= 1:
                score -= 500
            else:
                score -= 2.0 / ghostDist

    # Q6: Degrees of Freedom (BFS flood fill, inlined)
    # Count non-wall cells reachable from pos within DOF_RADIUS steps.
    # A low count means Pacman is in a dead-end or narrow corridor.
    DOF_RADIUS = 5
    _visited = set()
    _queue = util.Queue()
    _queue.push((pos, 0))
    _visited.add(pos)
    while not _queue.isEmpty():
        _cur, _depth = _queue.pop()
        if _depth >= DOF_RADIUS:
            continue
        _x, _y = _cur
        for _dx, _dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            _nx, _ny = _x + _dx, _y + _dy
            _nb = (_nx, _ny)
            if _nb not in _visited and not walls[_nx][_ny]:
                _visited.add(_nb)
                _queue.push((_nb, _depth + 1))
    dof = len(_visited)   # includes the starting cell
    MAX_DOF = (DOF_RADIUS * 2 + 1) * (DOF_RADIUS * 2 + 1)   # conservative upper bound = 121
    dof_norm = dof / MAX_DOF                # 0..1  (1 = fully open)

    # Q6: Entrapment Risk  (ghost threat × spatial constraint)
    # Accumulate threat only from nearby ACTIVE ghosts
    THREAT_RADIUS = 6
    ghost_threat = 0.0
    for ghost in ghostStates:
        if ghost.scaredTimer == 0:
            d = manhattanDistance(pos, ghost.getPosition())
            if d < THREAT_RADIUS:
                ghost_threat += (THREAT_RADIUS - d)   # range 1..5

    # entrapment_factor: high when DoF is low (trapped), zero when fully open
    # Using (1 - dof_norm) so it scales cleanly between 0 and 1
    entrapment_factor = 1.0 - dof_norm
    entrapment_risk   = ghost_threat * entrapment_factor * 40.0
    score -= entrapment_risk

    # Q6: Escape Route Bonus
    # Only reward openness when a ghost is actually nearby; otherwise the bonus
    # competes with food-seeking and causes Pacman to wander.
    if ghost_threat > 0:
        score += 0.5 * dof

    return score

# Abbreviation
riskAware = riskAwareEvaluationFunction

# Registry of available evaluation functions for easy discovery and menu selection
EVALUATION_FUNCTIONS = {
    'score': scoreEvaluationFunction,
    'better': betterEvaluationFunction,
    'riskAware': riskAwareEvaluationFunction,
}
