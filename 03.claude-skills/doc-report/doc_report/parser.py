"""
마크다운 파서 모듈
확장 문법 지원 (YAML 메타데이터, 콜아웃, 플로우 다이어그램)
"""

import re
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class BlockType(Enum):
    """블록 타입"""
    METADATA = "metadata"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    CODE = "code"
    QUOTE = "quote"
    CALLOUT_INFO = "callout_info"
    CALLOUT_WARNING = "callout_warning"
    FLOW = "flow"
    HORIZONTAL_RULE = "hr"
    PAGE_BREAK = "pagebreak"
    IMAGE = "image"


@dataclass
class DocumentMetadata:
    """문서 메타데이터"""
    title: str = ""
    subtitle: str = ""
    description: str = ""
    project: str = ""
    date: str = ""
    version: str = ""
    author: str = ""
    confidential: bool = True
    logo: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentMetadata':
        return cls(
            title=data.get('title', ''),
            subtitle=data.get('subtitle', ''),
            description=data.get('description', ''),
            project=data.get('project', ''),
            date=str(data.get('date', '')),
            version=data.get('version', ''),
            author=data.get('author', ''),
            confidential=data.get('confidential', True),
            logo=data.get('logo'),
        )


@dataclass
class ParsedBlock:
    """파싱된 블록"""
    type: BlockType
    content: Any
    level: int = 0  # 제목/목록 레벨
    raw: str = ""   # 원본 텍스트


@dataclass
class TableCell:
    """표 셀"""
    content: str
    is_header: bool = False
    align: str = "left"  # left, center, right


@dataclass
class ParsedTable:
    """파싱된 표"""
    headers: List[str]
    rows: List[List[str]]
    alignments: List[str]


@dataclass
class FlowItem:
    """플로우 다이어그램 아이템"""
    text: str
    is_arrow: bool = False


@dataclass
class ParsedFlow:
    """파싱된 플로우 다이어그램"""
    caption: str
    items: List[FlowItem]


