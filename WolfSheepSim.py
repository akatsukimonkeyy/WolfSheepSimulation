#WolfSheepSim.py



import math
import random
import pygame


WIDTH = 600
HEIGHT = 600
ROWS = 20
COLUMNS = 20
SQ_WIDTH = WIDTH//COLUMNS
SQ_HEIGHT = HEIGHT//ROWS
FPS = 30

#1. Reproduction
#2. Grass
#3. Eating function
#4. AI Finding grass


#Object-oriented programming (OOP)
#Inheritance - when some class inherits behaviors and features from
#another class.
class GridSquare(pygame.sprite.Sprite):
    #Deriving a new class from the base class Sprite
    def __init__(self, color, width, height):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()

class Grass(GridSquare):
    #IMAGES = ["grass0", "grass1", "grass2"]
    MAX_GRAZES = 5
    MIN_GRAZES = 0
    COLORS = [(96, 75, 9), (81, 100, 9), (58, 100, 9), (34, 111, 9), (48, 131, 11), (88, 174, 15)]
    REFRESH_TIME = FPS * 3
    def __init__(self, row, col, width, height):
        self.grazes_left = random.randint(self.MIN_GRAZES, self.MAX_GRAZES)
        super().__init__(self.COLORS[self.grazes_left], width, height)
        self.rect.x = col*width
        self.rect.y = row*height
        self.time_since_regrowth = random.randint(0, self.REFRESH_TIME)

    def update(self):
        if self.grazes_left >= self.MAX_GRAZES:
            return
        #increase time_since_regrowth by 1
        self.time_since_regrowth += 1
        #if that number becomes larger than REFRESH_TIME, add one to grazes_left
        if self.time_since_regrowth > self.REFRESH_TIME:
            self.grazes_left += 1
            self.time_since_regrowth = 0
            #change the color of self.image
            self.update_color()

    def update_color(self):
        self.image.fill(self.COLORS[self.grazes_left])


