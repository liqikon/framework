"""
pdf-report CLI 엔트리 포인트
"""

import argparse
import sys
from pathlib import Path

from .parser import MarkdownParser
from .generator import TypstGenerator


def main():
    parser = argparse.ArgumentParser(
        description="마크다운을 전문 PDF 보고서로 변환 (Typst 기반)"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="입력 마크다운 파일 경로"
    )
    parser.add_argument(
        "output",
        type=Path,
        help="출력 PDF 파일 경로"
    )
    parser.add_argument(
        "--logo", "-l",
        type=Path,
        default=None,
        help="로고 이미지 경로 (선택)"
    )
    parser.add_argument(
        "--template", "-t",
        type=Path,
        default=None,
        help="커스텀 Typst 템플릿 경로 (선택)"
    )

    args = parser.parse_args()

    # 입력 파일 확인
    if not args.input.exists():
        print(f"오류: 입력 파일을 찾을 수 없습니다: {args.input}")
        sys.exit(1)

    # 마크다운 읽기
    markdown_text = args.input.read_text(encoding="utf-8")

    # 파싱
    md_parser = MarkdownParser()
    doc = md_parser.parse(markdown_text)

    # PDF 생성
    generator = TypstGenerator(template_path=args.template)
    try:
        output_path = generator.generate(
            doc,
            args.output,
            logo_path=args.logo
        )
        print(f"PDF 생성 완료: {output_path}")
    except RuntimeError as e:
        print(f"오류: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("오류: Typst가 설치되어 있지 않습니다. 'brew install typst'로 설치하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
