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
        name = "Pacman"

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        self.makeMap(state)
        self.addWallsToMap(state)
        self.updateFoodInMap(state)
        self.map.display()
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

    def distanceBetween(self,pos1,pos2):
        return util.manhattanDistance(pos1,pos2)
    #Util end-------------------------------------------------------------





    def algorithm(self,state):
        actions = api.legalActions(state)
        if Directions.STOP in actions:
            actions.remove(Directions.STOP)

        rewards = self.getRewards(state,actions)

        chosenActionIndex = rewards.index(max(rewards))

        return api.makeMove(actions[chosenActionIndex], actions)


    def rewardFunction(self,state,pos,action):
        weightOfFood = 20
        weightOfSocialDistance = 80
        reward = weightOfFood * self.foodValue(state,pos,action) + weightOfSocialDistance * self.socialDistanceValue(state,pos)
        return reward

    def getRewards(self,state,actions):
        pos = api.whereAmI(state)
        rewards = []
        for action in actions:
            newPos = self.positionAfterMove(pos, action)
            rewards.append(self.rewardFunction(state,newPos,action))
        return rewards

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

    #need to be change
    def foodValue(self,state,pos,action):
        DISTANCEASCLOSE = 3

        food = api.food(state)
        directionCount = self.foodCountWithDirection(state,pos,action)
        directionWithRangeCount = self.foodCountWithDirection(state,pos,api.distanceLimited(food,state,DISTANCEASCLOSE))

        #mostly<1
        overallValue = directionCount/len(food) + directionWithRangeCount/16
        return overallValue

    def foodCountWithDirection(self,pos,action,foods):
        count = 0
        for food in foods:
            if (action == Directions.NORTH and food[1]>=pos[1] ):
                count += 1
            if (action == Directions.SOUTH and food[1]<=pos[1] ):
                count += 1
            if (action == Directions.WEST and food[0]<=pos[0] ):
                count += 1
            if (action == Directions.EAST and food[0]>=pos[0] ):
                count += 1
        return count







