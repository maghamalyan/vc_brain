"""Small TGAT-flavored temporal attention model over actor ego-graphs.

Per sample: the actor's last-k timestamped edges (event type, functional time
encoding of delta-t, two edge scalars) pass through one self-attention layer,
then an actor-query attention pooling layer whose weights are the exported
"which repos does the model look at" signal. Under 100k parameters.
"""

from __future__ import annotations

import math

import torch
from torch import nn

from dataset import N_ACTOR_FEATS, N_EVENT_TYPES


class FunctionalTimeEncoding(nn.Module):
    """TGAT-style harmonic time encoding: phi(dt) = cos(dt * w + b)."""

    def __init__(self, dim: int) -> None:
        super().__init__()
        # harmonic init spanning ~1 day .. ~10 years (dt measured in days)
        init = 1.0 / torch.logspace(0.0, math.log10(3650.0), dim)
        self.w = nn.Parameter(init)
        self.b = nn.Parameter(torch.zeros(dim))

    def forward(self, delta_t: torch.Tensor) -> torch.Tensor:
        return torch.cos(delta_t.unsqueeze(-1) * self.w + self.b)


class TemporalEgoAttention(nn.Module):
    def __init__(
        self,
        d_model: int = 48,
        n_heads: int = 2,
        d_time: int = 16,
        d_type: int = 12,
        n_scalars: int = 2,
    ) -> None:
        super().__init__()
        self.type_embedding = nn.Embedding(N_EVENT_TYPES, d_type)
        self.time_encoding = FunctionalTimeEncoding(d_time)
        self.edge_proj = nn.Linear(d_type + d_time + n_scalars, d_model)
        self.self_attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.norm1 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, 2 * d_model), nn.ReLU(), nn.Linear(2 * d_model, d_model)
        )
        self.norm2 = nn.LayerNorm(d_model)
        self.actor_proj = nn.Sequential(
            nn.Linear(N_ACTOR_FEATS, d_model), nn.ReLU(), nn.Linear(d_model, d_model)
        )
        self.pool_attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.head = nn.Sequential(
            nn.Linear(2 * d_model, 32), nn.ReLU(), nn.Linear(32, 1)
        )

    def forward(
        self,
        delta_t: torch.Tensor,  # (B, K)
        type_ids: torch.Tensor,  # (B, K)
        scalars: torch.Tensor,  # (B, K, 2)
        mask: torch.Tensor,  # (B, K) True = padding
        actor_feats: torch.Tensor,  # (B, F)
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Return (logits (B,), pooling attention weights (B, K))."""
        tokens = self.edge_proj(
            torch.cat(
                [
                    self.type_embedding(type_ids),
                    self.time_encoding(delta_t),
                    scalars,
                ],
                dim=-1,
            )
        )
        attended, _ = self.self_attn(
            tokens, tokens, tokens, key_padding_mask=mask, need_weights=False
        )
        tokens = self.norm1(tokens + attended)
        tokens = self.norm2(tokens + self.ffn(tokens))
        query = self.actor_proj(actor_feats).unsqueeze(1)  # (B, 1, D)
        pooled, attn_weights = self.pool_attn(
            query, tokens, tokens, key_padding_mask=mask, need_weights=True
        )
        pooled = pooled.squeeze(1)
        weights = attn_weights.squeeze(1)  # (B, K), averaged over heads
        logits = self.head(torch.cat([pooled, query.squeeze(1)], dim=-1)).squeeze(-1)
        return logits, weights


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
