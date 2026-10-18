import random

POPULATION_SIZE = 100
GENOME_LENGTH = 20
MUTATION_RATE = 0.01
CROSSOVER_RATE = 0.7
GENERATIONS = 200

def random_genome(length):
    return [random.randint(0,1) for _ in range(length)]

def init_population(population_size, genome_length)