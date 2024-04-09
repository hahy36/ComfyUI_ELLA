import os
import torch
import comfy

import folder_paths
from folder_paths import supported_pt_extensions, models_dir, folder_names_and_paths
from .ella_model.model import ELLA, T5TextEmbedder

folder_names_and_paths["ella"] = ([os.path.join(models_dir, "ella")], supported_pt_extensions)
folder_names_and_paths["t5_model"] = ([os.path.join(models_dir, "t5_model")],[])

class LoadElla:
    def __init__(self):
        self.device = comfy.model_management.text_encoder_device()
        self.dtype = comfy.model_management.text_encoder_dtype()

    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "ella_model": (folder_paths.get_filename_list("ella"),),
                              "t5_model": (os.listdir(folder_names_and_paths["t5_model"][0][0]),),
                              }}

    RETURN_TYPES = ("ELLA",)
    FUNCTION = "load_ella"

    CATEGORY = "ella/loaders"

    def load_ella(self, ella_model, t5_model):
        t5_path = os.path.join(models_dir, 't5_model', t5_model)
        ella_path = os.path.join(models_dir, 'ella', ella_model)
        t5_model = T5TextEmbedder(t5_path).to(self.device, self.dtype)
        ella = ELLA().to(self.device, self.dtype)

        ella_state_dict = comfy.utils.load_torch_file(ella_path)

        ella.load_state_dict(ella_state_dict)

        return ({"ELLA": ella, "T5": t5_model}, )

class ELLATextEncode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}), 
                "sigma": ("FLOAT", {"default": 1}, ),
                "ella": ("ELLA", ),
            }
        }

    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "encode"

    CATEGORY = "ella/conditioning"

    def encode(self, text, ella: dict, sigma):
        ella_dict = ella

        ella: ELLA = ella_dict.get("ELLA")
        t5: T5TextEmbedder = ella_dict.get("T5")

        cond = t5(text, max_length=128)
        cond_ella = ella(cond, timesteps=torch.from_numpy(sigma))
        
        return ([[cond_ella, {"pooled_output": cond_ella}]], ) # Output twice as we don't use pooled output
        
# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "LoadElla": LoadElla,
    "ELLATextEncode": ELLATextEncode,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadElla": "Load ELLA Model",
    "ELLATextEncode": "ELLATextEncode",
}