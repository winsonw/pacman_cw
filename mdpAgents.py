# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
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

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import util

class Grid:

    # Constructor
    #
    # Note that it creates variables:
    #
    # grid:   an array that has one position for each element in the grid.
    # width:  the width of the grid
    # height: the height of the grid
    #
    # Grid elements are not restricted, so you can place whatever you
    # like at each location. You just have to be careful how you
    # handle the elements when you use them.
    def __init__(self, width, height):
        self.width = width
        self.height = height
        subgrid = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(0)
            subgrid.append(row)

        self.grid = subgrid


    def display(self):
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print self.grid[i][j],
            # A new line after each line of the grid
            print
            # A line after the grid
        print

    def setValue(self, x, y, value):
        self.grid[self.height - (int(y) + 1)][int(x)] = value

    def getValue(self, x, y):
        return self.grid[int(y)][int(x)]

    def getHeight(self):
        return self.height

    def getWidth(self):
        return self.width

    def getValueAtExact(self,x,y):
        return self.grid[int(x)][int(y)]

    def setValueAtExact(self,x,y,value):
        self.grid[int(x)][int(y)] = value



class MDPAgent(Agent):

    # Original Part start------------------------------------
    def __init__(self):
        print "Starting up MDPAgent!"

    def registerInitialState(self, state):
        self.makeMap(state)
        self.addWallsToMap(state)

        self.randomActionP = 0.8
        self.width = self.map.getWidth()
        self.height = self.map.getHeight()
        self.gamma = 0.9
        self.ghostNum = len(api.ghosts(state))
        self.DISTANCEASCLOSE = 2 * self.ghostNum

        self.lastState = None
        self.remainFood = 0
        self.ghostPrediction = []
        # self.initialRouteMap()
        self.lastDecidedAction = None

    def final(self, state):
        print "Looks like the game just ended!"

    # For now I just move randomly
    def getAction(self, state):
        return self.algorithm(state)
    #Original Part end------------------------------------------


    #Making Map start-------------------------------------------
    def makeMap(self,state):
        corners = api.corners(state)
        height = self.getLayoutHeight(corners)
        width  = self.getLayoutWidth(corners)
        self.map = Grid(width, height)

    def getLayoutHeight(self, corners):
        height = -1
        for i in range(len(corners)):
            if corners[i][1] > height:
                height = corners[i][1]
        return height + 1

    def getLayoutWidth(self, corners):
        width = -1
        for i in range(len(corners)):
            if corners[i][0] > width:
                width = corners[i][0]
        return width + 1

    def addWallsToMap(self, state):
        walls = api.walls(state)
        for i in range(len(walls)):
            self.map.setValue(walls[i][0], walls[i][1], '%')

    def updateMap(self, state):
        # First, make all grid elements that aren't walls blank.
        for i in range(self.map.getHeight()):
            for j in range(self.map.getWidth()):
                if self.map.getValueAtExact(i, j) != '%':
                    self.map.setValueAtExact(i, j, ' ')
        food = api.food(state)
        capsule = api.capsules(state)
        ghosts = api.ghostStatesWithTimes(state)
        pacman = api.whereAmI(state)
        self.map.setValue(pacman[0], pacman[1], 'P')
        for i in range(len(capsule)):
            self.map.setValue(capsule[i][0], capsule[i][1], '1')
            pos = self.processPos(capsule[i])
            self.foodNearByMap[pos[0]][pos[1]].add(pos)
        for i in range(len(food)):
            self.map.setValue(food[i][0], food[i][1], '*')
            pos = self.processPos(food[i])
            self.foodNearByMap[pos[0]][pos[1]].add(pos)
        for i in range(len(ghosts)):
            if ghosts[i][1] <= 3:
                self.map.setValue(ghosts[i][0][0], ghosts[i][0][1], 'G')
                for j in range(len(self.ghostPrediction[i])):
                    if self.map.getValueAtExact(self.ghostPrediction[i][j][0], self.ghostPrediction[i][j][1]) != "G":
                        self.map.setValueAtExact(self.ghostPrediction[i][j][0], self.ghostPrediction[i][j][1], 'M')
    #Make Map end---------------------------------------------------------


    #Util start-----------------------------------------------------------
    def positionAfterMove(self,pos,dir):
        if dir == Directions.NORTH: newPos = (pos[0] - 1, pos[1])
        elif dir == Directions.SOUTH: newPos = (pos[0] + 1, pos[1])
        elif dir == Directions.EAST: newPos = (pos[0], pos[1] + 1)
        elif dir == Directions.WEST: newPos = (pos[0], pos[1] - 1)
        else: newPos = pos
        return newPos

    def convertNumDir(self,num):
        if num == 4: return Directions.STOP
        if num == 0: return Directions.NORTH
        if num == 1: return Directions.SOUTH
        if num == 2: return Directions.WEST
        if num == 3: return Directions.EAST

    # def initialRouteMap(self):
    #     self.routeMap = []
    #     for i in range(self.height):
    #         routeRow = []
    #         for j in range(self.width):
    #             routeCell = []
    #             for x in range(self.height):
    #                 routeRRow = []
    #                 for y in range(self.width):
    #                     routeRRow.append(0)
    #                 routeCell.append(routeRRow)
    #             routeRow.append(routeCell)
    #         self.routeMap.append(routeRow)

    def initialNeardbyFoodMap(self):
        foodNearByMap = []
        for i in range(self.height):
            foodNearByRow = []
            for j in range(self.width):
                foodNearByRow.append(set())
            foodNearByMap.append(foodNearByRow)
        return foodNearByMap

    def initialPolicyMap(self):
        policyMap = []
        for i in range(self.height):
            policyRow = []
            for j in range(self.width):
                policyRow.append(None)
            policyMap.append(policyRow)
        return policyMap

    def initialRewardMap(self):
        self.rewardMap = []
        for i in range(self.height):
            rewardRow = []
            for j in range(self.width):
                rewardRow.append(None)
            self.rewardMap.append(rewardRow)

    def initialUtilMap(self):
        utilMap = []
        for i in range(self.height):
            utilRow = []
            for j in range(self.width):
                if self.map.getValueAtExact(i,j) != '%':
                    utilRow.append(0)
                else:
                    utilRow.append(-1)
            utilMap.append(utilRow)
        return utilMap

    def getNearbyPos(self,pos,contain_stop = True):
        nearbyPos =[]
        if contain_stop:
            r = 5
        else:
            r = 4
        for n in range(r):
            dir = self.convertNumDir(n)
            if not self.isFacingWall(pos,dir):
                posAfter = self.positionAfterMove(self.posTurnInt(pos),dir)
                nearbyPos.append(posAfter)
        return nearbyPos

    def printMap(self, object):
        for i in object:
            for j in i:
                if j is None:
                    print "XX",
                elif isinstance(j,str):
                    print j[:2],
                elif isinstance(j,set):
                    print len(j),
                else:
                    print (int(j))//10,
            print
        print

    def isRandomAction(self,state):
        if self.lastState == None:
            return None
        actualAction = self.getDir(self.processPos(api.whereAmI(self.lastState)),self.processPos(api.whereAmI(state)))
        return actualAction == self.lastDecidedAction

    def posTurnInt(self,pos):
        return (int(pos[0]),int(pos[1]))

    def processPoss(self, objects):
        for i in range(len(objects)):
            objects[i] = self.processPos(objects[i])
        return objects

    def processPos(self, pos):
        return (self.height - (pos[1] + 1), pos[0])

    def isFacingWall(self,pos,dir):
        i,j = self.positionAfterMove(pos,dir)
        return self.map.getValueAtExact(i,j) == "%"

    def getDir(self,oldPos,newPos):
        if oldPos[1] > newPos[1]:
            return Directions.WEST
        if oldPos[1] < newPos[1]:
            return Directions.EAST
        if oldPos[0] > newPos[0]:
            return Directions.NORTH
        if oldPos[0] < newPos[0]:
            return Directions.SOUTH
        return Directions.STOP

    def distanceLimited(self,objects, pos, limit):
        nearObjects = []
        for i in range(len(objects)):
            if self.distanceBetween(pos, objects[i]) <= limit:
                nearObjects.append(objects[i])
        return nearObjects

    def randomNearbyAction(self,utilMap,pos):
        count = 0
        value = 0
        for new_pos in self.getNearbyPos(pos):
            (i, j) = new_pos
            if (utilMap[i][j] != -1):
                value += utilMap[i][j]
                count += 1
        return value / count

    # def findRoute(self,pos1,pos2, step, posList = [], beenList = []):
    #     currentPos = posList[0]
    #     i,j = pos1
    #     i1,j1 = currentPos
    #     if currentPos == pos2:
    #         return self.routeMap[i][j][i1][j1]
    #
    #     beenList.append(currentPos)
    #     index = 0
    #     while (index < len(posList)):
    #         if posList[index] == currentPos:
    #             posList.pop(index)
    #         else:
    #             index+=1
    #     for pos3 in self.getNearbyPos(currentPos,contain_stop=False):
    #         if not beenList.__contains__(pos3):
    #             i3,j3 = pos3
    #             self.routeMap[i][j][i3][j3] = step + 1
    #             h = self.routeMap[i][j][i3][j3] + util.manhattanDistance(pos3,pos2)
    #             index = 0
    #             while (index < len(posList) and h > (self.routeMap[i][j][posList[index][0]][posList[index][1]] + util.manhattanDistance(posList[index],pos2))):
    #                 index += 1
    #             posList.insert(index,pos3)
    #     for n in range(len(posList)):
    #         if not beenList.__contains__(posList[n]):
    #             result = self.findRoute(pos1,pos2,step = self.routeMap[i][j][posList[n][0]][posList[n][1]],posList= posList,beenList=beenList)
    #             if result != -1:
    #                 return result
    #     return -1

    def distanceBetween(self,pos1,pos2):
        # return util.manhattanDistance(pos1,pos2)
        return self.findRoute(pos1,pos2,step=0,posList=[pos1],beenList=[])
    #Util end-------------------------------------------------------------


    #Reward start---------------------------------------------------------
    def getRewards(self, state, pos):
        if self.rewardMap[pos[0]][pos[1]] != None:
            return self.rewardMap[pos[0]][pos[1]]
        if self.map.getValueAtExact(pos[0],pos[1]) == "G":
            return -990
        if self.map.getValueAtExact(pos[0],pos[1]) == "M":
            return -891
        reward = self.rewardFunction(state, pos)
        self.rewardMap[pos[0]][pos[1]] = reward
        return reward

    def rewardFunction(self,state,pos):
        food_value = self.foodValue(state,pos)
        return 10*food_value

    # def _rewardFunction(self,state,pos):
    #     weightOfFood = 20
    #     weightOfSocialDistance = 80
    #     food_value = self.foodValue(state,pos)
    #     socialDistance_value = self.socialDistanceValue(state,pos)
    #     reward = weightOfFood * food_value + weightOfSocialDistance * socialDistance_value
    #     reward = 10 * food_value
    #     return reward
    #
    # def socialDistanceValue(self,state,pos):
    #     DISTANCEASCLOSE = 3
    #
    #     overallValue = 0
    #     ghostsState = api.ghostStatesWithTimes(state)
    #     ghosts = self.ghostPrediction
    #     for i in range(self.ghostNum):
    #         ghostState = ghostsState[i]
    #         if ghostState[1] <= DISTANCEASCLOSE:
    #             ghostPossibleMovement = ghosts[i]
    #
    #             value = 0.0
    #             for ghostPos in ghostPossibleMovement:
    #                 distance = self.distanceBetween(pos, ghostPos)
    #                 if distance <= 3:
    #                     value += 1 - 1 / (distance + 1)
    #             value /= len(ghostPossibleMovement)
    #             overallValue += value
    #
    #     overallValue /= self.ghostNum
    #     return overallValue
    #
    # def _foodValue(self,state,pos):
    #     food = self.processPoss(api.food(state))
    #     nearbyFood = len(self.distanceLimited(food,pos,self.DISTANCEASCLOSE))
    #     value =float(nearbyFood)/self.remainFood * 0.5
    #     if self.map.getValueAtExact(pos[0],pos[1]) == "*" or self.map.getValueAtExact(pos[0],pos[1]) == "1":
    #         value += 0.5
    #     return value

    def foodValue(self,state,pos):
        value = 0
        nearbyFood = len(self.foodNearByMap[pos[0]][pos[1]])
        if self.map.getValueAtExact(pos[0],pos[1]) == "*" or self.map.getValueAtExact(pos[0],pos[1]) == "1":
            value = 0.5 + float(nearbyFood-1) / self.remainFood * 0.5
        else:
            value = float(nearbyFood) / self.remainFood * 0.5
        return value
    #Reward end------------------------------------------------------------

    # Algorithm start------------------------------------------------------
    def algorithm(self,state):
        # print self.isRandom(state)
        self.foodNearByMap = self.initialNeardbyFoodMap()
        policyMap = self.initialPolicyMap()
        utilMap = self.initialUtilMap()

        self.remainFood = len(api.food(state)) + len(api.capsules(state))
        self.ghostPrediction = self.predictGhostNextMove(state)
        self.updateMap(state)
        self.findNearbyFood()

        actions = api.legalActions(state)
        if Directions.STOP in actions:
            actions.remove(Directions.STOP)
        self.initialRewardMap()
        for n in range(20):
            utilMap = self.policyEvaluation(state,utilMap,policyMap)
            policyMap = self.policyImprovement(utilMap,policyMap)

        # self.printMap(utilMap)
        # self.printMap(policyMap)
        # self.map.display()

        i,j = self.processPos(api.whereAmI(state))
        chosenActionDir = policyMap[i][j]
        self.lastState = state
        self.lastDecidedAction = chosenActionDir
        return api.makeMove(chosenActionDir, actions)

    def findNearbyFood(self):
        for n in range(self.DISTANCEASCLOSE - 1):
            newFoodMap = self.initialNeardbyFoodMap()
            for i in range(self.height):
                for j in range(self.width):
                    if self.map.getValueAtExact(i,j) != "%":
                        nearyByBlock = self.getNearbyPos((i, j))
                        for pos in nearyByBlock:
                            for x in self.foodNearByMap[pos[0]][pos[1]]:
                                newFoodMap[i][j].add(x)
            self.foodNearByMap = newFoodMap


    def predictGhostNextMove(self,state):
        ghostsPossibleMovement = []
        ghostsPos = self.processPoss(api.ghosts(state))
        if not self.lastState is None:
            lastGhostPos = self.processPoss(api.ghosts(self.lastState))
        for i in range(self.ghostNum):
            ghostPos = ghostsPos[i]
            nearbyPos = self.getNearbyPos(ghostPos,contain_stop=False)
            if len(nearbyPos) >= 2 and not self.lastState is None and nearbyPos.__contains__(lastGhostPos[i]):
                index = nearbyPos.index(lastGhostPos[i])
                nearbyPos.pop(index)
            ghostPossibleMovement = nearbyPos
            ghostsPossibleMovement.append(ghostPossibleMovement)
        return ghostsPossibleMovement

    def policyEvaluation(self,state, utilMap, policyMap):
        newUtilMap = self.initialUtilMap()
        for i in range(self.height-2):
            for j in range(self.width-2):
                pos = (i+1,j+1)
                if utilMap[i+1][j+1] != -1:
                    reward = self.getRewards(state,pos)
                    newUtilMap[i + 1][j + 1] = reward
                    if policyMap[i+1][j+1] != None:
                        action_i, action_j = self.positionAfterMove((i+1,j+1),policyMap[i+1][j+1])
                        expect = self.randomActionP * utilMap[action_i][action_j] + (1 - self.randomActionP) * self.randomNearbyAction(utilMap,pos)
                        newUtilMap[i+1][j+1] += self.gamma * expect
        return newUtilMap

    def policyImprovement(self,utilMap,policyMap):
        for i in range(self.height - 2):
            for j in range(self.width - 2):
                if utilMap[i + 1][j + 1] != -1:
                    policyMap[i + 1][j + 1] = self.selectLagrestNearby(utilMap,(i + 1, j + 1))
        return policyMap

    def selectLagrestNearby(self,utilMap,pos):
        max_i = None
        max_j = None
        max_dir = Directions.STOP
        for new_pos in self.getNearbyPos(pos):
            (new_i, new_j) = new_pos
            if (max_i is None) or (utilMap[new_i][new_j] >= utilMap[max_i][max_j]):
                max_i = new_i
                max_j = new_j
                max_dir = self.getDir(pos,new_pos)
        return max_dir
    # Algorithm end--------------------------------------------------------
















