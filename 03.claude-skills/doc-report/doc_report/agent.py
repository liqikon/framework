"""
doc-report 메인 에이전트
"""

from pathlib import Path
from typing import Optional

from .parser import MarkdownParser
from .generator import DocxGenerator
from .styles import DocumentStyle, DEFAULT_STYLE, KB_STYLE


class DocReportAgent:
    """문서 보고서 생성 에이전트"""

    # 사전 정의된 스타일
    STYLES = {
        'default': DEFAULT_STYLE,
        'kb': KB_STYLE,
    }

    def __init__(self, style: str = 'default'):
        """
        Args:
            style: 스타일 이름 ('default', 'kb') 또는 DocumentStyle 객체
        """
        if isinstance(style, str):
            self.style = self.STYLES.get(style, DEFAULT_STYLE)
        else:
            self.style = style

    def convert(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        logo: Optional[str] = None
    ) -> str:
        """
        마크다운 파일을 DOCX로 변환

        Args:
            input_path: 입력 마크다운 파일 경로
            output_path: 출력 DOCX 파일 경로 (없으면 자동 생성)
            logo: 표지 로고 이미지 경로

        Returns:
            생성된 DOCX 파일 경로
        """
        input_file = Path(input_path)

        if not input_file.exists():
            raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")

        # 출력 경로 결정
        if output_path is None:
            output_path = str(input_file.with_suffix('.docx'))

        # 마크다운 읽기
        with open(input_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 변환 실행
        result_path = self.convert_text(md_content, output_path, logo)

        return result_path

    def convert_text(
        self,
        markdown_text: str,
        output_path: str,
        logo: Optional[str] = None
    ) -> str:
        """
        마크다운 텍스트를 DOCX로 변환

        Args:
            markdown_text: 마크다운 텍스트
            output_path: 출력 DOCX 파일 경로
            logo: 표지 로고 이미지 경로

        Returns:
            생성된 DOCX 파일 경로
        """
        # 1. 파싱
        parser = MarkdownParser(markdown_text)
        metadata, blocks = parser.parse()

        # 로고 경로 오버라이드
        if logo and metadata:
            metadata.logo = logo

        # 2. 생성
        generator = DocxGenerator(self.style)
        generator.generate(metadata, blocks)

        # 3. 저장
        generator.save(output_path)

        return output_path


def main():
    """CLI 엔트리 포인트"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description='마크다운을 전문적인 보고서 스타일의 Word 문서로 변환'
    )
    parser.add_argument('input', help='입력 마크다운 파일')
    parser.add_argument('output', nargs='?', help='출력 DOCX 파일 (선택)')
    parser.add_argument('--style', '-s', default='default',
                        choices=['default', 'kb'],
                        help='문서 스타일 (default: default)')
    parser.add_argument('--logo', '-l', help='표지 로고 이미지 경로')

    args = parser.parse_args()

    try:
        agent = DocReportAgent(style=args.style)
        result = agent.convert(
            args.input,
            args.output,
            logo=args.logo
        )
        print(f"✅ 문서 생성 완료: {result}")
    except Exception as e:
        print(f"❌ 오류: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
