"""
Typst 생성기 v2: HTML → Typst 변환 기반
"""

import re
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from html.parser import HTMLParser

from .parser import ParsedDocument, Metadata


class HTMLToTypstConverter(HTMLParser):
    """HTML을 Typst로 변환"""

    def __init__(self):
        super().__init__()
        self.output = []
        self.list_stack = []  # 리스트 중첩 추적
        self.in_code_block = False
        self.code_content = []
        self.in_table = False
        self.table_rows = []
        self.current_row = []
        self.is_header_row = False
        self.in_blockquote = False
        self.blockquote_content = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag[1])
            self.output.append(f"\n{'=' * level} ")

        elif tag == 'p':
            if not self.in_table and not self.in_code_block:
                self.output.append('\n')

        elif tag == 'strong' or tag == 'b':
            self.output.append('*')

        elif tag == 'em' or tag == 'i':
            self.output.append('_')

        elif tag == 'code':
            if not self.in_code_block:
                self.output.append('`')

        elif tag == 'pre':
            self.in_code_block = True
            self.code_content = []

        elif tag == 'ul':
            self.list_stack.append('ul')

        elif tag == 'ol':
            self.list_stack.append('ol')

        elif tag == 'li':
            indent = '  ' * (len(self.list_stack) - 1)
            if self.list_stack and self.list_stack[-1] == 'ol':
                self.output.append(f'\n{indent}+ ')
            else:
                self.output.append(f'\n{indent}- ')

        elif tag == 'a':
            href = attrs_dict.get('href', '')
            self.output.append(f'#link("{href}")[')

        elif tag == 'table':
            self.in_table = True
            self.table_rows = []

        elif tag == 'thead':
            self.is_header_row = True

        elif tag == 'tbody':
            self.is_header_row = False

        elif tag == 'tr':
            self.current_row = []

        elif tag in ['th', 'td']:
            pass  # 텍스트에서 처리

        elif tag == 'blockquote':
            self.in_blockquote = True
            self.blockquote_content = []

        elif tag == 'br':
            self.output.append('\n')

    def handle_endtag(self, tag):
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.output.append('\n')

        elif tag == 'p':
            self.output.append('\n')

        elif tag == 'strong' or tag == 'b':
            self.output.append('*')

        elif tag == 'em' or tag == 'i':
            self.output.append('_')

        elif tag == 'code':
            if not self.in_code_block:
                self.output.append('`')

        elif tag == 'pre':
            self.in_code_block = False
            code = ''.join(self.code_content)
            # 코드 블록을 raw block으로 출력 (템플릿 폰트 설정 사용)
            self.output.append('\n```\n')
            self.output.append(code)
            self.output.append('\n```\n')

        elif tag == 'ul' or tag == 'ol':
            if self.list_stack:
                self.list_stack.pop()
            self.output.append('\n')

        elif tag == 'a':
            self.output.append(']')

        elif tag == 'table':
            self.in_table = False
            self._render_table()

        elif tag == 'tr':
            if self.current_row:
                self.table_rows.append((self.is_header_row, self.current_row))

        elif tag in ['th', 'td']:
            pass

        elif tag == 'blockquote':
            self.in_blockquote = False
            quote_text = ''.join(self.blockquote_content)
            self.output.append(f'\n#block(stroke: (left: 3pt + gray), inset: (left: 12pt, y: 8pt))[\n')
            self.output.append(f'#text(fill: rgb("#666666"))[{self._escape_typst(quote_text)}]\n')
            self.output.append(']\n')

    def handle_data(self, data):
        if self.in_code_block:
            self.code_content.append(data)
        elif self.in_table:
            # 테이블 셀에 데이터 추가
            cleaned = data.strip()
            if cleaned:
                self.current_row.append(cleaned)
        elif self.in_blockquote:
            self.blockquote_content.append(data)
        else:
            # 일반 텍스트
            escaped = self._escape_typst(data)
            self.output.append(escaped)

    def _escape_typst(self, text: str) -> str:
        """Typst 특수문자 이스케이프"""
        if not text:
            return ""
        # # $ @ * _ 등 이스케이프
        text = text.replace('\\', '\\\\')
        text = text.replace('#', '\\#')
        text = text.replace('$', '\\$')
        text = text.replace('@', '\\@')
        text = text.replace('<', '\\<')
        text = text.replace('>', '\\>')
        text = text.replace('*', '\\*')
        text = text.replace('_', '\\_')
        return text

    def _render_table(self):
        """테이블을 Typst로 렌더링"""
        if not self.table_rows:
            return

        # 열 개수 계산
        max_cols = max(len(row[1]) for row in self.table_rows) if self.table_rows else 0
        if max_cols == 0:
            return

        self.output.append(f'\n#table(\n')
        self.output.append(f'  columns: {max_cols},\n')
        self.output.append(f'  stroke: 0.5pt + rgb("#cccccc"),\n')
        self.output.append(f'  inset: 8pt,\n')
        self.output.append(f'  align: center,\n')

        for is_header, cells in self.table_rows:
            # 빈 셀 채우기
            while len(cells) < max_cols:
                cells.append('')

            for cell in cells:
                escaped_cell = self._escape_typst(cell)
                if is_header:
                    self.output.append(f'  [*{escaped_cell}*],\n')
                else:
                    self.output.append(f'  [{escaped_cell}],\n')

        self.output.append(')\n')

    def get_typst(self) -> str:
        return ''.join(self.output)


