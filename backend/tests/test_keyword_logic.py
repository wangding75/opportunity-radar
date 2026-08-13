from app.services.keywords import canonicalize_keyword
from app.services.normalizer import normalize_text


def test_normalizers():
    assert normalize_text("  AI   short video  ") == "AI short video"
    assert canonicalize_keyword("  AI Short Video ") == "ai short video"


def test_chinese_candidate_segmentation_avoids_fixed_length_truncation():
    from app.services.keywords import _candidate_terms

    terms = _candidate_terms("AI短剧批量生成与多平台分发工具；短剧剪辑和矩阵运营")
    assert "AI短剧批量生成" in terms
    assert "多平台分发工具" in terms
    assert "短剧剪辑" in terms
    assert "矩阵运营" in terms
    assert "短剧批量生成与多" not in terms
