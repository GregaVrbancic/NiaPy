# encoding=utf8
# pylint: disable=mixed-indentation, line-too-long, bad-continuation, multiple-statements, singleton-comparison, unused-argument, no-self-use, trailing-comma-tuple, logging-not-lazy, no-else-return
"""Implementation of benchmarks utility function."""
import logging
from numpy import ndarray, asarray, full, inf, dot, where, random as rnd
from matplotlib import pyplot as plt, animation as anim
from . import Rastrigin, Rosenbrock, Griewank, Sphere, Ackley, Schwefel, Schwefel221, Schwefel222, Whitley, Alpine1, Alpine2, HappyCat, Ridge, ChungReynolds, Csendes, Pinter, Qing, Quintic, Salomon, SchumerSteiglitz, Step, Step2, Step3, Stepint, SumSquares, StyblinskiTang, BentCigar, Discus, Elliptic, ExpandedGriewankPlusRosenbrock, HGBat, Katsuura, ExpandedScaffer, ModifiedSchwefel, Weierstrass

logging.basicConfig()
logger = logging.getLogger('NiaPy.benchmarks.utility')
logger.setLevel('INFO')

__all__ = ['Utility', 'Task', 'TaskConvPrint', 'TaskConvPlot']

class Utility:
	def __init__(self):
		self.classes = {
			'ackley': Ackley,
			'alpine1': Alpine1,
			'alpine2': Alpine2,
			'bentcigar': BentCigar,
			'chungReynolds': ChungReynolds,
			'csendes': Csendes,
			'discus': Discus,
			'conditionedellptic': Elliptic,
			'elliptic': Elliptic,
			'expandedgriewankplusrosenbrock': ExpandedGriewankPlusRosenbrock,
			'expandedscaffer': ExpandedScaffer,
			'griewank': Griewank,
			'happyCat': HappyCat,
			'hgbat': HGBat,
			'katsuura': Katsuura,
			'modifiedscwefel': ModifiedSchwefel,
			'pinter': Pinter,
			'qing': Qing,
			'quintic': Quintic,
			'rastrigin': Rastrigin,
			'ridge': Ridge,
			'rosenbrock': Rosenbrock,
			'salomon': Salomon,
			'schumerSteiglitz': SchumerSteiglitz,
			'schwefel': Schwefel,
			'schwefel221': Schwefel221,
			'schwefel222': Schwefel222,
			'sphere': Sphere,
			'step': Step,
			'step2': Step2,
			'step3': Step3,
			'stepint': Stepint,
			'styblinskiTang': StyblinskiTang,
			'sumSquares': SumSquares,
			'weierstrass': Weierstrass,
			'whitley': Whitley
		}

	def get_benchmark(self, benchmark):
		r"""Get the optimization problem.

		Arguments:
		benchmark {string} or {class} -- String or class that represent the optimization problem
		"""
		if not isinstance(benchmark, str) and not callable(benchmark): return benchmark
		elif benchmark in self.classes:	return self.classes[benchmark]()
		raise TypeError('Passed benchmark is not defined!')

	@classmethod
	def __raiseLowerAndUpperNotDefined(cls): raise TypeError('Upper and Lower value must be defined!')

