import numpy as np
import MEGA as prin

def differential_evolution(pop_size, num_vars, lb, ub, num_generations, F, CR):
    # Initialize populationprin.fo
    population = np.random.uniform(lb, ub, (pop_size, num_vars))
    
    # Main loop
    for gen in range(num_generations):
        # Evaluate fitness
        fitness = np.apply_along_axis(prin.fo, 1, population)
        best_fitness = np.min(fitness)
        
        # Create offspring population
        offspring = np.zeros_like(population)
        for i in range(pop_size):
            # Select three distinct individuals from the population
            idx = np.random.choice(pop_size, 3, replace=False)
            x1, x2, x3 = population[idx]
            
            # Mutation
            v = x1 + F * (x2 - x3)
            
            # Crossover
            mask = np.random.rand(num_vars) < CR
            u = np.where(mask, v, population[i])
            
            # Selection
            if prin.fo(u) <= fitness[i]:
                offspring[i] = u
            else:
                offspring[i] = population[i]
        
        # Update population
        population = offspring
        
        if gen % 1000 == 0:
            # Display current best fitness
            print(f'Generation {gen}: Best Fitness = {best_fitness}')
    
    # Final evaluation
    final_fitness = np.apply_along_axis(prin.fo, 1, population)
    best_solution = population[np.argmin(final_fitness)]
    best_fitness = np.min(final_fitness)
    print(f'Final Best Fitness = {best_fitness}')
    print('Best Solution:')
    print(best_solution)

