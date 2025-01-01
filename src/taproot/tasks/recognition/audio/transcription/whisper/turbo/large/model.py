from typing import Any, Dict, Optional

from ...pretrained import WhisperModel

__all__ = ["TurboWhisperLargeV3Model"]

class TurboWhisperLargeV3Model(WhisperModel):
    """
    Inference model for the Whisper Large V3 Turbo model.
    """
    model_url: Optional[str] = "https://huggingface.co/benjamin-paine/taproot-common/resolve/main/audio-transcription-whisper-large-v3-turbo.fp16.safetensors"

    @classmethod
    def get_default_config(cls) -> Optional[Dict[str, Any]]:
        """
        Returns the default configuration for the model.
        """
        return {
            "activation_dropout": 0,
            "activation_function": "gelu",
            "apply_spec_augment": False,
            "attention_dropout": 0,
            "begin_suppress_tokens": [220, 50256],
            "bos_token_id": 50257,
            "classifier_proj_size": 256,
            "d_model": 1280,
            "decoder_attention_heads": 20,
            "decoder_ffn_dim": 5120,
            "decoder_layerdrop": 0,
            "decoder_layers": 4,
            "decoder_start_token_id": 50258,
            "dropout": 0,
            "encoder_attention_heads": 20,
            "encoder_ffn_dim": 5120,
            "encoder_layerdrop": 0,
            "encoder_layers": 32,
            "eos_token_id": 50257,
            "init_std": 0.02,
            "is_encoder_decoder": True,
            "mask_feature_length": 10,
            "mask_feature_min_masks": 0,
            "mask_feature_prob": 0,
            "mask_time_length": 10,
            "mask_time_min_masks": 2,
            "mask_time_prob": 0.05,
            "max_source_positions": 1500,
            "max_target_positions": 448,
            "median_filter_width": 7,
            "model_type": "whisper",
            "num_hidden_layers": 32,
            "num_mel_bins": 128,
            "pad_token_id": 50257,
            "scale_embedding": False,
            "torch_dtype": "float16",
            "use_cache": True,
            "use_weighted_layer_sum": False,
            "vocab_size": 51866,
        }

    @classmethod
    def get_generation_config(cls) -> Optional[Dict[str, Any]]:
        """
        Returns the default generation configuration for the model.
        """
        return {
            "alignment_heads": [[2, 4], [2, 11], [3, 3], [3, 6], [3, 11], [3, 14]],
            "begin_suppress_tokens": [220, 50257],
            "bos_token_id": 50257,
            "decoder_start_token_id": 50258,
            "eos_token_id": 50257,
            "forced_decoder_ids": [[1, None], [2, 50360]],
            "is_multilingual": True,
            "lang_to_id": {
                "<|af|>": 50327,
                "<|am|>": 50334,
                "<|ar|>": 50272,
                "<|as|>": 50350,
                "<|az|>": 50304,
                "<|ba|>": 50355,
                "<|be|>": 50330,
                "<|bg|>": 50292,
                "<|bn|>": 50302,
                "<|bo|>": 50347,
                "<|br|>": 50309,
                "<|bs|>": 50315,
                "<|ca|>": 50270,
                "<|cs|>": 50283,
                "<|cy|>": 50297,
                "<|da|>": 50285,
                "<|de|>": 50261,
                "<|el|>": 50281,
                "<|en|>": 50259,
                "<|es|>": 50262,
                "<|et|>": 50307,
                "<|eu|>": 50310,
                "<|fa|>": 50300,
                "<|fi|>": 50277,
                "<|fo|>": 50338,
                "<|fr|>": 50265,
                "<|gl|>": 50319,
                "<|gu|>": 50333,
                "<|haw|>": 50352,
                "<|ha|>": 50354,
                "<|he|>": 50279,
                "<|hi|>": 50276,
                "<|hr|>": 50291,
                "<|ht|>": 50339,
                "<|hu|>": 50286,
                "<|hy|>": 50312,
                "<|id|>": 50275,
                "<|is|>": 50311,
                "<|it|>": 50274,
                "<|ja|>": 50266,
                "<|jw|>": 50356,
                "<|ka|>": 50329,
                "<|kk|>": 50316,
                "<|km|>": 50323,
                "<|kn|>": 50306,
                "<|ko|>": 50264,
                "<|la|>": 50294,
                "<|lb|>": 50345,
                "<|ln|>": 50353,
                "<|lo|>": 50336,
                "<|lt|>": 50293,
                "<|lv|>": 50301,
                "<|mg|>": 50349,
                "<|mi|>": 50295,
                "<|mk|>": 50308,
                "<|ml|>": 50296,
                "<|mn|>": 50314,
                "<|mr|>": 50320,
                "<|ms|>": 50282,
                "<|mt|>": 50343,
                "<|my|>": 50346,
                "<|ne|>": 50313,
                "<|nl|>": 50271,
                "<|nn|>": 50342,
                "<|no|>": 50288,
                "<|oc|>": 50328,
                "<|pa|>": 50321,
                "<|pl|>": 50269,
                "<|ps|>": 50340,
                "<|pt|>": 50267,
                "<|ro|>": 50284,
                "<|ru|>": 50263,
                "<|sa|>": 50344,
                "<|sd|>": 50332,
                "<|si|>": 50322,
                "<|sk|>": 50298,
                "<|sl|>": 50305,
                "<|sn|>": 50324,
                "<|so|>": 50326,
                "<|sq|>": 50317,
                "<|sr|>": 50303,
                "<|su|>": 50357,
                "<|sv|>": 50273,
                "<|sw|>": 50318,
                "<|ta|>": 50287,
                "<|te|>": 50299,
                "<|tg|>": 50331,
                "<|th|>": 50289,
                "<|tk|>": 50341,
                "<|tl|>": 50348,
                "<|tr|>": 50268,
                "<|tt|>": 50351,
                "<|uk|>": 50280,
                "<|ur|>": 50290,
                "<|uz|>": 50337,
                "<|vi|>": 50278,
                "<|yi|>": 50335,
                "<|yo|>": 50325,
                "<|yue|>": 50358,
                "<|zh|>": 50260,
            },
            "max_initial_timestamp_index": 50,
            "max_length": 448,
            "no_timestamps_token_id": 50364,
            "pad_token_id": 50257,
            "prev_sot_token_id": 50362,
            "return_timestamps": False,
            "suppress_tokens": [
                1,
                2,
                7,
                8,
                9,
                10,
                14,
                25,
                26,
                27,
                28,
                29,
                31,
                58,
                59,
                60,
                61,
                62,
                63,
                90,
                91,
                92,
                93,
                359,
                503,
                522,
                542,
                873,
                893,
                902,
                918,
                922,
                931,
                1350,
                1853,
                1982,
                2460,
                2627,
                3246,
                3253,
                3268,
                3536,
                3846,
                3961,
                4183,
                4667,
                6585,
                6647,
                7273,
                9061,
                9383,
                10428,
                10929,
                11938,
                12033,
                12331,
                12562,
                13793,
                14157,
                14635,
                15265,
                15618,
                16553,
                16604,
                18362,
                18956,
                20075,
                21675,
                22520,
                26130,
                26161,
                26435,
                28279,
                29464,
                31650,
                32302,
                32470,
                36865,
                42863,
                47425,
                49870,
                50254,
                50258,
                50359,
                50360,
                50361,
                50362,
                50363,
            ],
            "task_to_id": {"transcribe": 50360, "translate": 50359},
        }
