#    This file is part of EAP.
#
#    EAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    EAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with EAP. If not, see <http://www.gnu.org/licenses/>.

import random
import operator
import math

from eap import base
from eap import creator
from eap import gp
from eap import operators
from eap import toolbox

# Define new functions
def safeDiv(left, right):
    try:
        return left / right
    except ZeroDivisionError:
        return 0

adfset2 = gp.PrimitiveSet("ADF2", 2)
adfset2.addPrimitive(operator.add, 2)
adfset2.addPrimitive(operator.sub, 2)
adfset2.addPrimitive(operator.mul, 2)
adfset2.addPrimitive(safeDiv, 2)
adfset2.addPrimitive(operator.neg, 1)
adfset2.addPrimitive(math.cos, 1)
adfset2.addPrimitive(math.sin, 1)

adfset1 = gp.PrimitiveSet("ADF1", 2)
adfset1.addPrimitive(operator.add, 2)
adfset1.addPrimitive(operator.sub, 2)
adfset1.addPrimitive(operator.mul, 2)
adfset1.addPrimitive(safeDiv, 2)
adfset1.addPrimitive(operator.neg, 1)
adfset1.addPrimitive(math.cos, 1)
adfset1.addPrimitive(math.sin, 1)
adfset1.addADF(adfset2)

adfset0 = gp.PrimitiveSet("ADF0", 2)
adfset0.addPrimitive(operator.add, 2)
adfset0.addPrimitive(operator.sub, 2)
adfset0.addPrimitive(operator.mul, 2)
adfset0.addPrimitive(safeDiv, 2)
adfset0.addPrimitive(operator.neg, 1)
adfset0.addPrimitive(math.cos, 1)
adfset0.addPrimitive(math.sin, 1)
adfset0.addADF(adfset1)
adfset0.addADF(adfset2)

pset = gp.PrimitiveSet("MAIN", 1)
pset.addPrimitive(operator.add, 2)
pset.addPrimitive(operator.sub, 2)
pset.addPrimitive(operator.mul, 2)
pset.addPrimitive(safeDiv, 2)
pset.addPrimitive(operator.neg, 1)
pset.addPrimitive(math.cos, 1)
pset.addPrimitive(math.sin, 1)
pset.addEphemeralConstant(lambda: random.randint(-1, 1))
pset.addADF(adfset0)
pset.addADF(adfset1)
pset.addADF(adfset2)
pset.renameArguments({"ARG0" : "x"})

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("ADF0", gp.PrimitiveTree, pset=adfset0)
creator.create("ADF1", gp.PrimitiveTree, pset=adfset1)
creator.create("ADF2", gp.PrimitiveTree, pset=adfset2)
creator.create("MAIN", gp.PrimitiveTree, pset=pset)

creator.create("Individual", list, fitness=creator.FitnessMin)

tools = toolbox.Toolbox()
tools.register('adf_expr0', gp.generateFull, pset=adfset0, min_=1, max_=2)
tools.register('adf_expr1', gp.generateFull, pset=adfset1, min_=1, max_=2)
tools.register('adf_expr2', gp.generateFull, pset=adfset2, min_=1, max_=2)
tools.register('main_expr', gp.generateRamped, pset=pset, min_=1, max_=2)

tools.register('ADF0', creator.ADF0, toolbox.Iterate(tools.adf_expr0))
tools.register('ADF1', creator.ADF1, toolbox.Iterate(tools.adf_expr1))
tools.register('ADF2', creator.ADF2, toolbox.Iterate(tools.adf_expr2))
tools.register('MAIN', creator.MAIN, toolbox.Iterate(tools.main_expr))

func_cycle = toolbox.FuncCycle([tools.MAIN, tools.ADF0, tools.ADF1, tools.ADF2])

tools.register('individual', creator.Individual, toolbox.Repeat(func_cycle, 4))
tools.register('population', list, toolbox.Repeat(tools.individual, 100))

def evalSymbReg(individual):
    # Transform the tree expression in a callable function
    func = tools.lambdify(expr=individual)
    # Evaluate the sum of squared difference between the expression
    # and the real function : x**4 + x**3 + x**2 + x
    values = (x/10. for x in xrange(-10, 10))
    diff_func = lambda x: (func(x)-(x**4 + x**3 + x**2 + x))**2
    diff = sum(map(diff_func, values))
    return diff,

tools.register('lambdify', gp.lambdifyList)
tools.register('evaluate', evalSymbReg)
tools.register('select', operators.selTournament, tournsize=3)
tools.register('mate', operators.cxTreeUniformOnePoint)
tools.register('expr', gp.generateFull, min_=1, max_=2)
tools.register('mutate', operators.mutTreeUniform, expr=tools.expr)

stats_t = operators.Stats(lambda ind: ind.fitness.values)
stats_t.register("Avg", operators.mean)
stats_t.register("Std", operators.std_dev)
stats_t.register("Min", min)
stats_t.register("Max", max)

def main():
    random.seed(1024)
    
    pop = tools.population()
    hof = operators.HallOfFame(1)
    stats = tools.clone(stats_t)
    
    CXPB, MUTPB, NGEN = 0.5, 0.2, 40
    
    # Evaluate the entire population
    for ind in pop:
    	ind.fitness.values = tools.evaluate(ind)

    hof.update(pop)
    stats.update(pop)    
    
    for g in range(NGEN):
        print "-- Generation %i --" % g
    
        # Select the offsprings
        offsprings = tools.select(pop, n=len(pop))
        # Clone the offsprings
        offsprings = [tools.clone(ind) for ind in offsprings]
    
        # Apply crossover and mutation
        for ind1, ind2 in zip(offsprings[::2], offsprings[1::2]):
            for tree1, tree2 in zip(ind1, ind2):
                if random.random() < CXPB:
                    tools.mate(tree1, tree2)
                    del ind1.fitness.values
                    del ind2.fitness.values

        for ind in offsprings:
            for tree in ind:
                if random.random() < MUTPB:
                    tools.mutate(tree)
                    del ind.fitness.values
                            
        # Evaluate the individuals with an invalid fitness
        invalids = [ind for ind in offsprings if not ind.fitness.valid]
        for ind in invalids:
            ind.fitness.values = tools.evaluate(ind)
                
        # Replacement of the population by the offspring
        pop[:] = offsprings
        hof.update(pop)
        stats.update(pop)
        for key, stat in stats.data.iteritems():
            print "  %s %s" % (key, stat[-1][0])
    
    print 'Best individual : ', gp.evaluate(hof[0][0]), hof[0].fitness
    
    return pop, stats, hof
    
if __name__ == "__main__":
    main()

