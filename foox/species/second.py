"""
This module encapsulates the behaviour of second species counterpoint.
"""
import random

import foox.ga as ga
from utils import is_parallel, make_generate_function, is_stepwise_motion


# Some sane defaults.
DEFAULT_POPULATION_SIZE = 1000
DEFAULT_MAX_GENERATION = 200
DEFAULT_MUTATION_RANGE = 7
DEFAULT_MUTATION_RATE = 0.2

# Intervals between notes that are allowed in second sepcies counterpoint.
CONSONANCES = [2, 4, 5, 7, 9, 11]
DISSONANCES = [3, 6, 8, 10]
VALID_FIRST_BEAT_INTERVALS = CONSONANCES
VALID_THIRD_BEAT_INTERVALS = CONSONANCES + DISSONANCES

# Various rewards and punishments used with different aspects of the solution.

# Reward / punishment to ensure the solution starts correctly (5th or 8ve).
REWARD_FIRST = 2
PUNISH_FIRST = 0.7
# Reward / punishment to ensure the solution finishes correctly (at an 8ve).
REWARD_LAST = 4
PUNISH_LAST = 0.7
# Reward / punishment to ensure the penultimate note is step wise onto the
# final note.
REWARD_LAST_STEP = 2
PUNISH_LAST_STEP = 0.7
# Reward / punish contrary motion onto the final note.
REWARD_LAST_MOTION = 3
PUNISH_LAST_MOTION = 0.7
# Punishment if the penultimate note is a repeated note.
PUNISH_REPEATED_PENULTIMATE = 0.5
# Make sure the movement to the penultimate note isn't from too
# far away (not greater than a third).
REWARD_PENULTIMATE_PREPARATION = 1
PUNISH_PENULTIMATE_PREPARATION = 0.7
# Punish parallel fifths or octaves.
PUNISH_PARALLEL_FIFTHS_OCTAVES = 0.7
# Punishment for too many parallel/similar movements.
PUNISH_PARALLEL = 0.2
# Reward / punish correct stepwise movement around dissonances.
REWARD_STEPWISE_MOTION = 2
PUNISH_STEPWISE_MOTION = 0.2
# Punishment for too many repeated notes.
PUNISH_REPEATS = 0.1
# Punishment for too many large leaps in the melody.
PUNISH_LEAPS = 0.1

# The highest score a candidate solution may achieve. (Hack!)
MAX_REWARD = (REWARD_FIRST + REWARD_LAST + REWARD_LAST_STEP +
    REWARD_LAST_MOTION + REWARD_PENULTIMATE_PREPARATION)


def create_population(number, cantus_firmus):
    """
    Will create a new list of random candidate solutions of the specified
    number given the context of the cantus_firmus.
    """
    result = []
    for i in range(number):
        new_chromosome = []
        for note in cantus_firmus:
            valid_first_beat_range = [interval for interval in
                VALID_FIRST_BEAT_INTERVALS if (interval + note) < 17]
            valid_third_beat_range = [interval for interval in
                VALID_THIRD_BEAT_INTERVALS if (interval + note) < 17]
            first_beat_interval = random.choice(valid_first_beat_range)
            third_beat_interval = random.choice(valid_third_beat_range)
            new_chromosome.append(note + first_beat_interval)
            new_chromosome.append(note + third_beat_interval)
        # Remove the last minim since it's surplus to requirements.
        genome = Genome(new_chromosome[:-1])
        result.append(genome)
    return result


