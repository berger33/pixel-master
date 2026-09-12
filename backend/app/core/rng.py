"""RNG determinístico e utilidades de sorteio reproduzível.

O gerador procedural precisa produzir **exatamente** o mesmo sprite para o mesmo
``seed``, em qualquer máquina e qualquer versão do Python. Por isso evitamos o
módulo ``random`` global (estado compartilhado) e o ``hash()`` de strings
(sal aleatório por processo) em favor de uma função de hash inteira estável.
"""

from __future__ import annotations

import zlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeVar

__all__ = ["SeedRandom", "stable_hash", "T"]

T = TypeVar("T")

_MASK32 = 0xFFFFFFFF


def stable_hash(value: str) -> int:
    """Hash inteiro estável entre processos (substitui ``hash()``)."""
    return zlib.crc32(value.encode("utf-8")) & _MASK32


@dataclass
class SeedRandom:
    """Gerador pseudo-aleatório determinístico, isolado por instância.

    Implementa um xorshift32 — simples, rápido e suficiente para variação
    estética, onde não se exige qualidade criptográfica.
    """

    seed: int = 0
    _state: int = 0

    def __post_init__(self) -> None:
        self._state = (int(self.seed) & _MASK32) or 0x9E3779B9

    # ------------------------------------------------------------------
    def _next(self) -> int:
        x = self._state
        x ^= (x << 13) & _MASK32
        x ^= x >> 17
        x ^= (x << 5) & _MASK32
        self._state = x & _MASK32
        return self._state

    def random(self) -> float:
        """Float em ``[0, 1)``."""
        return self._next() / float(_MASK32 + 1)

    def randint(self, low: int, high: int) -> int:
        """Inteiro em ``[low, high]`` (inclusive)."""
        if high < low:
            low, high = high, low
        span = high - low + 1
        return low + int(self.random() * span) % span

    def uniform(self, low: float, high: float) -> float:
        return low + (high - low) * self.random()

    def choice(self, options: Sequence[T]) -> T:
        if not options:
            raise ValueError("sequence vazia")
        return options[self.randint(0, len(options) - 1)]

    def weighted_choice(self, options: Sequence[T], weights: Sequence[float]) -> T:
        if len(options) != len(weights):
            raise ValueError("options e weights precisam ter o mesmo tamanho")
        total = float(sum(weights))
        if total <= 0:
            return self.choice(options)
        target = self.random() * total
        acc = 0.0
        for option, weight in zip(options, weights, strict=True):
            acc += float(weight)
            if target <= acc:
                return option
        return options[-1]

    def chance(self, probability: float) -> bool:
        return self.random() < float(probability)

    def sample(self, options: Sequence[T], count: int) -> list[T]:
        pool = list(options)
        count = max(0, min(len(pool), int(count)))
        out: list[T] = []
        for _ in range(count):
            out.append(pool.pop(self.randint(0, len(pool) - 1)))
        return out

    def shuffle(self, options: Sequence[T]) -> list[T]:
        pool = list(options)
        for i in range(len(pool) - 1, 0, -1):
            j = self.randint(0, i)
            pool[i], pool[j] = pool[j], pool[i]
        return pool

    def fork(self, salt: str | int) -> SeedRandom:
        """Deriva um novo gerador independente a partir do estado atual."""
        if isinstance(salt, str):
            salt = stable_hash(salt)
        mixed = (self._state ^ (int(salt) * 2654435761)) & _MASK32
        return SeedRandom(seed=mixed or 1)


def seed_from_text(text: str) -> int:
    """Converte um nome/label em um seed estável."""
    return stable_hash(text.strip().lower())


def jitter(value: float, rng: SeedRandom, amount: float) -> float:
    return value + rng.uniform(-amount, amount)
