"""Modelos de secuencia (PyTorch): LSTM, GRU, CNN y Transformer.

Todos reciben (batch, ventana, dim) con dim = valores posibles codificados multi-hot
y devuelven logits (batch, dim) para el siguiente sorteo.
"""
from __future__ import annotations

import torch
from torch import nn

KINDS = ("lstm", "gru", "cnn", "transformer")


class RNNModel(nn.Module):
    def __init__(self, kind: str, dim: int, hidden: int, layers: int, dropout: float):
        super().__init__()
        rnn = {"lstm": nn.LSTM, "gru": nn.GRU}[kind]
        self.rnn = rnn(dim, hidden, num_layers=layers, batch_first=True,
                       dropout=dropout if layers > 1 else 0.0)
        self.drop = nn.Dropout(dropout)
        self.head = nn.Linear(hidden, dim)

    def forward(self, x):
        out, _ = self.rnn(x)
        return self.head(self.drop(out[:, -1]))


class CNNModel(nn.Module):
    def __init__(self, dim: int, hidden: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(dim, hidden, kernel_size=3, padding=1), nn.ReLU(),
            nn.Conv1d(hidden, hidden, kernel_size=3, padding=1), nn.ReLU(),
        )
        self.drop = nn.Dropout(dropout)
        self.head = nn.Linear(hidden, dim)

    def forward(self, x):
        h = self.net(x.transpose(1, 2))  # (B, hidden, T)
        return self.head(self.drop(h.mean(dim=2)))


class TransformerModel(nn.Module):
    def __init__(self, dim: int, window: int, hidden: int, layers: int, dropout: float, heads: int = 4):
        super().__init__()
        d_model = max(heads, (hidden // heads) * heads)  # divisible por nº de cabezas
        self.inp = nn.Linear(dim, d_model)
        self.pos = nn.Parameter(torch.zeros(1, window, d_model))
        nn.init.normal_(self.pos, std=0.02)
        layer = nn.TransformerEncoderLayer(d_model, heads, dim_feedforward=d_model * 2,
                                           dropout=dropout, batch_first=True)
        self.enc = nn.TransformerEncoder(layer, layers)
        self.drop = nn.Dropout(dropout)
        self.head = nn.Linear(d_model, dim)

    def forward(self, x):
        h = self.enc(self.inp(x) + self.pos[:, : x.shape[1]])
        return self.head(self.drop(h[:, -1]))


def build_model(kind: str, dim: int, window: int, hidden: int = 64,
                layers: int = 1, dropout: float = 0.2) -> nn.Module:
    kind = kind.lower()
    if kind in ("lstm", "gru"):
        return RNNModel(kind, dim, hidden, layers, dropout)
    if kind == "cnn":
        return CNNModel(dim, hidden, dropout)
    if kind == "transformer":
        return TransformerModel(dim, window, hidden, max(layers, 1), dropout)
    raise ValueError(f"Modelo desconocido: {kind!r}. Opciones: {KINDS}")