def make_fitness_function(cantus_firmus):
    """
    Given the cantus firmus, will return a function that takes a single Genome
    instance and returns a fitness score.
    """

    # Melody wide measures.
    repeat_threshold = len(cantus_firmus) * 0.5
    jump_threshold = len(cantus_firmus) * 0.3
    def fitness_function(genome):
        """
        Given a candidate solution will return its fitness score assuming
        the cantus_firmus in this closure. Caches the fitness score in the
        genome.
        """
        # Save some time!
        if genome.fitness is not None:
            return genome.fitness

        # The fitness score to be returned.
        fitness_score = 0.0
        # Counts the number of repeated notes.
        repeats = 0
        # Counts the amount of parallel motion.
        parallel_motion = 0
        # Counts the number of jumps in the melodic contour.
        jump_contour = 0

        contrapunctus = genome.chromosome

        # Make sure the solution starts correctly (at a 5th or octave).
        first_interval = contrapunctus[0] - cantus_firmus[0]
        if first_interval == 7 or first_interval == 4:
            fitness_score += REWARD_FIRST
        else:
            fitness_score -= PUNISH_FIRST

        # Make sure the solution finishes correctly (at an octave).
        if contrapunctus[-1] - cantus_firmus[-1] == 7:
            fitness_score += REWARD_LAST
        else:
            fitness_score -= PUNISH_LAST

        # Ensure the penultimate note is step wise onto the final note.
        if abs(contrapunctus[-1] - contrapunctus[-2]) == 1:
            fitness_score += REWARD_LAST_STEP
        else:
            fitness_score -= PUNISH_LAST_STEP

        # Reward contrary motion onto the final note.
        cantus_firmus_motion = cantus_firmus[-1] - cantus_firmus[-2]
        contrapunctus_motion = contrapunctus[-1] - contrapunctus[-2]

        if ((cantus_firmus_motion < 0 and contrapunctus_motion > 0) or
            (cantus_firmus_motion > 0 and contrapunctus_motion < 0)):
            fitness_score += REWARD_LAST_MOTION
        else:
            fitness_score -= PUNISH_LAST_MOTION

        # Make sure the penultimate note isn't a repeated note.
        penultimate_preparation = abs(contrapunctus[-2] - contrapunctus[-3])
        if penultimate_preparation == 0:
            fitness_score -= PUNISH_REPEATED_PENULTIMATE
        else:
            # Make sure the movement to the penultimate note isn't from too
            # far away (not greater than a third).
            if penultimate_preparation < 2:
                fitness_score += REWARD_PENULTIMATE_PREPARATION
            else:
                fitness_score -= PUNISH_PENULTIMATE_PREPARATION

        # Check the fitness of the body of the solution.
        last_notes = (contrapunctus[0], cantus_firmus[0])
        last_interval = last_notes[0] - last_notes[1]
        for i in range(1, len(contrapunctus)):
            contrapunctus_note = contrapunctus[i]
            cantus_firmus_note = cantus_firmus[i / 2]
            current_notes = (contrapunctus_note, cantus_firmus_note)
            current_interval = contrapunctus_note - cantus_firmus_note

            # Punish parallel fifths or octaves.
            if ((current_interval == 4 or current_interval == 7) and
                (last_interval == 4 or last_interval == 7)):
                fitness_score -= PUNISH_PARALLEL_FIFTHS_OCTAVES

            # Check for parallel motion.
            if is_parallel(last_notes, current_notes):
                parallel_motion += 1

            # Check if the melody is a repeating note.
            if contrapunctus_note == last_notes[0]:
                repeats += 1

            # Check the melodic contour.
            contour_leap = abs(current_notes[0] - last_notes[0])
            if contour_leap >= 2:
                jump_contour += contour_leap - 2

            # Ensure dissonances are part of a step-wise movement.
            if i % 2 and current_interval in DISSONANCES:
                # The current_note is a dissonance on the third beat of a bar.
                # Check that both the adjacent notes are only a step away.
                if is_stepwise_motion(contrapunctus, i):
                    fitness_score += REWARD_STEPWISE_MOTION
                else:
                    fitness_score -= PUNISH_STEPWISE_MOTION

            last_notes = current_notes
            last_interval = current_interval

        # Punish too many (> 1/3) repeated notes.
        if repeats > repeat_threshold:
            fitness_score -= PUNISH_REPEATS

        # Punish too many (> 1/3) parallel movements.
        if parallel_motion > repeat_threshold:
            fitness_score -= PUNISH_PARALLEL

        # Punish too many large leaps in the melody.
        if jump_contour > jump_threshold:
            fitness_score -= PUNISH_LEAPS

        genome.fitness = fitness_score

        return fitness_score

    return fitness_function


def make_halt_function(cantus_firmus):
    """
    Returns a halt function for the given cantus firmus.
    """

    def halt(population, generation_count):
        """
        Given a population of candidate solutions and generation count (the
        number of epochs the algorithm has run) will return a boolean to
        indicate if an acceptable solution has been found within the
        referenced population.
        """
        fittest = population[0]
        max_fitness = MAX_REWARD
        for i in range(len(fittest.chromosome)):
            # Check for dissonances. Each dissonance should have incremented
            # the fitness because it has been "placed" correctly.
            cantus_firmus_note = cantus_firmus[i / 2]
            melody_note = fittest.chromosome[i]
            interval = melody_note - cantus_firmus_note
            if interval in DISSONANCES:
                max_fitness += REWARD_STEPWISE_MOTION

        return (fittest.fitness >= max_fitness or
            generation_count > DEFAULT_MAX_GENERATION)

    return halt


class Genome(ga.Genome):
    """
    A class to represent a candidate solution for second species counterpoint.
    """

    def mutate(self, mutation_range, mutation_rate, context):
        """
        Mutates the genotypes no more than the mutation_range depending on the
        mutation_rate given and the cantus_firmus passed in as the context (to
        ensure the mutation is valid).
        """
        first_beat_mutation_intervals = [interval for interval in
            VALID_FIRST_BEAT_INTERVALS if interval <= mutation_range]
        third_beat_mutation_intervals = [interval for interval in
            VALID_THIRD_BEAT_INTERVALS if interval <= mutation_range]
        for locus in range(len(self.chromosome)):
            if mutation_rate >= random.random():
                cantus_firmus_note = context[locus / 2]
                if locus % 2:
                    # Current melody note is on the third beat of the bar
                    mutation_intervals = third_beat_mutation_intervals
                else:
                    # Current melody note is on the first beat of the bar.
                    mutation_intervals = first_beat_mutation_intervals
                valid_mutation_range = [interval for interval in
                    mutation_intervals if
                    (interval + cantus_firmus_note) < 17]
                mutation = random.choice(valid_mutation_range)
                new_allele = cantus_firmus_note + mutation
                self.chromosome[locus] = new_allele
                # Resets fitness score
                self.fitness = None
