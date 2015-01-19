import time
import shutil
import os
import glob

from numpy import asarray, array, vstack, hstack, size, random, argsort, ones, argmin, sin, cos, pi
from scipy.spatial.distance import cdist
from sklearn.datasets import make_blobs

from demo.base import StreamingDemo
from demo.util import loadrecent

class StreamingKMeans(StreamingDemo):

	def params(self, ncenters=3, ndims=2, std=0.2, seed=None, update='drift'):

		random.seed(seed)
		centers = random.randn(ncenters, ndims) * 2
		self.centers = asarray(centers)
		self.ncenters = ncenters
		self.ndims = ndims
		self.std = std
		self.update = update

		return self

	def run(self, lgn=None):

		viz = None

		closestpoint = lambda centers, p: argmin(cdist(centers, array([p])))

		centers = self.centers.copy()
		modeltime = 0
		model = []
		
		# loop over batches
		for i in range(0, self.nbatches):
			
			# drift means the points will slowly drift by adding noise to the position
			if self.update == 'drift':
				centers = centers + random.randn(centers.shape[0], centers.shape[1]) * 0.2

			# jump means every 15 batches the points will shift
			if self.update == 'jump':
				if i % 15 == 0:
					base = random.rand(self.ncenters * self.ndims) * 1 + 2
					delta = asarray([-d if random.rand() > 0.5 else d for d in base]).reshape(self.ncenters, self.ndims)
					centers = centers + delta

			# generate the points by sampling from the clusters and write to disk
			npoints = self.npoints
			pts, labels = make_blobs(npoints, self.ndims, centers, cluster_std=self.std)
			self.writepoints(pts, i)
			time.sleep(1)

			# get the latest model (after waiting)
			model, modeltime = loadrecent(self.dataout + '/*-model.txt', modeltime, model)

			# plot an update (if we got a valid model)
			if len(model) == self.ncenters:

			 	clrs = labels
			 	order = argsort(labels)
			 	clrs = clrs[order]
			 	pts = pts[order]
			 	s = ones(self.npoints) * 10
 				
 				if self.ndims == 1:
			 		pts = vstack((pts, model[:,None]))
			 	else:
			 		pts = vstack((pts, model))
			 	clrs = hstack((clrs, ones(self.ncenters) * 5))
			 	s = hstack((s, ones(self.ncenters) * 10))

			 	# wait a few iterations before plotting
				if (lgn is not None) & (i > 5):

					# scatter plot for two dimensions
					if self.ndims == 2:
						if viz is None:
	 		 				viz = lgn.scatterstreaming(pts[:,0], pts[:,1], label=clrs, size=s)
						else:
	 						viz.append(pts[:,0], pts[:,1], label=clrs, size=s)
	 				
	 				# line plot for one dimension
	 				elif self.ndims == 1:
	 					if viz is None:
	 						viz = lgn.linestreaming(pts, label=clrs, size=s/2)
	 					else:
	 						viz.append(pts, label=clrs, size=s/2)

	 				else:
	 					raise Exception('Plotting only supported with 2 or 3 dimensions')