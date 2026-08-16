from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class WordTiming:
    word: str
    start: float
    end: float
    confidence: Optional[float] = None


@dataclass
class NormalizedToken:
    original: str
    normalized: str
    source: str  # "transcript" | "timing" | "query"
    index: int
    start: Optional[float] = None
    end: Optional[float] = None
    confidence: Optional[float] = None
    is_filler: bool = False


@dataclass
class AlignmentPair:
    transcript_token: Optional[NormalizedToken]
    timing_token: Optional[NormalizedToken]
    relation: str  # match | mismatch | insertion | deletion | split_merge


@dataclass
class Conflict:
    type: str
    details: Dict[str, Any]
    decision: str
    reason: str


@dataclass
class BoundaryDecision:
    start_time: float
    end_time: float
    start_word: str
    end_word: str
    trusted_source_for_edges: str
    trusted_source_for_phrase_identity: str
    confidence: float
    reasoning: List[str] = field(default_factory=list)


@dataclass
class AgentResult:
    phrase: str
    start_time: float
    end_time: float
    start_frame: int
    end_frame: int
    output_path: Optional[str]
    conflicts: List[Conflict]
    log: Dict[str, Any]
