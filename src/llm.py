"""Modèles de langage interchangeables.

- ``LocalLLM`` : modèle instruct exécuté localement sur CPU via transformers (par défaut Qwen2.5-1.5B-Instruct, quantifié partiellement).
- ``APILLM``  : tout point d'accès compatible OpenAI (OpenAI, Groq, Mistral, vLLM, Ollama…).

Les deux exposent la même méthode ``chat(messages, max_new_tokens)`` ; le graphe ne dépend que de cette interface.
"""
from __future__ import annotations

import json
import time
import urllib.request
from functools import lru_cache

from .config import CONFIG


class BaseLLM:
    name = "base"

    def __init__(self):
        self.nb_appels, self.temps_total, self.tokens_generes = 0, 0.0, 0

    def chat(self, messages: list[dict], max_new_tokens: int | None = None) -> str:  # pragma: no cover
        raise NotImplementedError

    def stats(self) -> dict:
        return {"appels": self.nb_appels, "temps_llm_s": round(self.temps_total, 2), "tokens": self.tokens_generes}


class LocalLLM(BaseLLM):
    """Modèle local sur CPU.

    Sans GPU et avec 7 Go de RAM, Qwen2.5-1.5B ne tient pas en float32 (OOM) et est très lent en bfloat16
    (2,4 tokens/s). On applique donc une quantification dynamique int8 *partielle* : seules les projections
    ``gate_proj`` et ``up_proj`` des MLP sont quantifiées ; ``down_proj`` et l'attention restent en float32,
    car la quantification complète (testée) détruit les sorties du modèle (valeurs aberrantes d'activation).
    """

    def __init__(self, model_name: str | None = None):
        super().__init__()
        import gc

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        torch.set_num_threads(CONFIG.num_threads)
        self.torch = torch
        self.name = model_name or CONFIG.local_model
        self.tok = AutoTokenizer.from_pretrained(self.name)
        quant = CONFIG.local_quant == "int8-mlp"
        self.model = AutoModelForCausalLM.from_pretrained(self.name,
                                                          dtype=torch.bfloat16 if quant else torch.float32)
        if quant:
            from torch.ao.nn.quantized.dynamic import Linear as QLinear
            from torch.ao.quantization import per_channel_dynamic_qconfig
            for layer in self.model.model.layers:
                layer.float()
                for nom in ("gate_proj", "up_proj"):
                    lin = getattr(layer.mlp, nom)
                    lin.qconfig = per_channel_dynamic_qconfig
                    setattr(layer.mlp, nom, QLinear.from_float(lin))
                gc.collect()
            self.model.float()  # embeddings, normalisations, rotary, lm_head
            self.name += " (int8 gate/up)"
        self.model.eval()

    def chat(self, messages, max_new_tokens=None):
        t0 = time.time()
        enc = self.tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt",
                                           return_dict=True)
        with self.torch.inference_mode():
            out = self.model.generate(**enc, max_new_tokens=max_new_tokens or CONFIG.max_new_tokens,
                                      do_sample=False, repetition_penalty=1.05,
                                      pad_token_id=self.tok.eos_token_id)
        gen = out[0][enc["input_ids"].shape[1]:]
        self.nb_appels += 1
        self.tokens_generes += int(gen.shape[0])
        self.temps_total += time.time() - t0
        return self.tok.decode(gen, skip_special_tokens=True).strip()


class APILLM(BaseLLM):
    """Client minimal (sans dépendance) pour une API /chat/completions compatible OpenAI."""

    def __init__(self):
        super().__init__()
        if not CONFIG.api_key:
            raise RuntimeError("Aucune clé API : définir LLM_API_KEY (ou OPENAI_API_KEY / GROQ_API_KEY).")
        self.name = CONFIG.api_model

    def chat(self, messages, max_new_tokens=None):
        t0 = time.time()
        body = json.dumps({"model": CONFIG.api_model, "messages": messages, "temperature": 0,
                           "max_tokens": max_new_tokens or CONFIG.max_new_tokens}).encode()
        req = urllib.request.Request(CONFIG.api_base_url.rstrip("/") + "/chat/completions", data=body,
                                     headers={"Content-Type": "application/json",
                                              "Authorization": f"Bearer {CONFIG.api_key}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        self.nb_appels += 1
        self.tokens_generes += data.get("usage", {}).get("completion_tokens", 0)
        self.temps_total += time.time() - t0
        return data["choices"][0]["message"]["content"].strip()


@lru_cache(maxsize=1)
def get_llm() -> BaseLLM:
    return APILLM() if CONFIG.llm_provider == "openai" else LocalLLM()
