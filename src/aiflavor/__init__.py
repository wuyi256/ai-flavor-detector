"""ai-flavor-detector: 检测一段文字的「AI 味」浓度。"""

from .analyzer import Analysis, Hit, analyze

__all__ = ["analyze", "Analysis", "Hit"]
__version__ = "0.4.0"