class Animal(GridSquare):
    MAX_ENERGY = 1000 #energy decrease when the animal moves, energy increase when animal rests
    MAX_HUNGER = 1000 #hunger decreases every frame, hunger increases when we eat
    REST_ENERGY_GAIN = 10
    MOVE_HUNGER_LOSS = 5
    DECAY_TIME = FPS * 10
    GROW_TIME = FPS * 1
    MATING_COOLDOWN = FPS * 1
    #STATES
    THINKING = 0 #deciding what to do next
    RESTING = 1 #gaining energy
    MOVING = 2 #losing more hunger and energy; moving toward some goal (destination)
    EATING = 3 #gaining hunger
    MATING = 4 #have a baby animal

    def __init__(self, x, y, width, height, color, mate_group, image=None):
        super().__init__(color, width, height)
        if image is not None: #an image has been provided
            self.image = image
        self.rect.x = x
        self.rect.y = y
        self.speed = 5
        self.energy = self.MAX_ENERGY
        self.hunger = self.MAX_HUNGER
        self.destination = None #where we want to move
        self.state = self.THINKING #deciding what to do next
        self.actions = [self.think, self.rest, self.move, self.eat, self.mate]
        self.alive = True
        self.grow = 0
        self.decay = 0
        self.sex = random.choice(["M", "F"])
        self.can_mate = False
        self.mating_cooldown = 0
        self.mate_group = mate_group

    def think(self):
        # what should be the sheep's priority?
        # 1. Avoiding immediate danger
        if self.nearby_danger():
            return
            self.state = self.MOVING
        # 2. Keeping hunger value high (above 60%)
        elif self.is_hungry():
            if self.nearby_food():
                self.state = self.EATING
            else:
                self.find_food()
                self.state = self.MOVING
        # 3. Keeping energy value high (above 60%)
        elif self.energy < 0.6 * self.MAX_ENERGY:
            self.state = self.RESTING
        # 4. Mating/reproducing
        elif self.can_mate:
            if self.nearby_mate():
                self.state = self.MATING
            else:
                self.find_mate()
                self.state = self.MOVING
        # 5. Rest/Eat - nothing else to do so rest/eat
        else:
            self.state = random.choice([self.EATING, self.RESTING, self.MOVING])
            if self.state == self.MOVING:
                self.set_random_destination()

    def is_hungry(self):
        return self.hunger < 0.6 * self.MAX_HUNGER

    def nearby_food(self):
        return False #Override this in the child class

    def find_food(self):
        pass #Override this in the child class

    def move(self):
        if self.destination is None:
            self.state = self.THINKING
            return
        dest_x = self.destination[0]
        dest_y = self.destination[1]
        delta_x = dest_x - self.rect.x
        delta_y = dest_y - self.rect.y
        dist = math.sqrt(delta_x**2 + delta_y**2)
        if dist < self.speed: #don't overshoot the destination
            self.rect.x = dest_x
            self.rect.y = dest_y
            self.state = self.THINKING
            self.destination = None
        else:
            moves = dist/self.speed
            self.rect.move_ip(delta_x/moves, delta_y/moves)
        self.energy -= self.speed
        self.hunger -= self.MOVE_HUNGER_LOSS

    def nearby_danger(self):
        #TODO: when we add wolves - avoid them
        self.wolf_group = pygame.sprite.Group()
        close_wolf = pygame.sprite.spritecollide(self, self.wolf_group, False,
                                                  pygame.sprite.collide_rect_ratio(3))

        for wolf in close_wolf:
            close_wolves = []
            close_wolves.append(wolf)

            self.destination = random.choice(close_wolves).rect.center - 5
            if len(close_wolves) == 0:
                self.state = self.THINKING
            return
        return False

    def nearby_mate(self):
        #check to see if any collisions with any other object mate_group
        for mate in pygame.sprite.spritecollide(self, self.mate_group, False):
            if mate.sex != self.sex and mate.can_mate:
                return True
        return False

    def find_mate(self):
        for mate in pygame.sprite.spritecollide(self, self.mate_group, False,
                                                pygame.sprite.collide_rect_ratio(5)):
            if mate.sex != self.sex and mate.can_mate:
                #check a radius of about 5 squares and then set the destination
                #to the halfway point between itself and that mate
                self.destination = (self.rect.x + (mate.rect.x-self.rect.x)/2,
                                    self.rect.y + (mate.rect.y-self.rect.y)/2)
                return
        self.set_random_destination() # move randomly

    def eat(self):
        pass #Override this in the child class

    #regain some energy
    def rest(self):
        self.energy += self.REST_ENERGY_GAIN
        if self.energy >= self.MAX_ENERGY:
            self.energy = self.MAX_ENERGY
            self.state = self.THINKING
        elif self.nearby_danger() or self.is_hungry():
            self.state = self.THINKING

    def mate(self):
        mate_group = self.mate_group
        self.state = self.THINKING
        for mate in pygame.sprite.spritecollide(self, mate_group, False):
            if mate.sex != self.sex and mate.can_mate and self.can_mate:
                self.mating_cooldown = 0
                self.can_mate = False
                self.energy -= 50
                self.hunger -= 50
                mate.mating_cooldown = 0
                mate.can_mate = False
                mate.energy -= 50
                mate.hunger -= 50
                return True
        return False



    #this is called once every frame
    def update(self):
        if not self.alive:
            self.decay += 1
            if self.DECAY_TIME == self.decay:
                self.kill() #sprite function, kill() - removes sprite from every group
                #TODO: replenish nearby grass
            return

        if self.energy < 0 or self.hunger < 0:
            self.alive = False
            self.image.fill("black")
            return

        self.energy -= 1
        self.hunger -= 1
        #grow a little bit if not at max size
        if self.rect.width < SQ_WIDTH:
            self.grow += 1
            if self.grow == self.GROW_TIME:
                self.grow = 0
                self.rect.inflate_ip(1, 1) #adds 1 to the width and height
                self.image = pygame.transform.scale(self.image, self.rect.size) #updates the graphic
        else: #full size
            if self.mating_cooldown == self.MATING_COOLDOWN:
                self.can_mate = True
            else:
                self.mating_cooldown += 1
        self.actions[self.state]()
        #print("Energy: ", self.energy, "Hunger: ", self.hunger, "Action: ", self.state)

    def set_random_destination(self):
        #generate a destination within 1 SQUARE_WIDTH, SQUARE HEIGHT
        #of the current position; make sure in bounds
        random_x = self.rect.x + random.uniform(-SQ_WIDTH, SQ_WIDTH)
        random_y = self.rect.y + random.uniform(-SQ_HEIGHT, SQ_HEIGHT)
        if random_x < 0:
            random_x = 0
        elif random_x > WIDTH:
            random_x = WIDTH
        if random_y < 0:
            random_y = 0
        elif random_y > HEIGHT:
            random_y = HEIGHT
        self.destination = (random_x, random_y)

class Sheep(Animal):
    HUNGER_GAIN_FROM_GRASS = 30

    def __init__(self, x, y, width, height, grass_group, sheep_group, image=None):
        Animal.__init__(self, x, y, width, height, "white", sheep_group, image)
        self.grass_group = grass_group
        if self.sex == "M":
            self.image.fill(0xB4F0DC)

    def eat(self):
        #self refers to the Sheep Sprite
        grass_collide = pygame.sprite.spritecollide(self, self.grass_group, False)
        for grass in grass_collide:
            if self.graze(grass):
                self.hunger += self.HUNGER_GAIN_FROM_GRASS
                if self.hunger > self.MAX_HUNGER:
                    self.hunger = self.MAX_HUNGER
                break #only eat one square per frame
        self.state = self.THINKING

    def find_food(self):
        close_grass = pygame.sprite.spritecollide(self, self.grass_group, False,
                                                  pygame.sprite.collide_rect_ratio(3))
        #out of all the squares that are within (3), find the maximum (the best)
        best_so_far = 0
        best_grass = []
        for grass in close_grass:
            if grass.grazes_left > best_so_far:
                best_so_far = grass.grazes_left
                best_grass = [] #empty the list
                best_grass.append(grass)
            elif grass.grazes_left == best_so_far:
                best_grass.append(grass)

        if best_so_far == 0:
            self.set_random_destination()
        else:
            grass = random.choice(best_grass)
            self.destination = (grass.rect.x, grass.rect.y)

    def nearby_food(self):
        #look at the grass you're colliding with and see if any have grazes left
        collided_grass = pygame.sprite.spritecollide(self, self.grass_group, False)
        for grass in collided_grass:
            if grass.grazes_left > 0:
                return True
        return False

    def graze(self, grass):
        if grass.grazes_left > 0: #eating the grass
            grass.grazes_left -= 1
            grass.update_color()
            return True
        return False



    def mate(self):
        if super().mate(): #calls Animal.mate()
            baby = Sheep(self.rect.x, self.rect.y, 0.25*SQ_WIDTH, 0.25*SQ_HEIGHT,
                         self.grass_group, self.mate_group)
            self.mate_group.add(baby)

