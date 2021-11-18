#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""End-to-End Enhancer.
"""

from __future__ import annotations

from abc import ABCMeta
from typing import Optional

import numpy as np
import torch
import torch.nn as nn

from torchkit.core.image import imshow_plt
from torchkit.core.runner import BaseModel
from torchkit.core.utils import ForwardXYOutput
from torchkit.core.utils import Images
from torchkit.core.utils import Indexes
from torchkit.core.utils import Tensors
from torchkit.core.utils import to_4d_array
from torchkit.models.builder import LOSSES
from torchkit.models.builder import METRICS


# MARK: - End2EndEnhancer

class End2EndEnhancer(BaseModel, metaclass=ABCMeta):
	"""End-to-End Enhancer is a base class for all end-to-end trainable image
	enhancement models. End-to-End means that the whole network can be trained
	end-to-end, without having to freeze some parts of the network during
	training.
	
	Usually, we add functions such as:
	- Define main components.
	- Forward pass with custom loss and metrics.
	- Result visualization.
	
	Attributes:
		backbone (nn.Module):
			The features module.
		neck (nn.Module, optional):
			The neck module. Default: `None`.
		head (nn.Module):
			The head module.
	"""

	# MARK: Magic Functions
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.backbone: Optional[nn.Module] = None
		self.neck	 : Optional[nn.Module] = None
		self.head	 : Optional[nn.Module] = None
		
	# MARK: Properties
	
	@property
	def with_backbone(self) -> bool:
		"""Return whether if the `backbone` has been defined."""
		return hasattr(self, "backbone") and self.backbone is not None
	
	@property
	def with_neck(self) -> bool:
		"""Return whether if the `neck` has been defined."""
		return hasattr(self, "neck") and self.neck is not None
	
	@property
	def with_head(self) -> bool:
		"""Return whether if the `head` has been defined."""
		return hasattr(self, "head") and self.head is not None
	
	# MARK: Forward Pass
	
	def forward_train(
		self, x: torch.Tensor, y: torch.Tensor, *args, **kwargs
	) -> ForwardXYOutput:
		"""Forward pass during training with both `x` and `y` are given.
		
		Args:
			x (torch.Tensor):
				The low-quality images of shape [B, C, H, W].
			y (torch.Tensor, optional):
				The high-quality images (a.k.a ground truth) of shape
				[B, C, H, W].

		Returns:
			y_hat (Tensors):
				The final predictions consisting of the enhanced image.
			metrics (Metrics, optional):
				- A dictionary with the first key must be the `loss`.
				- `None`, training will skip to the next batch.
		"""
		y_hat   = self.forward_infer(x=x, *args, **kwargs)
		metrics = {}
		if self.with_loss:
			metrics["loss"] = self.loss(y_hat, y)
		if self.with_metrics:
			ms 	    = {m.name: m(y_hat, y) for m in self.metrics}
			metrics = metrics | ms  	   # NOTE: 3.9+ ONLY
			# metrics = {**metrics, **ms}  # NOTE: 3.5+ ONLY
		metrics = metrics if len(metrics) else None
		return y_hat, metrics
	
	def forward_infer(self, x: torch.Tensor, *args, **kwargs) -> Tensors:
		"""Forward pass during inference with only `x` is given.

		Args:
			x (Tensors):
				The low-light images of shape [B, C, H, W].

		Returns:
			y_hat (Tensors):
				The final predictions consisting the enhanced images.
		"""
		y_hat = self.backbone(x)
		if self.with_neck:
			y_hat = self.neck(y_hat)
		if self.with_head:
			y_hat = self.head(y_hat)
		return y_hat
	
	def forward_features(
		self, x: torch.Tensor, out_indexes: Optional[Indexes] = None
	) -> Tensors:
		"""Forward pass for features extraction.

		Args:
			x (torch.Tensor):
				The input image.
			out_indexes (Indexes, optional):
				The list of layers' indexes to extract features. This is called
				in `forward_features()` and is useful when the model
				is used as a component in another model.
				- If is a `tuple` or `list`, return an array of features.
				- If is a `int`, return only the feature from that layer's index.
				- If is `-1`, return the last layer's output.
				Default: `None`.
		"""
		out_indexes = self.out_indexes if out_indexes is None else out_indexes
		assert self.with_backbone, f"`backbone` has not been defined."
		
		y_hat = []
		for idx, m in enumerate(self.backbone.children()):
			x = m(x)
			if isinstance(out_indexes, (tuple, list)) and (idx in out_indexes):
				y_hat.append(x)
			elif isinstance(out_indexes, int) and (idx == out_indexes):
				return x
			else:
				y_hat = x
		return y_hat
	
	# MARK: Visualization
	
	def show_results(
		self,
		y_hat		 : Images,
		x    		 : Optional[Images] = None,
		y    		 : Optional[Images] = None,
		filepath	 : Optional[str]    = None,
		image_quality: int              = 95,
		show         : bool             = False,
		show_max_n   : int              = 8,
		wait_time    : float            = 0.01,
		*args, **kwargs
	):
		"""Draw `result` over input image.

		Args:
			y_hat (Images):
				The enhanced images.
			x (Images, optional):
				The low quality images.
			y (Images, optional):
				The high quality images.
			filepath (str, optional):
				The file path to save the debug result.
			image_quality (int):
				The image quality to be saved. Default: `95`.
			show (bool):
				If `True` shows the results on the screen. Default: `False`.
			show_max_n (int):
				Maximum debugging items to be shown. Default: `8`.
			wait_time (float):
				Pause some times before showing the next image.
		"""
		# NOTE: Prepare images
		results = {}
		y_hat   = to_4d_array(y_hat)
		if x is not None:
			results["low"] = to_4d_array(x)
		if y is not None:
			results["high"] = to_4d_array(y)
		results["enhance"] = y_hat

		filepath = self.debug_image_filepath if filepath is None else filepath
		save_cfg = dict(filepath=filepath,
						pil_kwargs=dict(quality=image_quality))
		imshow_plt(images=results, scale=2, save_cfg=save_cfg, show=show,
				   show_max_n=show_max_n, wait_time=wait_time)
