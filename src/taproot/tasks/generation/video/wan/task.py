from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from taproot.constants import *
from taproot.util import get_seed, get_diffusers_scheduler_by_name
from taproot.tasks.base import Task

from .pretrained import (
    PretrainedWanTextEncoder,
    PretrainedWanTokenizer,
    PretrainedWanVAE,
    PretrainedWanScheduler,
    PretrainedWanT2V1BTransformer,
    PretrainedWanT2V14BTransformer,
    PretrainedWanT2V14BTransformerQ80,
    PretrainedWanT2V14BTransformerQ6K,
    PretrainedWanT2V14BTransformerQ5KM,
    PretrainedWanT2V14BTransformerQ4KM,
    PretrainedWanT2V14BTransformerQ3KM,
)

if TYPE_CHECKING:
    import torch
    from taproot.hinting import SeedType, ImageResultType

__all__ = [
    "WanVideoGeneration1B",
    "WanVideoGeneration14B",
]

class WanVideoGeneration1B(Task):
    """
    Text-to-video generation using Wan Video.
    """
    
    """Global Task Metadata"""
    task = "video-generation"
    model = "wan"
    default = False
    display_name = "Wan Video Generation"

    """Model Configuration"""
    static_gpu_memory_gb = 38.3
    pretrained_models = {
        "vae": PretrainedWanVAE,
        "scheduler": PretrainedWanScheduler,
        "tokenizer": PretrainedWanTokenizer,
        "text_encoder": PretrainedWanTextEncoder,
        "transformer": PretrainedWanT2V1BTransformer,
    }
    offload_models = ["vae", "text_encoder", "transformer"]
    """
    pretrained_models = {
        "scheduler": PretrainedWanScheduler,
    }
    """

    """Authorship Metadata"""
    author = "Wan Foundation Model Team"
    author_affiliations = ["Tencent"]
    author_url = "https://arxiv.org/abs/2412.03603"
    author_journal = "arXiv"
    author_journal_year = 2024
    author_journal_volume = "2412.03603"
    author_journal_title = "WanVideo: A Systematic Framework for Large Video Generation Models"

    """License Metadata"""
    license = "Tencent Wan Community License"
    license_url = "https://github.com/Tencent/WanVideo/blob/main/LICENSE.txt"
    license_attribution = True # Must attribute the authors
    license_redistribution = True # Can redistribute
    license_derivatives = True # Can modify
    license_commercial = True # Can use for commercial purposes up to 100 million users/month
    license_hosting = True # Can host the model as a service
    license_copy_left = False # Derived works do not have to be open source

    def load(self) -> None:
        """
        TODO: remove
        """
        return super().load()
        import sys
        sys.path.insert(0, "/home/benjamin/Wan2.1")
        from wan.text2video import WanT2V
        from wan.configs import t2v_1_3B
        self.model = WanT2V(
            config=t2v_1_3B,
            checkpoint_dir="/home/benjamin/Wan2.1/Wan2.1-T2V-1.3B"
        )
        self.model.model.to("cpu")
        self.model.text_encoder.to("cpu")

    def get_video_tensor_from_result(
        self,
        result: torch.Tensor
    ) -> torch.Tensor:
        """
        Get the video tensor from the result.
        """
        import torch
        import torchvision # type: ignore[import-untyped]
        result = result.unsqueeze(0)
        result = result.clamp(-1, 1)
        result = torch.stack([
            torchvision.utils.make_grid(
                u, nrow=1, normalize=True, value_range=(-1, 1)
            )
            for u in result.unbind(2)
        ], dim=1)
        result = result.cpu().permute(1, 0, 2, 3).unsqueeze(0)
        return result

    def __call__( # type: ignore[override]
        self,
        *,
        prompt: str,
        height: int=480,
        width: int=832,
        num_frames: int=81,
        num_inference_steps: int=50,
        window_size: Optional[int]=None,
        window_stride: Optional[int]=None,
        guidance_scale: float=5.0,
        guidance_end: Optional[float]=None,
        frame_rate: int=16,
        seed: Optional[SeedType]=None,
        scheduler: Optional[DIFFUSERS_SCHEDULER_LITERAL]=None,
        output_format: VIDEO_OUTPUT_FORMAT_LITERAL="mp4",
        output_upload: bool=False,
    ) -> ImageResultType:
        """
        Generate a video from a text prompt.
        """
        import torch
        from .model import WanPipeline
        pipeline = WanPipeline(
            text_encoder=self.pretrained.text_encoder,
            tokenizer=self.pretrained.tokenizer,
            vae=self.pretrained.vae,
            transformer=self.pretrained.transformer,
            scheduler=self.pretrained.scheduler,
            device=self.device,
        )
        if scheduler is not None:
            pipeline.scheduler = get_diffusers_scheduler_by_name(
                name=scheduler,
                config=self.pretrained.scheduler.config
            )

        seed = get_seed(seed)
        generator = torch.Generator()
        generator.manual_seed(seed)
        results = pipeline(
            prompt=prompt,
            height=height,
            width=width,
            num_frames=num_frames,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            guidance_end=guidance_end,
            window_size=window_size,
            window_stride=window_stride,
            generator=generator,
        )
        results = self.get_video_tensor_from_result(results)
        return self.get_output_from_video_result(
            results,
            multi_video=False,
            frame_rate=frame_rate,
            output_format=output_format,
            output_upload=output_upload,
        )