class Wolf(Animal):
    HUNGER_GAIN_FROM_SHEEP = 30

    def __init__(self, x, y, width, height, sheep_group, wolf_group, image=None):
        Animal.__init__(self, x, y, width, height, "red", wolf_group, image)
        self.wolf_group = wolf_group
        self.sheep_group = sheep_group
        if self.sex == "M":
            self.image.fill("blue")

    def eat(self):
        # self refers to the wolf Sprite
        sheep_collide = pygame.sprite.spritecollide(self, self.sheep_group, False)
        for sheep in sheep_collide:
            sheep.alive = False
            if not sheep.alive:
                self.hunger += 15
                self.hunger += self.HUNGER_GAIN_FROM_SHEEP
                if self.hunger > self.MAX_HUNGER:
                    self.hunger = self.MAX_HUNGER
            else:
                if sheep.alive == True:
                    return
                break  # only eat one square per frame

        self.state = self.THINKING

    def find_food(self):
        while True:
            close_sheep = pygame.sprite.spritecollide(self, self.sheep_group, False,
                                                      pygame.sprite.collide_rect_ratio(7))
            for sheep in close_sheep:
                best_sheep = []
                best_sheep.append(sheep)

                self.destination = random.choice(best_sheep).rect.center
                if len(best_sheep) == 0:
                    self.state = self.THINKING
                return

            self.state = self.THINKING

    def nearby_food(self):
        sheep_collide = pygame.sprite.spritecollide(self, self.sheep_group, False)
        for sheep in sheep_collide:
            sheep.alive = False
            Wolf.find_food(self)
            return True
        return False

    # def graze(self, sheep):
    #     if sheep.grazes_left > 0:  # eating the grass
    #         sheep.grazes_left -= 1
    #         sheep.update_color()
    #         return True
    #     return False

    def mate(self):
        if super().mate():  # calls Animal.mate()
            baby = Wolf(self.rect.x, self.rect.y, 0.25 * SQ_WIDTH, 0.25 * SQ_HEIGHT,
                         self.wolf_group, self.mate_group)
            self.mate_group.add(baby)




def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    running = True
    grass_group = pygame.sprite.Group()
    sheep_group = pygame.sprite.Group()
    wolf_group = pygame.sprite.Group()

    num_sheep = 35 #15 sheep initially
    #randomly place 15 different sheep onto the map
    for i in range(num_sheep):
        scale_factor = random.uniform(0.25, 1)
        sheep = Sheep(random.uniform(0, WIDTH-SQ_WIDTH), random.uniform(0, HEIGHT-SQ_HEIGHT),
                      scale_factor*SQ_WIDTH, scale_factor*SQ_HEIGHT, grass_group, sheep_group)
        sheep.add(sheep_group)

    num_wolf = int(num_sheep/3)
    for i in range(num_wolf):
        scale_factor = random.uniform(0.25, 1)
        wolf = Wolf(random.uniform(0, WIDTH-SQ_WIDTH), random.uniform(0, HEIGHT-SQ_HEIGHT), scale_factor*SQ_WIDTH, scale_factor*SQ_HEIGHT, sheep_group, wolf_group)
        wolf.add(wolf_group)

    #Create the grid of grass squares.
    #For each square in the grid, there is 50% chance
    #that there is grass on that square.
    grow_factor = 0.80
    for row in range(ROWS):
        for col in range(COLUMNS):
            if random.uniform(0, 1) < grow_factor:
                grass = Grass(row, col, SQ_WIDTH, SQ_HEIGHT)
                grass.add(grass_group)

    mouse_x = 0
    mouse_y = 0 #temporary for testing
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x = event.pos[0]
                mouse_y = event.pos[1]
        screen.fill("dark gray")
        sheep_group.update() #update all the sheep
        grass_group.update()
        wolf_group.update()

        grass_group.draw(screen) #draw grass
        sheep_group.draw(screen) #draw all the sheep
        wolf_group.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()

if __name__ == '__main__':
    main()
