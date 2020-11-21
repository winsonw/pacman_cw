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
import random
import game
import util
import mapAgents


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

    # Print the grid out.
    def display(self):
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print self.grid[i][j],
            # A new line after each line of the grid
            print
            # A line after the grid
        print

    # The display function prints the grid out upside down. This
    # prints the grid out so that it matches the view we see when we
    # look at Pacman.
    def prettyDisplay(self):
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print self.grid[self.height - (i + 1)][j],
            # A new line after each line of the grid
            print
            # A line after the grid
        print

    # Set and get the values of specific elements in the grid.
    # Here x and y are indices.
    def setValue(self, x, y, value):
        self.grid[y][x] = value

    def getValue(self, x, y):
        return self.grid[y][x]

    # Return width and height to support functions that manipulate the
    # values stored in the grid.
    def getHeight(self):
        return self.height

    def getWidth(self):
        return self.width



class MDPAgent(Agent):

    # Original Part start------------------------------------
    def __init__(self):
        print "Starting up MDPAgent!"

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        self.makeMap(state)
        self.addWallsToMap(state)
        self.updateFoodInMap(state)
        self.map.display()

        self.randomActionP = 0.8
        self.width = self.map.getWidth()
        self.height = self.map.getHeight()
        self.gamma = 0.9

        self.lastState = None
        self.currentState = None
        self.remainFood = 0

        print "Running registerInitialState for MDPAgent!"
        print "I'm at:"
        print api.whereAmI(state)

    def final(self, state):
        print "Looks like the game just ended!"

    # For now I just move randomly
    def getAction(self, state):
        self.updateFoodInMap(state)
        self.map.prettyDisplay()

        return self.algorithm(state)
    #Original Part end------------------------------------------



    #Making Map start-------------------------------------------
    def makeMap(self,state):
        corners = api.corners(state)
        print corners
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

    def updateFoodInMap(self, state):
        # First, make all grid elements that aren't walls blank.
        for i in range(self.map.getWidth()):
            for j in range(self.map.getHeight()):
                if self.map.getValue(i, j) != '%':
                    self.map.setValue(i, j, ' ')
        food = api.food(state)
        capsule = api.capsules(state)
        for i in range(len(capsule)):
            self.map.setValue(capsule[i][0], capsule[i][1], '1')
        for i in range(len(food)):
            self.map.setValue(food[i][0], food[i][1], '*')
    #Make Map end---------------------------------------------------------



    #Util start-----------------------------------------------------------
    # This is what gets run in between multiple games
    def positionAfterMove(self,pos,dir):
        if dir == Directions.NORTH: newPos = (pos[0], pos[1]+1)
        elif dir == Directions.SOUTH: newPos = (pos[0], pos[1]-1)
        elif dir == Directions.EAST: newPos = (pos[0]+1, pos[1])
        elif dir == Directions.WEST: newPos = (pos[0]-1, pos[1])
        else: newPos = pos
        return newPos

    def convertNumDir(self,num):
        if num == 0: return Directions.STOP
        if num == 1: return Directions.NORTH
        if num == 2: return Directions.SOUTH
        if num == 3: return Directions.WEST
        if num == 4: return Directions.EAST

    def distanceBetween(self,pos1,pos2):
        return util.manhattanDistance(pos1,pos2)
    #Util end-------------------------------------------------------------

    #Reward start---------------------------------------------------------
    def getRewards(self, state, pos):
        reward = self.rewardFunction(state, pos)
        return reward

    def rewardFunction(self,state,pos):
        weightOfFood = 20
        weightOfSocialDistance = 80
        reward = weightOfFood * self.foodValue(state,pos) + weightOfSocialDistance * self.socialDistanceValue(state,pos)
        return reward

    def socialDistanceValue(self,state,pos):
        DISTANCEASCLOSE = 3

        overallValue = 0
        ghosts = api.ghostStatesWithTimes(state)
        for (ghost,ghostState) in ghosts:
            if ghostState <= DISTANCEASCLOSE:
                ghostPossibleMovement = self.predictGhostNextMove(ghost)

                # 0-100
                value = 0

                for ghostPos in ghostPossibleMovement:
                    distance = self.distanceBetween(pos,ghostPos)
                    if distance <= 3:
                        value += 100 / (distance + 1)
                value /= len(ghostPossibleMovement)
                overallValue += value

        overallValue /= len(ghosts)
        return overallValue

    # Not Finished
    def predictGhostNextMove(self,ghostPos):
        ghostPossibleMovement = []
        ghostPossibleMovement.append(ghostPos)
        return ghostPossibleMovement

    def foodValue(self,state,pos):
        DISTANCEASCLOSE = 3

        food = api.food(state)
        nearbyFood = api.distanceLimited(food,state,DISTANCEASCLOSE)
        value = nearbyFood/self.remainFood

        return value
    #Reward end------------------------------------------------------------

    # Algorithm start------------------------------------------------------
    def algorithm(self,state):
        self.lastState = self.currentState
        self.currentState = state
        self.remainFood = len(api.food(state)) + len(api.capsules(state))
        actions = api.legalActions(state)
        if Directions.STOP in actions:
            actions.remove(Directions.STOP)

        utilMap,policyMap = self.initialMap()

        for n in range(10):
            utilMap = self.policyEvaluation(state,utilMap,policyMap)
            policyMap = self.policyImprovement(utilMap,policyMap)

        i,j = api.whereAmI()
        chosenActionDir = policyMap[i][j]

        return api.makeMove(chosenActionDir, actions)

    def initialMap(self):
        policyMap = []
        for i in range(self.height):
            policyRow = []
            for j in range(self.width):
                policyRow.append(None)
            policyMap.append(policyRow)
        return self.initialUtilMap(),policyMap

    def initialUtilMap(self):
        utilMap = []
        for i in range(self.width):
            utilRow = []
            for j in range(self.height):
                if self.map.getValue(i,j) != '%':
                    utilRow.append(0)
                else:
                    utilRow.append(-1)
            utilMap.append(utilRow)
        return utilMap

    def policyEvaluation(self,state, utilMap, policyMap):
        newUtilMap = self.initialUtilMap()
        for i in range(self.height-2):
            for j in range(self.width-2):
                pos = (i+1,j+1)
                if utilMap[i+1][j+1] != -1:
                    reward = self.getRewards(state,pos)
                    newUtilMap[i + 1][j + 1] = reward
                    if policyMap[i+1][j+1] != None:
                        expect = self.randomActionP * policyMap[i+1][j+1] + (1 - self.randomActionP) * self.randomNearbyAction(utilMap,pos)
                        newUtilMap[i+1][j+1] += self.gamma * expect
        return newUtilMap

    def policyImprovement(self,utilMap,policyMap):
        for i in range(self.height - 2):
            for j in range(self.width - 2):
                if utilMap[i + 1][j + 1] != -1:
                    policyMap[i + 1][j + 1] = self.selectLagrestNearby(utilMap,(i + 1, j + 1))

    def selectLagrestNearby(self,utilMap,pos):
        max_i = 0
        max_j = 0
        for n in range(5):
            dir = self.convertNumDir(n)
            (new_i, new_j) = self.positionAfterMove((pos[0],pos[1]), dir)
            if (utilMap[new_i][new_j] > utilMap[max_i][max_j]):
                max_i = new_i
                max_j = new_j
                max_dir = dir
        return max_dir

    def randomNearbyAction(self,utilMap,pos):
        count = 0
        value = 0
        for n in range(5):
            dir = self.convertNumDir(n)
            (i, j) = self.positionAfterMove((pos[0], pos[1]), dir)
            if (utilMap[i][j] != -1):
                value += utilMap[i][j]
                count += 1
        return value / count
    # Algorithm end--------------------------------------------------------
















