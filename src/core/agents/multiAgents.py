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

# Abbreviation
better = betterEvaluationFunction


def riskAwareEvaluationFunction(currentGameState: GameState):
    """
    Q6: Risk-aware evaluation function that extends betterEvaluationFunction
    with spatial entrapment awareness.

    DESCRIPTION:
    Adds specific optimizations and new components:
    1. Unified BFS Search — A single BFS flood fill from Pacman's position 
       calculates TWO crucial metrics simultaneously:
       a) True maze distance to the closest food (overcoming Manhattan distance flaws).
       b) Degrees of Freedom (DoF): counts how many cells are reachable within 
          DOF_RADIUS steps. A low DoF value means Pacman is in a dead-end.
    2. Entrapment Risk — ghost threat (summed over active ghosts within THREAT_RADIUS) 
       is *amplified* when DoF is low. Being cornered near a ghost is 
       penalized heavily compared to being threatened in open space.
       entrapment_risk = ghost_threat * (1.0 - (dof / MAX_DOF)) * WEIGHT
    3. Conditional Escape Bonus — When a ghost threat is present, a small reward 
       proportional to DoF is added. This encourages Pacman to navigate towards 
       open intersections rather than narrow corridors when being hunted.
    """

    pos         = currentGameState.getPacmanPosition()
    foodList    = currentGameState.getFood().asList()
    ghostStates = currentGameState.getGhostStates()
    capsules    = currentGameState.getCapsules()
    walls       = currentGameState.getWalls()

    score = currentGameState.getScore()

    # BFS from Pacman's position
    # Compute 3 metrics simultaneously in a single pass:
    #   1. Actual maze distance to the closest food
    #   2. Degrees of Freedom (DoF): reachable cells within DOF_RADIUS steps
    #   3. Maze distance to each ghost
    DOF_RADIUS = 5

    queue = util.Queue()
    queue.push((pos, 0))
    visited = {pos}

    closest_food_dist = None
    dof = 1
    ghost_dists = [-1] * len(ghostStates) 

    while not queue.isEmpty():
        cur_pos, depth = queue.pop()

        # 1. Check for food
        if closest_food_dist is None and cur_pos in foodList:
            closest_food_dist = depth

        # 2. Check for ghosts
        for i in range(len(ghostStates)):
            ghost_pos = ghostStates[i].getPosition()
            ghost_pos_int = (int(ghost_pos[0]), int(ghost_pos[1]))
            
            if cur_pos == ghost_pos_int and ghost_dists[i] == -1:
                ghost_dists[i] = depth

        # 3. Check stopping conditions
        food_done = False
        if closest_food_dist is not None or len(foodList) == 0:
            food_done = True
            
        dof_done = False
        if depth >= DOF_RADIUS:
            dof_done = True
            
        ghosts_done = True
        for dist in ghost_dists:
            if dist == -1:
                ghosts_done = False
                break

        if food_done and dof_done and ghosts_done:
            break

        # 4. Flood fill to 4 directions
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            next_x = cur_pos[0] + dx
            next_y = cur_pos[1] + dy
            next_pos = (next_x, next_y)
            
            if next_pos not in visited and not walls[next_x][next_y]:
                visited.add(next_pos)
                queue.push((next_pos, depth + 1))
                
                if depth + 1 <= DOF_RADIUS:
                    dof += 1

    if closest_food_dist is None:
        closest_food_dist = 0

    # SCORE CALCULATION BASED ON GATHERED METRICS
    
    # 1. Food Score
    # Reward approaching food and penalize having many foods left on the map
    if len(foodList) > 0:
        food_distance_bonus = 10.0 / (closest_food_dist + 1)
        score += food_distance_bonus
        
        food_remaining_penalty = 4 * len(foodList)
        score -= food_remaining_penalty

    # 2. Capsule Score
    # Heavily penalize remaining capsules to prioritize eating them early
    capsule_penalty = 20 * len(capsules)
    score -= capsule_penalty

    # 3. Ghost Score
    # Penalize getting close to active ghosts, reward approaching scared ghosts
    for i in range(len(ghostStates)):
        ghost = ghostStates[i]
        
        # Retrieve the accurate distance calculated by BFS above
        if ghost_dists[i] != -1:
            ghost_dist = ghost_dists[i]
        else:
            ghost_dist = manhattanDistance(pos, ghost.getPosition())

        if ghost.scaredTimer > 0:
            # Scared ghost -> Pacman is the hunter -> High reward for chasing
            scared_ghost_bonus = 200.0 / (ghost_dist + 1)
            score += scared_ghost_bonus
        else:
            # Active ghost -> Pacman is the prey -> Penalize to stay away
            if ghost_dist <= 1:
                score -= 500  # Imminent death -> Extreme penalty
            else:
                active_ghost_penalty = 2.0 / ghost_dist
                score -= active_ghost_penalty

    # 4. Entrapment Risk - THE SECRET WEAPON OF Q6
    # Extremely heavy penalty if the space is narrow (low DoF) AND a ghost is nearby
    MAX_DOF = (DOF_RADIUS * 2 + 1) ** 2  # The most open environment possible
    
    # Calculate narrowness (from 0.0 to 1.0, higher means narrower space)
    dof_ratio = dof / MAX_DOF
    narrowness_factor = 1.0 - dof_ratio 

    # Calculate Ghost Threat
    THREAT_RADIUS = 6
    ghost_threat = 0.0
    for i in range(len(ghostStates)):
        ghost = ghostStates[i]
        if ghost.scaredTimer == 0:  # Only active ghosts are a threat
            if ghost_dists[i] != -1:
                dist = ghost_dists[i]
            else:
                dist = manhattanDistance(pos, ghost.getPosition())
                
            if dist < THREAT_RADIUS:  # If ghost is inside the alert radius
                ghost_threat += (THREAT_RADIUS - dist)  # Closer ghost -> Higher threat

    # Total Entrapment Risk: Ghost Threat x Narrowness x Penalty Weight (40)
    entrapment_risk = ghost_threat * narrowness_factor * 40.0
    score -= entrapment_risk

    # 5. Escape Bonus
    # If threatened by a ghost, prioritize directions with high Degrees of Freedom (DoF)
    # This guides Pacman towards open intersections to easily escape
    if ghost_threat > 0:
        escape_bonus = 0.5 * dof
        score += escape_bonus

    return score

# Abbreviation
riskAware = riskAwareEvaluationFunction

# Registry of available evaluation functions for easy discovery and menu selection
EVALUATION_FUNCTIONS = {
    'score': scoreEvaluationFunction,
    'better': betterEvaluationFunction,
    'riskAware': riskAwareEvaluationFunction,
}
