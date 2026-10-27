"""Tests for Zoom validators."""

import cgi
import io

from PIL import Image
import pytest

from zoom.validators import image_mime_type_valid


def image_bytes(image_format):
    """Return a small valid image in the requested format."""
    stream = io.BytesIO()
    mode = '1' if image_format == 'XBM' else 'RGB'
    Image.new(mode, (2, 2)).save(stream, format=image_format)
    return stream.getvalue()


def uploaded_file(data):
    """Build the upload shape currently accepted by the validator."""
    upload = object.__new__(cgi.FieldStorage)
    upload.file = io.BytesIO(data)
    return upload


def test_image_upload_validation_preserves_stream_position():
    upload = uploaded_file(image_bytes('PNG'))
    stream = upload.file
    assert stream is not None
    stream.seek(5)

    assert image_mime_type_valid(upload)
    assert stream.tell() == 5


@pytest.mark.parametrize('image_format', ['GIF', 'JPEG', 'PNG', 'XBM', 'BMP'])
def test_image_validation_accepts_browser_supported_formats(image_format):
    data = image_bytes(image_format)

    assert image_mime_type_valid(data)
    assert image_mime_type_valid(uploaded_file(data))


def test_image_validation_rejects_unsupported_format():
    assert not image_mime_type_valid(image_bytes('TIFF'))


@pytest.mark.parametrize('data', [b'not an image', b'\x89PNG\r\n\x1a\n'])
def test_image_validation_rejects_invalid_or_truncated_data(data):
    assert not image_mime_type_valid(data)


@pytest.mark.parametrize('data', [None, '', b''])
def test_image_validation_allows_empty_values(data):
    assert image_mime_type_valid(data)


def test_image_validation_rejects_nonempty_text():
    assert not image_mime_type_valid('image.png')


def test_image_validation_rejects_decompression_bomb(monkeypatch):
    data = image_bytes('PNG')
    monkeypatch.setattr(Image, 'MAX_IMAGE_PIXELS', 1)

    assert not image_mime_type_valid(data)
