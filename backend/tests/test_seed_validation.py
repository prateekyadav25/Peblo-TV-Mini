import pytest
from app.services.validation_service import SeedValidator

@pytest.fixture
def ref_data():
    return {
        "sections": ["featured", "series"],
        "categories": ["adventure", "learning"],
        "languages": ["en", "hi"]
    }

def test_missing_section_published(ref_data):
    seed_data = [{
        "episode_id": "ep_1",
        "show_title": "Show 1",
        "slug": "show-1",
        "section": None,
        "categories": ["adventure"],
        "status": "published",
        "duration_seconds": 100,
        "language": "en",
        "content_group": "show1-s01e01",
        "artwork_available": ["poster"]
    }]
    validator = SeedValidator(ref_data, seed_data)
    report = validator.validate()
    assert len(report['errors']) == 1
    assert report['errors'][0]['field'] == 'section'

def test_missing_section_draft(ref_data):
    seed_data = [{
        "episode_id": "ep_1",
        "show_title": "Show 1",
        "slug": "show-1",
        "section": None,
        "categories": ["adventure"],
        "status": "draft",
        "duration_seconds": 100,
        "language": "en",
        "content_group": "show1-s01e01",
        "artwork_available": ["poster"]
    }]
    validator = SeedValidator(ref_data, seed_data)
    report = validator.validate()
    # It should be a warning, not an error
    assert len(report['errors']) == 0
    assert len(report['warnings']) == 1
    assert report['warnings'][0]['field'] == 'section'

def test_duplicate_cg_lang(ref_data):
    seed_data = [
        {
            "episode_id": "ep_1",
            "show_title": "Show 1",
            "slug": "show-1",
            "section": "series",
            "categories": [],
            "status": "draft",
            "duration_seconds": 100,
            "language": "en",
            "content_group": "cg1",
            "artwork_available": ["poster"]
        },
        {
            "episode_id": "ep_2",
            "show_title": "Show 1",
            "slug": "show-1",
            "section": "series",
            "categories": [],
            "status": "draft",
            "duration_seconds": 100,
            "language": "en",
            "content_group": "cg1",
            "artwork_available": ["poster"]
        }
    ]
    validator = SeedValidator(ref_data, seed_data)
    report = validator.validate()
    assert len(report['errors']) == 1
    assert report['errors'][0]['field'] == 'content_group + language'

def test_published_missing_artwork(ref_data):
    seed_data = [{
        "episode_id": "ep_1",
        "show_title": "Show 1",
        "slug": "show-1",
        "section": "series",
        "categories": [],
        "status": "published",
        "duration_seconds": 100,
        "language": "en",
        "content_group": "cg1",
        "artwork_available": []
    }]
    validator = SeedValidator(ref_data, seed_data)
    report = validator.validate()
    assert len(report['errors']) == 1
    assert report['errors'][0]['field'] == 'artwork_available'

def test_casing_warnings(ref_data):
    seed_data = [{
        "episode_id": "ep_1",
        "show_title": "Show 1",
        "slug": "show-1",
        "section": "series",
        "categories": [],
        "status": "draft",
        "duration_seconds": 100,
        "language": "en",
        "content_group": "cg1",
        "episode_title": "ALL CAPS",
        "artwork_available": ["poster"]
    }]
    validator = SeedValidator(ref_data, seed_data)
    report = validator.validate()
    assert any(w['field'] == 'episode_title' for w in report['warnings'])
