"""
마크다운 파서 v2: markdown 라이브러리 기반 견고한 파싱
"""

import re
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
import markdown
from markdown.extensions import tables, fenced_code, toc


@dataclass
class Metadata:
    """문서 메타데이터"""
    title: str = "제목 없음"
    subtitle: str = ""
    description: str = ""
    project: str = ""
    date: str = ""
    version: str = "v1.0"
    author: str = ""
    confidential: bool = True
    logo: str = ""


@dataclass
class ParsedDocument:
    """파싱된 문서"""
    metadata: Metadata
    html_content: str
    raw_markdown: str


class MarkdownParser:
    """마크다운 파서 v2"""

    def __init__(self):
        # markdown 확장 설정
        self.md = markdown.Markdown(
            extensions=[
                'tables',
                'fenced_code',
                'toc',
                'nl2br',
                'sane_lists',
            ]
        )

    def parse(self, markdown_text: str) -> ParsedDocument:
        """마크다운 텍스트를 파싱"""
        # 전처리: LaTeX, 해시태그 등 변환
        processed_text = self._preprocess(markdown_text)

        # 메타데이터 추출
        metadata = self._extract_metadata(processed_text)

        # HTML 변환
        self.md.reset()
        html_content = self.md.convert(processed_text)

        return ParsedDocument(
            metadata=metadata,
            html_content=html_content,
            raw_markdown=processed_text
        )

    def _preprocess(self, text: str) -> str:
        """전처리: 특수 문법 변환"""
        # LaTeX 화살표 → 유니코드
        text = re.sub(r'\$\\rightarrow\$', '→', text)
        text = re.sub(r'\\rightarrow', '→', text)
        text = re.sub(r'\$\\leftarrow\$', '←', text)
        text = re.sub(r'\\leftarrow', '←', text)
        text = re.sub(r'\$\\leftrightarrow\$', '↔', text)

        # 들여쓰기된 코드블록 정규화 (리스트 내부 코드블록 처리)
        text = self._normalize_code_blocks(text)

        # 본문 내 해시태그 보호 (제목 # 제외)
        # 줄 시작이 아닌 #태그 → \#태그
        lines = text.split('\n')
        processed_lines = []
        for line in lines:
            # 제목 줄이 아닌 경우에만 해시태그 이스케이프
            if not re.match(r'^#{1,6}\s', line):
                # 공백 뒤의 #한글/영문 패턴
                line = re.sub(r'(\s)#([가-힣a-zA-Z])', r'\1\\#\2', line)
            processed_lines.append(line)

        return '\n'.join(processed_lines)

    def _normalize_code_blocks(self, text: str) -> str:
        """들여쓰기된 코드블록을 정규화"""
        lines = text.split('\n')
        result = []
        in_code_block = False
        code_block_content = []
        code_block_indent = 0
        code_block_lang = ''

        for line in lines:
            # 코드블록 시작 감지 (들여쓰기 포함)
            start_match = re.match(r'^(\s*)```(\w*)$', line)
            if start_match and not in_code_block:
                in_code_block = True
                code_block_indent = len(start_match.group(1))
                code_block_lang = start_match.group(2)
                code_block_content = []
                continue

            # 코드블록 종료 감지
            end_match = re.match(r'^\s*```\s*$', line)
            if end_match and in_code_block:
                in_code_block = False
                # 정규화된 코드블록 출력 (들여쓰기 제거)
                result.append(f'\n```{code_block_lang}')
                for content_line in code_block_content:
                    # 들여쓰기 제거
                    if len(content_line) >= code_block_indent:
                        result.append(content_line[code_block_indent:])
                    else:
                        result.append(content_line.lstrip())
                result.append('```\n')
                continue

            if in_code_block:
                code_block_content.append(line)
            else:
                result.append(line)

        return '\n'.join(result)

    def _extract_metadata(self, text: str) -> Metadata:
        """메타데이터 추출 (YAML 또는 본문에서)"""
        metadata = Metadata()

        # 1. YAML 프론트매터 시도
        yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
        if yaml_match:
            try:
                data = yaml.safe_load(yaml_match.group(1))
                if data:
                    metadata.title = data.get('title', metadata.title)
                    metadata.subtitle = data.get('subtitle', '')
                    metadata.description = data.get('description', '')
                    metadata.project = data.get('project', '')
                    metadata.date = str(data.get('date', ''))
                    metadata.version = data.get('version', 'v1.0')
                    metadata.author = data.get('author', '')
                    metadata.confidential = data.get('confidential', True)
                    metadata.logo = data.get('logo', '')
                    return metadata
            except yaml.YAMLError:
                pass

        # 2. 본문에서 추출 (YAML 없는 경우)
        lines = text.split('\n')

        # 첫 번째 H1 제목을 title로
        for line in lines[:20]:
            h1_match = re.match(r'^#\s+(.+)$', line)
            if h1_match:
                metadata.title = h1_match.group(1).strip()
                break

        # **키**: 값 형식에서 메타데이터 추출
        for line in lines[:30]:
            # **버전**: v0.99 형식
            version_match = re.search(r'\*\*버전\*\*[:\s]+([^\s]+)', line)
            if version_match:
                metadata.version = version_match.group(1)

            # **작성일**: 2026년 1월 30일 형식
            date_match = re.search(r'\*\*작성일\*\*[:\s]+(.+?)(?:\s{2,}|\*\*|$)', line)
            if date_match:
                metadata.date = date_match.group(1).strip()

            # **프로젝트명**: ... 형식
            project_match = re.search(r'\*\*프로젝트명\*\*[:\s]+(.+?)(?:\s{2,}|\*\*|$)', line)
            if project_match:
                metadata.project = project_match.group(1).strip()

            # **작성자**: ... 형식
            author_match = re.search(r'\*\*작성자?\*\*[:\s]+(.+?)(?:\s{2,}|\*\*|$)', line)
            if author_match:
                metadata.author = author_match.group(1).strip()

        return metadata