class Task(Utility):
	def __init__(self, D, nFES, nGEN, benchmark=None, o=None, fo=None, M=None, fM=None, optF=None):
		r"""Initialize task class for optimization.

		Arguments:
		D {integer} -- Number of dimensions
		nFES {integer} -- Number of function evaluations
		nGEN {integer} -- Number of generation or iterations
		benchmark {class} or {string} -- Problem to solve
		o {array} -- Array for shifting
		of {function} -- Function applied on shifted input
		M {matrix} -- Matrix for rotating
		fM {function} -- Function applied after rotating
		optF {real} -- Value added to benchmark function return
		"""
		super(Task, self).__init__()
		self.benchmark = self.get_benchmark(benchmark) if benchmark != None else None
		self.D = D  # dimension of the problem
		self.Iters, self.nGEN = 0, nGEN if nGEN != None else 10000
		self.Evals, self.nFES = 0, nFES
		self.Fun = self.benchmark.function() if benchmark != None else None
		self.o = o if isinstance(o, ndarray) or o == None else asarray(o)
		self.M = M if isinstance(M, ndarray) or M == None else asarray(M)
		self.fo, self.fM, self.optF = fo, fM, optF
		self.__initBounds()

	def __initBounds(self):
		Lower, Upper = self.benchmark.Lower, self.benchmark.Upper
		if isinstance(Lower, (int, float)): self.Lower = full(self.D, Lower)
		else: self.Lower = Lower if isinstance(Lower, ndarray) else asarray(Lower)
		if isinstance(Upper, (int, float)): self.Upper = full(self.D, Upper)
		else: self.Upper = Upper if isinstance(Upper, ndarray) else asarray(Upper)
		self.bRange = self.Upper - self.Lower

	def stopCond(self):
		r"""Check if stoping condition reached."""
		return self.Evals >= self.nFES or (False if self.nGEN == None else self.Iters >= self.nGEN)

	def stopCondI(self):
		r"""Check if stoping condition reached and incrise number of iterations."""
		r = self.Evals >= self.nFES or (False if self.nGEN == None else self.Iters >= self.nGEN)
		self.Iters += 1
		return r

	def eval(self, A):
		r"""Evaluate the solution A.

		Arguments:
		A {array} -- Solution to evaluate
		"""
		if self.stopCond() or not self.isFeasible(A): return inf
		self.Evals += 1
		X = A - self.o if self.o != None else A
		X = self.fo(X) if self.fo != None else X
		X = dot(X, self.M) if self.M != None else X
		X = self.fM(X) if self.fM != None else X
		return self.Fun(self.D, X) + (self.optF if self.optF != None else 0)

	def nextIter(self):
		r"""Increase the number of generation/iterations of algorithms main loop."""
		self.Iters += 1

	def isFeasible(self, A):
		r"""Check if the solution is in bounds and is feasible.

		Arguments:
		A {array} -- Solution to check
		"""
		return (False if True in (A < self.Lower) else True) and (False if True in (A > self.Upper) else True)

	def repair(self, x):
		r"""Repair solution and put the solution in the random position inside of the bounds of problem.

		Arguments:
		x {array}
		"""
		ir = where(x > self.Upper)
		x[ir] = rnd.uniform(self.Lower[ir], self.Upper[ir])
		ir = where(x < self.Lower)
		x[ir] = rnd.uniform(self.Lower[ir], self.Upper[ir])
		return x

class TaskConvPrint(Task):
	def __init__(self, **kwargs):
		super(TaskConvPrint, self).__init__(**kwargs)
		self.x, self.x_f = None, inf

	def eval(self, A):
		x_f = super(TaskConvPrint, self).eval(A)
		if x_f < self.x_f:
			self.x, self.x_f = A, x_f
			logger.info('nFES:%d nGEN:%d => %s -> %s' % (self.Evals, self.Iters, self.x, self.x_f))
		return x_f

class TaskConvPlot(Task):
	def __init__(self, **kwargs):
		super(TaskConvPlot, self).__init__(**kwargs)
		self.x_fs, self.iters = list(), list()
		self.fig = plt.figure()
		self.ax = self.fig.subplots(nrows=1, ncols=1)
		self.ax.set_xlim(0, self.nFES)
		self.line, = self.ax.plot(self.iters, self.x_fs, animated=True)
		self.ani = anim.FuncAnimation(self.fig, self.updatePlot, blit=True)
		self.showPlot()

	def eval(self, A):
		x_f = super(TaskConvPlot, self).eval(A)
		if not self.x_fs: self.x_fs.append(x_f)
		elif x_f < self.x_fs[-1]: self.x_fs.append(x_f)
		else: self.x_fs.append(self.x_fs[-1])
		self.iters.append(self.Evals)
		return x_f

	def showPlot(self):
		plt.show(block=False)
		plt.pause(0.001)

	def updatePlot(self, frame):
		if self.x_fs:
			maxx_fs, minx_fs = self.x_fs[0], self.x_fs[-1]
			self.ax.set_ylim(minx_fs + 1, maxx_fs + 1)
		self.line.set_data(self.iters, self.x_fs)
		return self.line,

# vim: tabstop=3 noexpandtab shiftwidth=3 softtabstop=3
