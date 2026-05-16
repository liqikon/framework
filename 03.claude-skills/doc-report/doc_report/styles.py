"""
스타일 정의 모듈
KB자산운용 AI기획 문서 스타일 기반
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from docx.shared import Pt, Inches, RGBColor, Cm, Twips


@dataclass
class ColorPalette:
    """색상 팔레트"""
    # 브랜드 색상
    brand_blue: str = "2B579A"

    # 텍스트 색상
    text_black: str = "1A1A1A"
    text_dark_gray: str = "333333"
    text_gray: str = "666666"
    text_light_gray: str = "999999"

    # 배경 색상
    bg_info: str = "F5F5F5"         # 정보 박스
    bg_warning: str = "FFF9C4"      # 경고 박스 (파스텔 노란색)
    bg_table_header: str = "E8E8E8"  # 표 헤더
    bg_white: str = "FFFFFF"

    # 테두리 색상
    border_gray: str = "CCCCCC"
    border_dark: str = "999999"

    def to_rgb(self, color: str) -> RGBColor:
        """HEX to RGBColor"""
        return RGBColor(
            int(color[0:2], 16),
            int(color[2:4], 16),
            int(color[4:6], 16)
        )


@dataclass
class FontConfig:
    """폰트 설정"""
    # 기본 폰트
    default_font: str = "맑은 고딕"
    fallback_font: str = "Arial"
    code_font: str = "Consolas"

    # 폰트 크기
    title_size: Pt = field(default_factory=lambda: Pt(36))
    subtitle_size: Pt = field(default_factory=lambda: Pt(28))
    h1_size: Pt = field(default_factory=lambda: Pt(24))
    h2_size: Pt = field(default_factory=lambda: Pt(18))
    h3_size: Pt = field(default_factory=lambda: Pt(14))
    body_size: Pt = field(default_factory=lambda: Pt(11))
    small_size: Pt = field(default_factory=lambda: Pt(10))
    caption_size: Pt = field(default_factory=lambda: Pt(9))


@dataclass
class PageConfig:
    """페이지 설정"""
    # A4 크기
    width: Inches = field(default_factory=lambda: Inches(8.27))
    height: Inches = field(default_factory=lambda: Inches(11.69))

    # 여백
    margin_top: Inches = field(default_factory=lambda: Inches(1.0))
    margin_bottom: Inches = field(default_factory=lambda: Inches(1.0))
    margin_left: Inches = field(default_factory=lambda: Inches(1.0))
    margin_right: Inches = field(default_factory=lambda: Inches(1.0))

    @property
    def content_width(self):
        """본문 콘텐츠 너비 (동적 계산)"""
        return self.width - self.margin_left - self.margin_right


@dataclass
class SpacingConfig:
    """간격 설정"""
    # 제목 간격
    h1_before: Pt = field(default_factory=lambda: Pt(24))
    h1_after: Pt = field(default_factory=lambda: Pt(12))
    h2_before: Pt = field(default_factory=lambda: Pt(18))
    h2_after: Pt = field(default_factory=lambda: Pt(8))
    h3_before: Pt = field(default_factory=lambda: Pt(12))
    h3_after: Pt = field(default_factory=lambda: Pt(6))

    # 본문 간격
    para_before: Pt = field(default_factory=lambda: Pt(0))
    para_after: Pt = field(default_factory=lambda: Pt(8))
    line_spacing: float = 1.15


@dataclass
class TableStyle:
    """표 스타일"""
    # 셀 패딩
    cell_padding_top: Twips = field(default_factory=lambda: Twips(80))
    cell_padding_bottom: Twips = field(default_factory=lambda: Twips(80))
    cell_padding_left: Twips = field(default_factory=lambda: Twips(120))
    cell_padding_right: Twips = field(default_factory=lambda: Twips(120))

    # 테두리
    border_size: int = 1  # pt
    border_color: str = "CCCCCC"

    # 헤더
    header_bg: str = "E8E8E8"
    header_bold: bool = True


@dataclass
class CalloutStyle:
    """콜아웃 박스 스타일"""
    # 정보 박스
    info_bg: str = "F5F5F5"
    info_border: str = "CCCCCC"
    info_icon: str = ""

    # 경고 박스 (정보 박스와 동일 그레이)
    warning_bg: str = "F5F5F5"
    warning_border: str = "CCCCCC"
    warning_icon: str = ""

    # 공통
    padding: Pt = field(default_factory=lambda: Pt(12))
    border_width: int = 1


@dataclass
class DocumentStyle:
    """문서 전체 스타일"""
    colors: ColorPalette = field(default_factory=ColorPalette)
    fonts: FontConfig = field(default_factory=FontConfig)
    page: PageConfig = field(default_factory=PageConfig)
    spacing: SpacingConfig = field(default_factory=SpacingConfig)
    table: TableStyle = field(default_factory=TableStyle)
    callout: CalloutStyle = field(default_factory=CalloutStyle)

    # 메타 설정
    toc_title: str = "0. 목차"
    confidential_text: str = "Confidential - Internal Use Only"

    # 번호 체계
    heading_numbering: bool = True
    heading_number_format: Dict[int, str] = field(default_factory=lambda: {
        1: "{n}.",      # "1."
        2: "{p}.{n}",   # "1.1"
        3: "{p}.{n}",   # "1.1.1"
    })


# 기본 스타일 인스턴스
DEFAULT_STYLE = DocumentStyle()


# KB자산운용 스타일 (커스텀)
KB_STYLE = DocumentStyle(
    colors=ColorPalette(
        brand_blue="2B579A",  # KB 블루
    ),
    fonts=FontConfig(
        default_font="Pretendard",
        fallback_font="맑은 고딕",
    ),
    page=PageConfig(
        margin_left=Inches(0.75),
        margin_right=Inches(0.75),
    ),
    heading_numbering=False,
)
