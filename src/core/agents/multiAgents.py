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


# def riskAwareEvaluationFunction(currentGameState: GameState):
#     """
#     Q6: evaluate a state by balancing progress with local survival risk.

#     DESCRIPTION: <write something here so we know what you did>
#     """
#     # TODO Q6: Implement a risk-aware state evaluation function.
#     util.raiseNotDefined()
    
def riskAwareEvaluationFunction(currentGameState: GameState):
    """
    Q6: Risk-aware evaluation function that extends betterEvaluationFunction
    with spatial entrapment awareness.

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

    # ── Food features (inherited from Q5) ───────────────────────────────────
    if foodList:
        foodDistances = [manhattanDistance(pos, f) for f in foodList]
        score += 10.0 / min(foodDistances)
        score -= 0.3 * (sum(foodDistances) / len(foodDistances))
    score -= 5.0 * len(foodList)

    # ── Capsule features (inherited from Q5) ────────────────────────────────
    if capsules:
        capsuleDists = [manhattanDistance(pos, c) for c in capsules]
        anyGhostClose = any(
            manhattanDistance(pos, g.getPosition()) <= 5 and g.scaredTimer == 0
            for g in ghostStates
        )
        if anyGhostClose:
            score += 10.0 / (min(capsuleDists) + 1)
        score -= 15.0 * len(capsules)

    # ── Ghost features (inherited from Q5) ──────────────────────────────────
    for ghost in ghostStates:
        d = manhattanDistance(pos, ghost.getPosition())
        if ghost.scaredTimer > 0:
            score += 200.0 / (d + 0.5)     # chase scared ghosts
        else:
            if d <= 1:
                score -= 2000
            elif d <= 2:
                score -= 200
            elif d <= 4:
                score -= 20

    # ── Q6: Degrees of Freedom (BFS flood fill, inlined) ───────────────────────
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
    MAX_DOF = DOF_RADIUS * DOF_RADIUS * 4   # conservative upper bound = 100
    dof_norm = dof / MAX_DOF                # 0..1  (1 = fully open)

    # ── Q6: Entrapment Risk  (ghost threat × spatial constraint) ─────────────
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

    # ── Q6: Escape Route Bonus ───────────────────────────────────────────────
    # Only reward openness when a ghost is actually nearby; otherwise the bonus
    # competes with food-seeking and causes Pacman to wander.
    if ghost_threat > 0:
        score += 0.5 * dof

    return score

# Abbreviation
riskAware = riskAwareEvaluationFunction