class TypstGenerator:
    """Typst 코드 생성 및 PDF 컴파일 v2"""

    def __init__(self, template_path: Optional[Path] = None):
        if template_path:
            self.template_path = Path(template_path)
        else:
            self.template_path = Path(__file__).parent.parent / "templates" / "report.typ"

    def generate(self, doc: ParsedDocument, output_path: Path, logo_path: Optional[Path] = None) -> Path:
        """파싱된 문서를 PDF로 생성"""
        # Typst 코드 생성
        typst_code = self._generate_typst_code(doc, logo_path)

        # 임시 디렉토리에서 컴파일
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # 템플릿 복사
            template_dest = tmp_path / "template.typ"
            shutil.copy(self.template_path, template_dest)

            # 메인 Typst 파일 생성
            main_file = tmp_path / "main.typ"
            main_file.write_text(typst_code, encoding="utf-8")

            # 로고 복사
            if logo_path and Path(logo_path).exists():
                logo_dest = tmp_path / Path(logo_path).name
                shutil.copy(logo_path, logo_dest)

            # PDF 컴파일
            output_pdf = tmp_path / "output.pdf"

            # typst 경로 찾기
            typst_path = shutil.which("typst") or str(Path.home() / ".local/bin/typst")

            result = subprocess.run(
                [typst_path, "compile", str(main_file), str(output_pdf)],
                capture_output=True,
                text=True,
                cwd=tmp_path
            )

            if result.returncode != 0:
                raise RuntimeError(f"Typst compilation failed: {result.stderr}")

            # 출력 경로로 복사
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(output_pdf, output_path)

        return output_path

    def _generate_typst_code(self, doc: ParsedDocument, logo_path: Optional[Path] = None) -> str:
        """Typst 코드 생성"""
        lines = []

        # 템플릿 임포트
        lines.append('#import "template.typ": *')
        lines.append("")

        # 문서 설정
        meta = doc.metadata
        logo_str = f'"{Path(logo_path).name}"' if logo_path else "none"

        lines.append("#show: report.with(")
        lines.append(f'  title: "{self._escape_string(meta.title)}",')
        lines.append(f'  subtitle: "{self._escape_string(meta.subtitle)}",')
        lines.append(f'  description: "{self._escape_string(meta.description)}",')
        lines.append(f'  project: "{self._escape_string(meta.project)}",')
        lines.append(f'  date: "{self._escape_string(meta.date)}",')
        lines.append(f'  version: "{self._escape_string(meta.version)}",')
        lines.append(f'  author: "{self._escape_string(meta.author)}",')
        lines.append(f'  confidential: {"true" if meta.confidential else "false"},')
        lines.append(f'  logo: {logo_str},')
        lines.append(")")
        lines.append("")

        # HTML → Typst 변환
        converter = HTMLToTypstConverter()
        converter.feed(doc.html_content)
        typst_body = converter.get_typst()

        lines.append(typst_body)

        return "\n".join(lines)

    def _escape_string(self, text: str) -> str:
        """문자열 이스케이프 (따옴표 안)"""
        if not text:
            return ""
        text = text.replace("\\", "\\\\")
        text = text.replace('"', '\\"')
        return text
