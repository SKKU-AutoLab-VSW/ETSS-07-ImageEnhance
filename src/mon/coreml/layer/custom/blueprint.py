#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module implements Subspace Blueprint Separable Convolution layers.
"""

from __future__ import annotations

__all__ = [
    "ABSConv2dS", "ABSConv2dS1", "ABSConv2dS10", "ABSConv2dS11", "ABSConv2dS12",
    "ABSConv2dS13", "ABSConv2dS2", "ABSConv2dS3", "ABSConv2dS4", "ABSConv2dS5",
    "ABSConv2dS6", "ABSConv2dS7", "ABSConv2dS8", "ABSConv2dS9", "ABSConv2dU",
    "AttentionSubspaceBlueprintSeparableConv2d",
    "AttentionSubspaceBlueprintSeparableConv2d1",
    "AttentionSubspaceBlueprintSeparableConv2d10",
    "AttentionSubspaceBlueprintSeparableConv2d11",
    "AttentionSubspaceBlueprintSeparableConv2d12",
    "AttentionSubspaceBlueprintSeparableConv2d13",
    "AttentionSubspaceBlueprintSeparableConv2d2",
    "AttentionSubspaceBlueprintSeparableConv2d3",
    "AttentionSubspaceBlueprintSeparableConv2d4",
    "AttentionSubspaceBlueprintSeparableConv2d5",
    "AttentionSubspaceBlueprintSeparableConv2d6",
    "AttentionSubspaceBlueprintSeparableConv2d7",
    "AttentionSubspaceBlueprintSeparableConv2d8",
    "AttentionSubspaceBlueprintSeparableConv2d9",
    "AttentionUnconstrainedBlueprintSeparableConv2d", "BSConv2dS", "BSConv2dU",
    "SubspaceBlueprintSeparableConv2d", "UnconstrainedBlueprintSeparableConv2d",
]

from typing import Any, Callable

import torch
from torch import nn

from mon.coreml.layer import base
from mon.coreml.layer.typing import _size_2_t
from mon.foundation import math
from mon.globals import LAYERS


# region Blueprint Separable Convolution

@LAYERS.register()
class SubspaceBlueprintSeparableConv2d(base.ConvLayerParsingMixin, nn.Module):
    """Subspace Blueprint Separable Conv2d adopted from the paper: "Rethinking
    Depthwise Separable Convolutions: How Intra-Kernel Correlations Lead to
    Improved MobileNets".
    
    References:
        https://github.com/zeiss-microscopy/BSConv
    """
    
    def __init__(
        self,
        in_channels     : int,
        out_channels    : int,
        kernel_size     : _size_2_t,
        stride          : _size_2_t       = 1,
        padding         : _size_2_t | str = 0,
        dilation        : _size_2_t       = 1,
        groups          : int             = 1,
        bias            : bool            = True,
        padding_mode    : str             = "zeros",
        device          : Any             = None,
        dtype           : Any             = None,
        p               : float           = 0.25,
        min_mid_channels: int             = 4,
        act             : Callable        = None,
        *args, **kwargs
    ):
        super().__init__()
        mid_channels  = min(in_channels, max(min_mid_channels, math.ceil(p * in_channels)))
        self.pw_conv1 = base.Conv2d(
            in_channels  = in_channels,
            out_channels = mid_channels,
            kernel_size  = 1,
            stride       = 1,
            padding      = 0,
            dilation     = 1,
            groups       = 1,
            bias         = False,
            padding_mode = "zeros",
            device       = device,
            dtype        = dtype,
        )
        self.act1 = base.to_act_layer(
            act          = act,
            num_features = mid_channels
        )  # if act else None
        self.pw_conv2 = base.Conv2d(
            in_channels  = mid_channels,
            out_channels = out_channels,
            kernel_size  = 1,
            stride       = 1,
            padding      = 0,
            dilation     = 1,
            groups       = 1,
            bias         = False,
            padding_mode = "zeros",
            device       = device,
            dtype        = dtype,
        )
        self.act2 = base.to_act_layer(
            act          = act,
            num_features = out_channels
        )  # if act else None
        self.dw_conv = base.Conv2d(
            in_channels  = out_channels,
            out_channels = out_channels,
            kernel_size  = kernel_size,
            stride       = stride,
            padding      = padding,
            dilation     = dilation,
            groups       = out_channels,
            bias         = bias,
            padding_mode = padding_mode,
            device       = device,
            dtype        = dtype,
        )
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        if self.act1 is not None:
            y = self.act1(y)
        y = self.pw_conv2(y)
        if self.act2 is not None:
            y = self.act2(y)
        y = self.dw_conv(y)
        return y
    
    def regularization_loss(self):
        w   = self.pw_conv1.weight[:, :, 0, 0]
        wwt = torch.mm(w, torch.transpose(w, 0, 1))
        i   = torch.eye(wwt.shape[0], device=wwt.device)
        return torch.norm(wwt - i, p="fro")


@LAYERS.register()
class UnconstrainedBlueprintSeparableConv2d(base.ConvLayerParsingMixin, nn.Module):
    """Unconstrained Blueprint Separable Conv2d adopted from the paper:
    "Rethinking Depthwise Separable Convolutions: How Intra-Kernel Correlations
    Lead to Improved MobileNets," CVPR 2020.
    
    References:
        https://github.com/zeiss-microscopy/BSConv
    """
    
    def __init__(
        self,
        in_channels : int,
        out_channels: int,
        kernel_size : _size_2_t,
        stride      : _size_2_t       = 1,
        padding     : _size_2_t | str = 0,
        dilation    : _size_2_t       = 1,
        groups      : int             = 1,
        bias        : bool            = True,
        padding_mode: str             = "zeros",
        device      : Any             = None,
        dtype       : Any             = None,
        act         : Callable        = None,
        *args, **kwargs
    ):
        super().__init__()
        self.pw_conv = base.Conv2d(
            in_channels  = in_channels,
            out_channels = out_channels,
            kernel_size  = 1,
            stride       = 1,
            padding      = 0,
            dilation     = 1,
            groups       = 1,
            bias         = False,
            padding_mode = "zeros",
            device       = device,
            dtype        = dtype,
        )
        self.act     = base.to_act_layer(act=act, num_features=out_channels)
        self.dw_conv = base.Conv2d(
            in_channels  = out_channels,
            out_channels = out_channels,
            kernel_size  = kernel_size,
            stride       = stride,
            padding      = padding,
            dilation     = dilation,
            groups       = out_channels,
            bias         = bias,
            padding_mode = padding_mode,
            device       = device,
            dtype        = dtype,
        )
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv(x)
        if self.act is not None:
            y = self.act(y)
        y = self.dw_conv(y)
        return y


BSConv2dS = SubspaceBlueprintSeparableConv2d
BSConv2dU = UnconstrainedBlueprintSeparableConv2d
LAYERS.register(module=BSConv2dS)
LAYERS.register(module=BSConv2dU)

# endregion


# region Attention Blueprint Separable Convolution

@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d(
    base.ConvLayerParsingMixin,
    nn.Module
):
    """Subspace Blueprint Separable Conv2d with Self-Attention adopted from the
    paper:
        "Rethinking Depthwise Separable Convolutions: How Intra-Kernel
        Correlations Lead to Improved MobileNets," CVPR 2020.
    
    References:
        https://github.com/zeiss-microscopy/BSConv
    """
    
    def __init__(
        self,
        in_channels     : int,
        out_channels    : int,
        kernel_size     : _size_2_t,
        stride          : _size_2_t       = 1,
        padding         : _size_2_t | str = 0,
        dilation        : _size_2_t       = 1,
        groups          : int             = 1,
        bias            : bool            = True,
        padding_mode    : str             = "zeros",
        device          : Any             = None,
        dtype           : Any             = None,
        p               : float           = 0.25,
        min_mid_channels: int             = 4,
        act1            : Callable        = None,
        act2            : Callable        = None,
    ):
        super().__init__()
        assert 0.0 <= p <= 1.0
        mid_channels = min(
            in_channels, max(min_mid_channels, math.ceil(p * in_channels))
        )
        self.pw_conv1 = base.Conv2d(
            in_channels  = in_channels,
            out_channels = mid_channels,
            kernel_size  = 1,
            stride       = 1,
            padding      = 0,
            dilation     = 1,
            groups       = 1,
            bias         = False,
            padding_mode = "zeros",
            device       = device,
            dtype        = dtype,
        )
        self.act1 = act1(num_features=mid_channels) if act1 is not None else None
        self.pw_conv2 = base.Conv2d(
            in_channels  = mid_channels,
            out_channels = out_channels,
            kernel_size  = 1,
            stride       = 1,
            padding      = 0,
            dilation     = 1,
            groups       = 1,
            bias         = False,
            padding_mode = "zeros",
            device       = device,
            dtype        = dtype,
        )
        self.act2 = act2(num_features=out_channels) if act2 is not None else None
        self.dw_conv = base.Conv2d(
            in_channels  = out_channels,
            out_channels = out_channels,
            kernel_size  = kernel_size,
            stride       = stride,
            padding      = padding,
            dilation     = dilation,
            groups       = out_channels,
            bias         = bias,
            padding_mode = padding_mode,
            device       = device,
            dtype        = dtype,
        )
        self.simam = base.SimAM()
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        y = self.simam(y)
        if self.act1 is not None:
            y = self.act1(y)
        y = self.pw_conv2(y)
        if self.act2 is not None:
            y = self.act2(y)
        y = self.dw_conv(y)
        return y
    
    def regularization_loss(self):
        w   = self.pw_conv1.weight[:, :, 0, 0]
        wwt = torch.mm(w, torch.transpose(w, 0, 1))
        i   = torch.eye(wwt.shape[0], device=wwt.device)
        return torch.norm(wwt - i, p="fro")


@LAYERS.register()
class AttentionUnconstrainedBlueprintSeparableConv2d(
    base.ConvLayerParsingMixin,
    nn.Module
):
    """Subspace Blueprint Separable Conv2d with Self-Attention adopted from the
    paper:
        "Rethinking Depthwise Separable Convolutions: How Intra-Kernel
        Correlations Lead to Improved MobileNets," CVPR 2020.
    
    References:
        https://github.com/zeiss-microscopy/BSConv
    """
    
    def __init__(
        self,
        in_channels     : int,
        out_channels    : int,
        kernel_size     : _size_2_t,
        stride          : _size_2_t       = 1,
        padding         : _size_2_t | str = 0,
        dilation        : _size_2_t       = 1,
        groups          : int             = 1,
        bias            : bool            = True,
        padding_mode    : str             = "zeros",
        device          : Any             = None,
        dtype           : Any             = None,
        p               : float           = 0.25,
        min_mid_channels: int             = 4,
        act             : Callable        = None,
    ):
        super().__init__()
        self.pw_conv = base.Conv2d(
            in_channels  = in_channels,
            out_channels = out_channels,
            kernel_size  = 1,
            stride       = 1,
            padding      = 0,
            dilation     = 1,
            groups       = 1,
            bias         = False,
            padding_mode = "zeros",
            device       = device,
            dtype        = dtype,
        )
        self.act = act(num_features=out_channels) if act is not None else None
        self.dw_conv = base.Conv2d(
            in_channels  = out_channels,
            out_channels = out_channels,
            kernel_size  = kernel_size,
            stride       = stride,
            padding      = padding,
            dilation     = dilation,
            groups       = out_channels,
            bias         = bias,
            padding_mode = padding_mode,
            device       = device,
            dtype        = dtype,
        )
        self.simam = base.SimAM()
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv(x)
        y = self.simam(y)
        if self.act is not None:
            y = self.act(y)
        y = self.dw_conv(y)
        return y


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d1(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        x = self.pw_conv1(x)
        # x = self.simam(x)
        # if self.act1 is not None:
        #     x = self.act1(x)
        x = self.pw_conv2(x)
        # if self.act2 is not None:
        #     x = self.act2(x)
        x = self.dw_conv(x)
        return x


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d2(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        # y = self.simam(y)
        if self.act1 is not None:
            y = self.act1(y)
        y = self.pw_conv2(y)
        # if self.act2 is not None:
        #    y = self.act2(y)
        y = self.dw_conv(y)
        return y


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d3(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        # y = self.simam(y)
        # if self.act1 is not None:
        #    y = self.act1(y)
        y = self.pw_conv2(y)
        if self.act2 is not None:
            y = self.act2(y)
        y = self.dw_conv(y)
        return y


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d4(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        # y = self.simam(y)
        if self.act1 is not None:
            y = self.act1(y)
        y = self.pw_conv2(y)
        if self.act2 is not None:
            y = self.act2(y)
        y = self.dw_conv(y)
        return y


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d5(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        y = self.simam(y)
        # if self.act1 is not None:
        #    y = self.act1(y)
        y = self.pw_conv2(y)
        # if self.act2 is not None:
        #    y = self.act2(y)
        y = self.dw_conv(y)
        return y


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d6(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        # if self.act1 is not None:
        #    y = self.act1(y)
        y = self.pw_conv2(y)
        y = self.simam(y)
        # if self.act2 is not None:
        #    y = self.act2(y)
        y = self.dw_conv(y)
        return y


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d7(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        # if self.act1 is not None:
        #    y = self.act1(y)
        y = self.pw_conv2(y)
        # if self.act2 is not None:
        #    y = self.act2(y)
        y = self.dw_conv(y)
        y = self.simam(y)
        return y


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d8(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        y = self.simam(y)
        if self.act1 is not None:
            y = self.act1(y)
        y = self.pw_conv2(y)
        # if self.act2 is not None:
        #    y = self.act2(y)
        y = self.dw_conv(y)
        return y


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d9(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        y = self.simam(y)
        # if self.act1 is not None:
        #     y = self.act1(y)
        y = self.pw_conv2(y)
        if self.act2 is not None:
            y = self.act2(y)
        y = self.dw_conv(y)
        return y


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d10(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        if self.act1 is not None:
            y = self.act1(y)
        y = self.pw_conv2(y)
        y = self.simam(y)
        # if self.act2 is not None:
        #     y = self.act2(y)
        y = self.dw_conv(y)
        return y


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d11(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        # if self.act1 is not None:
        #     y = self.act1(y)
        y = self.pw_conv2(y)
        y = self.simam(y)
        if self.act2 is not None:
            y = self.act2(y)
        y = self.dw_conv(y)
        return y


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d12(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        if self.act1 is not None:
            y = self.act1(y)
        y = self.pw_conv2(y)
        if self.act2 is not None:
            y = self.act2(y)
        y = self.dw_conv(y)
        y = self.simam(y)
        return y


@LAYERS.register()
class AttentionSubspaceBlueprintSeparableConv2d13(
    AttentionSubspaceBlueprintSeparableConv2d
):
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        y = self.pw_conv1(x)
        y = self.simam(y)
        if self.act1 is not None:
            y = self.act1(y)
        y = self.pw_conv2(y)
        if self.act2 is not None:
            y = self.act2(y)
        y = self.dw_conv(y)
        return y


ABSConv2dS   = AttentionSubspaceBlueprintSeparableConv2d
ABSConv2dU   = AttentionUnconstrainedBlueprintSeparableConv2d
ABSConv2dS1  = AttentionSubspaceBlueprintSeparableConv2d1
ABSConv2dS2  = AttentionSubspaceBlueprintSeparableConv2d2
ABSConv2dS3  = AttentionSubspaceBlueprintSeparableConv2d3
ABSConv2dS4  = AttentionSubspaceBlueprintSeparableConv2d4
ABSConv2dS5  = AttentionSubspaceBlueprintSeparableConv2d5
ABSConv2dS6  = AttentionSubspaceBlueprintSeparableConv2d6
ABSConv2dS7  = AttentionSubspaceBlueprintSeparableConv2d7
ABSConv2dS8  = AttentionSubspaceBlueprintSeparableConv2d8
ABSConv2dS9  = AttentionSubspaceBlueprintSeparableConv2d9
ABSConv2dS10 = AttentionSubspaceBlueprintSeparableConv2d10
ABSConv2dS11 = AttentionSubspaceBlueprintSeparableConv2d11
ABSConv2dS12 = AttentionSubspaceBlueprintSeparableConv2d12
ABSConv2dS13 = AttentionSubspaceBlueprintSeparableConv2d13

LAYERS.register(module=ABSConv2dS)
LAYERS.register(module=ABSConv2dU)
LAYERS.register(module=ABSConv2dS1)
LAYERS.register(module=ABSConv2dS2)
LAYERS.register(module=ABSConv2dS3)
LAYERS.register(module=ABSConv2dS4)
LAYERS.register(module=ABSConv2dS5)
LAYERS.register(module=ABSConv2dS6)
LAYERS.register(module=ABSConv2dS7)
LAYERS.register(module=ABSConv2dS8)
LAYERS.register(module=ABSConv2dS9)
LAYERS.register(module=ABSConv2dS10)
LAYERS.register(module=ABSConv2dS11)
LAYERS.register(module=ABSConv2dS12)
LAYERS.register(module=ABSConv2dS13)

# endregion