class WanVideoGeneration14B(WanVideoGeneration1B):
    """
    Text-to-video generation using Wan Video.
    """
    
    """Global Task Metadata"""
    model = "wan-14b"
    display_name = "Wan Video Generation (14B)"

    """Model Configuration"""
    static_gpu_memory_gb = 38.3
    pretrained_models = {
        **WanVideoGeneration1B.pretrained_models,
        "transformer": PretrainedWanT2V14BTransformer,
    }

class WanVideoGeneration14BQ80(WanVideoGeneration14B):
    """
    Text-to-video generation using Wan Video.
    """
    
    """Global Task Metadata"""
    model = "wan-14b-q8-0"
    display_name = "Wan Video Generation (14B Q8-0)"

    """Model Configuration"""
    static_gpu_memory_gb = 24.1
    pretrained_models = {
        **WanVideoGeneration14B.pretrained_models,
        "transformer": PretrainedWanT2V14BTransformerQ80,
    }

class WanVideoGeneration14BQ6K(WanVideoGeneration14B):
    """
    Text-to-video generation using Wan Video.
    """
    
    """Global Task Metadata"""
    model = "wan-14b-q6-k"
    display_name = "Wan Video Generation (14B Q6-K)"

    """Model Configuration"""
    static_gpu_memory_gb = 22.1
    pretrained_models = {
        **WanVideoGeneration14B.pretrained_models,
        "transformer": PretrainedWanT2V14BTransformerQ6K,
    }

class WanVideoGeneration14BQ5KM(WanVideoGeneration14B):
    """
    Text-to-video generation using Wan Video.
    """
    
    """Global Task Metadata"""
    model = "wan-14b-q5-k-m"
    display_name = "Wan Video Generation (14B Q5-K-M)"

    """Model Configuration"""
    static_gpu_memory_gb = 20.1
    pretrained_models = {
        **WanVideoGeneration14B.pretrained_models,
        "transformer": PretrainedWanT2V14BTransformerQ5KM,
    }

class WanVideoGeneration14BQ4KM(WanVideoGeneration14B):
    """
    Text-to-video generation using Wan Video.
    """
    
    """Global Task Metadata"""
    model = "wan-14b-q4-k-m"
    display_name = "Wan Video Generation (14B Q4-K-M)"

    """Model Configuration"""
    static_gpu_memory_gb = 18.1
    pretrained_models = {
        **WanVideoGeneration14B.pretrained_models,
        "transformer": PretrainedWanT2V14BTransformerQ4KM,
    }

class WanVideoGeneration14BQ3KM(WanVideoGeneration14B):
    """
    Text-to-video generation using Wan Video.
    """
    
    """Global Task Metadata"""
    model = "wan-14b-q3-k-m"
    display_name = "Wan Video Generation (14B Q3-K-M)"

    """Model Configuration"""
    static_gpu_memory_gb = 16.1
    pretrained_models = {
        **WanVideoGeneration14B.pretrained_models,
        "transformer": PretrainedWanT2V14BTransformerQ3KM,
    }
