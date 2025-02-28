import torch
import torch.amp as amp
import inspect
import numpy as np

from typing import Any, List, Optional, Sequence, Tuple

from .t5 import T5Encoder
from .wan import WanModel
from .vae import WanVideoVAE

from math import ceil
from diffusers import SchedulerMixin
from transformers import T5Tokenizer # type: ignore[import-untyped]
from contextlib import nullcontext

from taproot.util import (
    maybe_use_tqdm,
    empty_cache,
    logger,
    log_duration,
    sliding_1d_windows,
)

class WanPipeline:
    """
    Video synthesis pipeline using Wan
    """
    def __init__(
        self,
        text_encoder: T5Encoder,
        tokenizer: T5Tokenizer,
        transformer: WanModel,
        vae: WanVideoVAE,
        scheduler: SchedulerMixin,
        dtype: torch.dtype=torch.float16,
        device: Optional[torch.device]=None,
        default_negative_prompt: str="色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走"
    ) -> None:
        super().__init__()
        self.text_encoder = text_encoder
        self.tokenizer = tokenizer
        self.transformer = transformer
        self.vae = vae
        self.scheduler = scheduler
        self.dtype = dtype
        self.device = torch.device("cpu") if device is None else device
        self.default_negative_prompt = default_negative_prompt

    def get_sampling_sigmas(
        self,
        sampling_steps: int,
        shift: float
    ) -> np.ndarray[Any, Any]:
        """
        Get the sampling sigmas for the inference steps
        :param sampling_steps: Number of sampling steps
        :param shift: Shift value
        :return: Sampling sigmas
        """
        sigma = np.linspace(1, 0, sampling_steps + 1)[:sampling_steps]
        sigma = (shift * sigma / (1 + (shift - 1) * sigma))
        return sigma

    def retrieve_timesteps(
        self,
        num_inference_steps: Optional[int]=None,
        device: Optional[torch.device]=None,
        timesteps: Optional[Sequence[int]]=None,
        sigmas: Optional[Sequence[float]]=None,
        **kwargs: Any,
    ) -> Tuple[List[int], int]:
        """
        Retrieve the timesteps for the inference steps

        :param num_inference_steps: Number of inference steps
        :param device: Device to use
        :param timesteps: Timesteps to use
        :param sigmas: Sigmas to use
        :param kwargs: Additional keyword arguments
        :return: Timesteps and number of inference steps
        """
        if not hasattr(self.scheduler, "set_timesteps") or not hasattr(self.scheduler, "timesteps"):
            raise ValueError("The current scheduler class does not support custom timesteps or sigmas schedules.")

        passed_args = [num_inference_steps, timesteps, sigmas]
        num_passed_args = sum([arg is not None for arg in passed_args])

        if num_passed_args != 1:
            raise ValueError(
                "Exactly one of `num_inference_steps`, `timesteps`, or `sigmas` must be passed."
            )

        accepts_shift = "shift" in set(
            inspect.signature(self.scheduler.set_timesteps)
                .parameters
                .keys()
        )

        if not accepts_shift:
            kwargs.pop("shift", None)

        if timesteps is not None:
            accepts_timesteps = (
                "timesteps" in set(
                    inspect.signature(self.scheduler.set_timesteps)
                        .parameters
                        .keys()
                )
            )
            if not accepts_timesteps:
                raise ValueError(
                    f"The current scheduler class {self.scheduler.__class__}'s `set_timesteps` does not support custom"
                    f" timestep schedules. Please check whether you are using the correct scheduler."
                )
            self.scheduler.set_timesteps(timesteps=timesteps, device=device, **kwargs)
            timesteps = list(self.scheduler.timesteps)
            num_inference_steps = len(timesteps)
        elif sigmas is not None:
            accept_sigmas = (
                "sigmas" in set(
                    inspect.signature(self.scheduler.set_timesteps)
                        .parameters
                        .keys()
                )
            )
            if not accept_sigmas:
                raise ValueError(
                    f"The current scheduler class {self.scheduler.__class__}'s `set_timesteps` does not support custom"
                    f" sigmas schedules. Please check whether you are using the correct scheduler."
                )

            self.scheduler.set_timesteps(sigmas=sigmas, device=device, **kwargs)
            timesteps = list(self.scheduler.timesteps)
            num_inference_steps = len(timesteps)
        else:
            self.scheduler.set_timesteps(num_inference_steps, device=device, **kwargs)
            timesteps = list(self.scheduler.timesteps)

        return timesteps, num_inference_steps # type: ignore [return-value]

    @torch.no_grad()
    def encode_prompt(
        self,
        prompt: str,
    ) -> torch.Tensor:
        """
        Encode the prompt

        :param prompt: Prompt to encode
        :return: Encoded prompt
        """
        """
        self.text_encoder.model.to(self.device)
        return self.text_encoder([prompt], self.device)[0]
        """
        tokenizer_output = self.tokenizer(
            [prompt],
            padding="max_length",
            truncation=True,
            max_length=self.transformer.text_len,
            add_special_tokens=True,
            return_tensors="pt"
        )
        ids = tokenizer_output["input_ids"]
        mask = tokenizer_output["attention_mask"]
        ids = ids.to(self.device)
        mask = mask.to(self.device)
        seq_len = mask.gt(0).sum(dim=1).long()
        context = self.text_encoder(ids, mask).detach()

        return [u[:v] for u, v in zip(context, seq_len)][0] # type: ignore [no-any-return]

    @torch.no_grad()
    def predict_noise_at_timestep(
        self,
        timestep: torch.Tensor,
        latents: List[torch.Tensor],
        cond: List[torch.Tensor],
        uncond: Optional[List[torch.Tensor]],
        window_size: Optional[int],
        window_stride: Optional[int],
        guidance_scale: float,
        seq_len: int,
        do_classifier_free_guidance: bool,
    ) -> torch.Tensor:
        """
        Predict noise at a given timestep
        """
        if window_size and window_stride:
            num_frames = latents[0].shape[1]
            windows = sliding_1d_windows(
                num_frames,
                window_size,
                window_stride
            )
            num_windows = len(windows)
            noise_pred_count = torch.zeros_like(latents[0])
            noise_pred_total = torch.zeros_like(latents[0])

            for i, (start, end) in enumerate(windows):
                latent_model_input = [l[:, start:end] for l in latents]

                if do_classifier_free_guidance and uncond is not None:
                    [noise_pred_cond, noise_pred_uncond] = self.transformer(
                        latent_model_input + latent_model_input,    
                        t=timestep,
                        context=cond + uncond,
                        seq_len=seq_len
                    )
                    noise_pred = noise_pred_uncond + guidance_scale * (noise_pred_cond - noise_pred_uncond)
                else:
                    noise_pred = self.transformer(
                        latent_model_input,
                        t=timestep,
                        context=cond,
                        seq_len=seq_len
                    )[0]

                window_mask = torch.ones_like(noise_pred)

                if i > 0:
                    window_mask[:, :window_stride] = torch.linspace(0, 1, window_stride, device=noise_pred.device).unsqueeze(0).unsqueeze(-1).unsqueeze(-1)
                if i < num_windows - 1:
                    window_mask[:, -window_stride:] = torch.linspace(1, 0, window_stride, device=noise_pred.device).unsqueeze(0).unsqueeze(-1).unsqueeze(-1)

                noise_pred_total[:, start:end] += noise_pred * window_mask
                noise_pred_count[:, start:end] += window_mask

            noise_pred = noise_pred_total / noise_pred_count
        else:
            latent_model_input = latents
            noise_pred_cond = self.transformer(
                latent_model_input,
                t=timestep,
                context=cond,
                seq_len=seq_len
            )[0]

            if do_classifier_free_guidance and uncond is not None:
                noise_pred_uncond = self.transformer(
                    latent_model_input,
                    t=timestep,
                    context=uncond,
                    seq_len=seq_len
                )[0]
                noise_pred = noise_pred_uncond + guidance_scale * (noise_pred_cond - noise_pred_uncond)
            else:
                noise_pred = noise_pred_cond

        return noise_pred

    def __call__(
        self,
        prompt: str,
        negative_prompt: Optional[str]=None,
        num_frames: int=81,
        width: int=832,
        height: int=480,
        shift: float=5.0,
        guidance_scale: float=5.0,
        guidance_end: Optional[float]=None,
        num_inference_steps: int=50,
        window_size: Optional[int]=None,
        window_stride: Optional[int]=None,
        generator: Optional[torch.Generator]=None,
        use_tqdm: bool=True,
        cpu_offload: bool=True,
    ) -> torch.Tensor:
        """
        Generate video frames from the prompt.

        :param prompt: Prompt to generate video frames from
        :param negative_prompt: Negative prompt to generate video frames from
        :param num_frames: Number of frames to generate
        :param width: Width of the video in pixels
        :param height: Height of the video in pixels
        :param shift: Shift value
        :param num_inference_steps: Number of inference steps
        :param guidance_scale: Guidance scale
        :param generator: Generator to use for reproducibility
        :return: Video frames [3, T, H, W]
        """
        # Standardize args
        encoded_shape = self.vae.get_target_shape(
            num_frames=num_frames,
            height=height,
            width=width,
        )
        e_d, e_t, e_h, e_w = encoded_shape
        p_t, p_h, p_w = self.transformer.patch_size
        seq_len = ceil(
            (e_h * e_w) / (p_h * p_w) * e_t
        )

        if guidance_end is None:
            guidance_end = 1.0

        do_classifier_free_guidance = guidance_scale > 1.0

        # Get timesteps
        timesteps, num_inference_steps = self.retrieve_timesteps(
            num_inference_steps=num_inference_steps,
            device=self.device,
            shift=shift,
        )
        guidance_end_step = int(guidance_end * num_inference_steps) - 1

        # Encode prompts
        if cpu_offload:
            with log_duration("onloading text encoder"):
                self.text_encoder.to(self.device)

        with log_duration("encoding prompt"):
            cond = [self.encode_prompt(prompt).to(self.dtype)]

        if do_classifier_free_guidance:
            with log_duration("encoding negative prompt"):
                uncond = [self.encode_prompt(negative_prompt or self.default_negative_prompt).to(self.dtype)]

        if cpu_offload:
            with log_duration("offloading text encoder"):
                self.text_encoder.to("cpu")
                empty_cache()

        # Denoising loop
        noise = torch.randn(*encoded_shape, generator=generator, dtype=torch.float32)
        noise = noise.to(self.device, dtype=self.dtype)

        if hasattr(self.transformer, "no_sync"):
            sync_context = self.transformer.no_sync
        else:
            sync_context = nullcontext

        with amp.autocast("cuda", dtype=self.dtype), torch.no_grad(), sync_context(): # type: ignore[attr-defined]
            if cpu_offload:
                with log_duration("onloading transformer"):
                    self.transformer.to(self.device)

            latents = [noise]

            for i, t in maybe_use_tqdm(
                enumerate(timesteps),
                use_tqdm=use_tqdm,
                total=num_inference_steps
            ):
                timestep = torch.stack([t])
                noise_pred = self.predict_noise_at_timestep(
                    timestep=timestep,
                    latents=latents,
                    cond=cond,
                    uncond=uncond,
                    window_size=window_size,
                    window_stride=window_stride,
                    guidance_scale=guidance_scale,
                    seq_len=seq_len,
                    do_classifier_free_guidance=do_classifier_free_guidance,
                )
                temp_x0 = self.scheduler.step( # type: ignore[attr-defined]
                    noise_pred.unsqueeze(0),
                    t,
                    latents[0].unsqueeze(0),
                    generator=generator,
                    return_dict=False
                )[0]
                latents = [temp_x0.squeeze(0)]

                if i >= guidance_end_step and do_classifier_free_guidance:
                    logger.debug(f"Disabling guidance at step {i}")
                    do_classifier_free_guidance = False

            # Decode
            if cpu_offload:
                with log_duration("offloading transformer"):
                    self.transformer.to("cpu")
                    empty_cache()

                with log_duration("onloading vae"):
                    self.vae.to(self.device)

            videos = self.vae.decode(latents)

        if cpu_offload:
            with log_duration("offloading vae"):
                self.vae.to("cpu")
                empty_cache()

        return videos[0]