class MarkdownParser:
    """마크다운 파서"""

    # 정규식 패턴
    YAML_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    LIST_PATTERN = re.compile(r'^(\s*)[-*]\s+(.+)$')
    NUMBERED_LIST_PATTERN = re.compile(r'^(\s*)(\d+)\.\s+(.+)$')
    TABLE_ROW_PATTERN = re.compile(r'^\|(.+)\|$')
    TABLE_SEPARATOR_PATTERN = re.compile(r'^\|[\s\-:|]+\|$')
    CALLOUT_START_PATTERN = re.compile(r'^:::(info|warning)\s*(.*)$')
    CALLOUT_END_PATTERN = re.compile(r'^:::$')
    FLOW_START_PATTERN = re.compile(r'^:::flow\s+(.+)$')
    CODE_BLOCK_PATTERN = re.compile(r'^```')
    QUOTE_PATTERN = re.compile(r'^\s*>\s*(.*)$')
    HR_PATTERN = re.compile(r'^---+$')
    PAGEBREAK_PATTERN = re.compile(r'^<!--\s*pagebreak\s*-->')
    IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    # 인라인 패턴
    BOLD_PATTERN = re.compile(r'\*\*([^*]+)\*\*')
    ITALIC_PATTERN = re.compile(r'\*([^*]+)\*')
    CODE_INLINE_PATTERN = re.compile(r'`([^`]+)`')
    LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

    def __init__(self, text: str):
        self.text = text
        self.metadata: Optional[DocumentMetadata] = None
        self.blocks: List[ParsedBlock] = []

    def parse(self) -> Tuple[Optional[DocumentMetadata], List[ParsedBlock]]:
        """마크다운 파싱"""
        text = self.text

        # 0. 전처리: LaTeX 화살표, HTML 태그 변환
        text = self._preprocess(text)

        # 1. YAML 메타데이터 추출
        text = self._extract_metadata(text)

        # 2. 블록 단위로 파싱
        self._parse_blocks(text)

        return self.metadata, self.blocks

    def _preprocess(self, text: str) -> str:
        """전처리: LaTeX 화살표, HTML 태그 변환"""
        # LaTeX 화살표 → 유니코드
        # $\rightarrow$ 형태 (실제 파일: $\ + rightarrow + $)
        text = re.sub(r'\$\\rightarrow\$', '→', text)
        text = re.sub(r'\$\\leftarrow\$', '←', text)
        text = re.sub(r'\$\\leftrightarrow\$', '↔', text)
        # \rightarrow 단독 형태
        text = re.sub(r'\\rightarrow', '→', text)
        text = re.sub(r'\\leftarrow', '←', text)
        text = re.sub(r'\\leftrightarrow', '↔', text)
        # $ 기호만 남은 경우 제거
        text = re.sub(r'\$\s*→\s*\$', '→', text)
        text = re.sub(r'\$\s*←\s*\$', '←', text)
        text = re.sub(r'\$\s*↔\s*\$', '↔', text)

        # HTML <br> 태그 → 공백 (테이블 셀 내부용)
        text = re.sub(r'<br\s*/?>', ' ', text, flags=re.IGNORECASE)

        return text

    def _extract_metadata(self, text: str) -> str:
        """YAML 메타데이터 추출"""
        match = self.YAML_PATTERN.match(text)
        if match:
            yaml_content = match.group(1)
            try:
                data = yaml.safe_load(yaml_content)
                self.metadata = DocumentMetadata.from_dict(data)
            except yaml.YAMLError:
                pass
            return text[match.end():]
        return text

    def _parse_blocks(self, text: str):
        """블록 파싱"""
        lines = text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # 빈 줄 스킵
            if not line.strip():
                i += 1
                continue

            # 페이지 나누기
            if self.PAGEBREAK_PATTERN.match(line.strip()):
                self.blocks.append(ParsedBlock(
                    type=BlockType.PAGE_BREAK,
                    content=None,
                    raw=line
                ))
                i += 1
                continue

            # 수평선
            if self.HR_PATTERN.match(line.strip()):
                self.blocks.append(ParsedBlock(
                    type=BlockType.HORIZONTAL_RULE,
                    content=None,
                    raw=line
                ))
                i += 1
                continue

            # 제목
            heading_match = self.HEADING_PATTERN.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2).strip()
                self.blocks.append(ParsedBlock(
                    type=BlockType.HEADING,
                    content=content,
                    level=level,
                    raw=line
                ))
                i += 1
                continue

            # 콜아웃 시작
            callout_match = self.CALLOUT_START_PATTERN.match(line.strip())
            if callout_match:
                callout_type = callout_match.group(1)
                callout_title = callout_match.group(2).strip()
                i, content = self._parse_callout(lines, i + 1)
                block_type = BlockType.CALLOUT_INFO if callout_type == 'info' else BlockType.CALLOUT_WARNING
                self.blocks.append(ParsedBlock(
                    type=block_type,
                    content={'title': callout_title, 'body': content},
                    raw=line
                ))
                continue

            # 플로우 다이어그램
            flow_match = self.FLOW_START_PATTERN.match(line.strip())
            if flow_match:
                caption = flow_match.group(1).strip()
                i, flow_content = self._parse_callout(lines, i + 1)
                flow = self._parse_flow_content(caption, flow_content)
                self.blocks.append(ParsedBlock(
                    type=BlockType.FLOW,
                    content=flow,
                    raw=line
                ))
                continue

            # 코드 블록
            if self.CODE_BLOCK_PATTERN.match(line.strip()):
                i, code_content = self._parse_code_block(lines, i)
                self.blocks.append(ParsedBlock(
                    type=BlockType.CODE,
                    content=code_content,
                    raw=line
                ))
                continue

            # 표
            if self.TABLE_ROW_PATTERN.match(line.strip()):
                i, table = self._parse_table(lines, i)
                if table:
                    self.blocks.append(ParsedBlock(
                        type=BlockType.TABLE,
                        content=table,
                        raw=line
                    ))
                continue

            # 인용구 블록 (> 로 시작)
            quote_match = self.QUOTE_PATTERN.match(line)
            if quote_match:
                i, quote_content = self._parse_quote(lines, i)
                self.blocks.append(ParsedBlock(
                    type=BlockType.QUOTE,
                    content=quote_content,
                    raw=line
                ))
                continue

            # 목록
            list_match = self.LIST_PATTERN.match(line)
            num_list_match = self.NUMBERED_LIST_PATTERN.match(line)
            if list_match or num_list_match:
                i, list_items = self._parse_list(lines, i)
                self.blocks.append(ParsedBlock(
                    type=BlockType.LIST,
                    content=list_items,
                    raw=line
                ))
                continue

            # 이미지
            img_match = self.IMAGE_PATTERN.search(line)
            if img_match and line.strip().startswith('!'):
                self.blocks.append(ParsedBlock(
                    type=BlockType.IMAGE,
                    content={'alt': img_match.group(1), 'src': img_match.group(2)},
                    raw=line
                ))
                i += 1
                continue

            # 일반 단락
            i, para_content = self._parse_paragraph(lines, i)
            if para_content.strip():
                self.blocks.append(ParsedBlock(
                    type=BlockType.PARAGRAPH,
                    content=para_content,
                    raw=line
                ))

    def _parse_callout(self, lines: List[str], start: int) -> Tuple[int, str]:
        """콜아웃/플로우 내용 파싱"""
        content_lines = []
        i = start
        while i < len(lines):
            if self.CALLOUT_END_PATTERN.match(lines[i].strip()):
                i += 1
                break
            content_lines.append(lines[i])
            i += 1
        return i, '\n'.join(content_lines)

    def _parse_code_block(self, lines: List[str], start: int) -> Tuple[int, str]:
        """코드 블록 파싱"""
        content_lines = []
        i = start + 1  # ``` 다음 줄부터
        while i < len(lines):
            if self.CODE_BLOCK_PATTERN.match(lines[i].strip()):
                i += 1
                break
            content_lines.append(lines[i])
            i += 1
        return i, '\n'.join(content_lines)

    def _parse_table(self, lines: List[str], start: int) -> Tuple[int, Optional[ParsedTable]]:
        """표 파싱"""
        table_lines = []
        i = start

        while i < len(lines) and self.TABLE_ROW_PATTERN.match(lines[i].strip()):
            table_lines.append(lines[i].strip())
            i += 1

        if len(table_lines) < 2:
            return i, None

        # 헤더
        headers = [cell.strip() for cell in table_lines[0].strip('|').split('|')]

        # 구분선에서 정렬 정보 추출
        alignments = []
        if self.TABLE_SEPARATOR_PATTERN.match(table_lines[1]):
            sep_cells = table_lines[1].strip('|').split('|')
            for cell in sep_cells:
                cell = cell.strip()
                if cell.startswith(':') and cell.endswith(':'):
                    alignments.append('center')
                elif cell.endswith(':'):
                    alignments.append('right')
                else:
                    alignments.append('left')
            row_start = 2
        else:
            alignments = ['left'] * len(headers)
            row_start = 1

        # 데이터 행
        rows = []
        for line in table_lines[row_start:]:
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            rows.append(cells)

        return i, ParsedTable(headers=headers, rows=rows, alignments=alignments)

    def _parse_list(self, lines: List[str], start: int) -> Tuple[int, List[Dict]]:
        """목록 파싱"""
        items = []
        i = start

        while i < len(lines):
            line = lines[i]

            # 불릿 목록
            match = self.LIST_PATTERN.match(line)
            if match:
                indent = len(match.group(1))
                content = match.group(2)
                items.append({
                    'type': 'bullet',
                    'level': indent // 2,
                    'content': content
                })
                i += 1
                continue

            # 번호 목록
            num_match = self.NUMBERED_LIST_PATTERN.match(line)
            if num_match:
                indent = len(num_match.group(1))
                number = num_match.group(2)
                content = num_match.group(3)
                items.append({
                    'type': 'number',
                    'level': indent // 2,
                    'number': int(number),
                    'content': content
                })
                i += 1
                continue

            # 목록 끝
            break

        return i, items

    def _parse_quote(self, lines: List[str], start: int) -> Tuple[int, str]:
        """인용구 블록 파싱"""
        quote_lines = []
        i = start

        while i < len(lines):
            line = lines[i]
            match = self.QUOTE_PATTERN.match(line)
            if match:
                # > 제거하고 내용만 추출
                quote_lines.append(match.group(1))
                i += 1
            else:
                # 빈 줄이면 인용구 계속 확인
                if not line.strip():
                    # 다음 줄이 인용구인지 확인
                    if i + 1 < len(lines) and self.QUOTE_PATTERN.match(lines[i + 1]):
                        quote_lines.append('')  # 빈 줄 유지
                        i += 1
                        continue
                break

        return i, '\n'.join(quote_lines)

    def _parse_paragraph(self, lines: List[str], start: int) -> Tuple[int, str]:
        """단락 파싱"""
        para_lines = []
        i = start

        while i < len(lines):
            line = lines[i]

            # 빈 줄이면 단락 끝
            if not line.strip():
                i += 1
                break

            # 다른 블록 시작이면 단락 끝
            if (self.HEADING_PATTERN.match(line) or
                self.LIST_PATTERN.match(line) or
                self.NUMBERED_LIST_PATTERN.match(line) or
                self.QUOTE_PATTERN.match(line) or
                self.TABLE_ROW_PATTERN.match(line.strip()) or
                self.CALLOUT_START_PATTERN.match(line.strip()) or
                self.FLOW_START_PATTERN.match(line.strip()) or
                self.CODE_BLOCK_PATTERN.match(line.strip()) or
                self.HR_PATTERN.match(line.strip()) or
                self.PAGEBREAK_PATTERN.match(line.strip())):
                break

            para_lines.append(line)
            i += 1

        return i, ' '.join(para_lines)

    def _parse_flow_content(self, caption: str, content: str) -> ParsedFlow:
        """플로우 다이어그램 내용 파싱"""
        items = []

        # 화살표로 분리
        parts = re.split(r'\s*->\s*', content.strip())

        for i, part in enumerate(parts):
            if part.strip():
                items.append(FlowItem(text=part.strip()))
                if i < len(parts) - 1:
                    items.append(FlowItem(text='→', is_arrow=True))

        return ParsedFlow(caption=caption, items=items)

    @staticmethod
    def parse_inline(text: str) -> List[Dict]:
        """인라인 서식 파싱"""
        result = []
        pos = 0

        # 패턴 매칭을 위한 통합 정규식
        combined_pattern = re.compile(
            r'(\*\*([^*]+)\*\*)|'  # bold
            r'(\*([^*]+)\*)|'       # italic
            r'(`([^`]+)`)|'         # code
            r'(\[([^\]]+)\]\(([^)]+)\))'  # link
        )

        for match in combined_pattern.finditer(text):
            # 매치 전 일반 텍스트
            if match.start() > pos:
                result.append({
                    'type': 'text',
                    'content': text[pos:match.start()]
                })

            if match.group(1):  # bold
                result.append({
                    'type': 'bold',
                    'content': match.group(2)
                })
            elif match.group(3):  # italic
                result.append({
                    'type': 'italic',
                    'content': match.group(4)
                })
            elif match.group(5):  # code
                result.append({
                    'type': 'code',
                    'content': match.group(6)
                })
            elif match.group(7):  # link
                result.append({
                    'type': 'link',
                    'content': match.group(8),
                    'url': match.group(9)
                })

            pos = match.end()

        # 남은 텍스트
        if pos < len(text):
            result.append({
                'type': 'text',
                'content': text[pos:]
            })

        return result if result else [{'type': 'text', 'content': text}]
