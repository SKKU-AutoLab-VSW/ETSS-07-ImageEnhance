#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Base class for different label file handler. Each subclass handler is used
to load and dump labels from/to different file format such as: coco (.json),
yolo (.txt), pascal (.xml), ...
"""

from __future__ import annotations

import logging
from abc import ABCMeta
from abc import abstractmethod
from typing import Any

logger = logging.getLogger()


# MARK: - BaseLabelHandler

class BaseLabelHandler(metaclass=ABCMeta):
	"""The template for loading and dumping labels from/to different file
	formats.
	"""
	
	# MARK: Load
	
	@abstractmethod
	def load_from_file(self, image_path: str, label_path: str, **kwargs) -> Any:
		"""Load data from file.
		
		Args:
			image_path (str):
				The image filepath.
			label_path (str):
				The label filepath.
		"""
		pass
		
	# MARK: Dump
	
	@abstractmethod
	def dump_to_file(self, data: any, path: str, **kwargs):
		"""Dump data from object to file.

		Args:
			data (any):
				The data object.
			path (str):
				The label filepath to dump the data.
		"""
		pass
