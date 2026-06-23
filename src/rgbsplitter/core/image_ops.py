from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from PIL import Image

CHANNELS = ("R", "G", "B", "A")
CHANNEL_ITEMS = ("None", "White", "Black", "Gray")
SEPARATOR_ITEM = "-" * 40
EMPTY_ITEM = "-"
DEFAULT_IMAGE_SIZE = 4096
ImageSize = int | tuple[int, int]


@dataclass(frozen=True)
class MixSelection:
    image_name: str
    source_channel: str


@dataclass(frozen=True)
class MergeSelection:
    image_name: str


@dataclass(frozen=True)
class SplitSelection:
    image_name: str
    source_channel: str
    suffix: str = ""


@dataclass(frozen=True)
class CachedImage:
    path: Path
    image: Image.Image


ImageInput = str | Path | CachedImage


def load_cached_image(image_path: str | Path) -> CachedImage | None:
    path = Path(image_path)
    try:
        with Image.open(path) as image:
            return CachedImage(path=path, image=image.copy())
    except OSError as error:
        print(f"[WARN] Could not load image into cache: {path} ({error})")
        return None


def image_display_name(image_path: ImageInput) -> str:
    return _source_path(image_path).stem


def channel_items(image_paths: Iterable[ImageInput], include_special_items: bool = True) -> list[str]:
    items: list[str] = []
    if include_special_items:
        items.extend(CHANNEL_ITEMS)
        items.append(SEPARATOR_ITEM)
    items.extend(image_display_name(path) for path in image_paths)
    return items


def split_items(image_paths: Iterable[ImageInput]) -> list[str]:
    return [EMPTY_ITEM, *(image_display_name(path) for path in image_paths)]


def infer_size_from_last_image(image_paths: list[ImageInput], fallback: int = DEFAULT_IMAGE_SIZE) -> int:
    for image_path in reversed(image_paths):
        image = _copy_source_image(image_path)
        if image is not None:
            return image.width

    return fallback


def save_mix_image(
    image_paths: list[ImageInput],
    selections: Mapping[str, MixSelection],
    image_size: ImageSize,
    output_name: str,
    file_format: str,
) -> Path:
    output_path = _output_path(image_paths, output_name or "Blend_Mix", file_format)
    image = build_mix_image(image_paths, selections, image_size)
    image.save(output_path)
    return output_path


def build_mix_image(
    image_paths: list[ImageInput],
    selections: Mapping[str, MixSelection],
    image_size: ImageSize,
) -> Image.Image:
    size = _normalize_image_size(image_size)
    channels = []

    for target_channel in CHANNELS:
        selection = selections[target_channel]
        channel = _resolve_mix_channel(image_paths, selection, target_channel, size)
        channels.append(channel)

    if selections["A"].image_name == "None":
        return Image.merge("RGB", channels[:3])
    return Image.merge("RGBA", channels)


def save_merge_image(
    image_paths: list[ImageInput],
    selections: Mapping[str, MergeSelection],
    image_size: ImageSize,
    output_name: str,
    file_format: str,
) -> Path:
    output_path = _output_path(image_paths, output_name or "Blend_Merge", file_format)
    image = build_merge_image(image_paths, selections, image_size)
    image.save(output_path)
    return output_path


def build_merge_image(
    image_paths: list[ImageInput],
    selections: Mapping[str, MergeSelection],
    image_size: ImageSize,
) -> Image.Image:
    size = _normalize_image_size(image_size)
    channels = []

    for target_channel in CHANNELS:
        selection = selections[target_channel]
        channel = _resolve_merge_channel(image_paths, selection, target_channel, size)
        channels.append(channel)

    if selections["A"].image_name == "None":
        return Image.merge("RGB", channels[:3])
    return Image.merge("RGBA", channels)


def save_split_images(
    image_paths: list[ImageInput],
    selections: Mapping[str, SplitSelection],
    image_size: ImageSize,
    output_name: str,
    file_format: str,
    keep_aspect_ratio: bool = False,
) -> list[Path]:
    base_name = output_name or "Blend_Split"
    size = _normalize_image_size(image_size)
    saved_paths: list[Path] = []

    for selection in selections.values():
        source = _find_image_source(image_paths, selection.image_name)
        if source is None:
            continue

        output_size = _size_for_source(source, size[0]) if keep_aspect_ratio else size

        image = _copy_source_image(source)
        if image is None:
            continue
        channel_image = dict(zip(CHANNELS, image.convert("RGBA").split(), strict=True))[selection.source_channel]
        resized = channel_image.convert("RGB").resize(output_size)

        suffix = selection.suffix or selection.source_channel
        output_path = _source_path(source).parent / f"{base_name}_{suffix}.{file_format}"
        resized.save(output_path)
        saved_paths.append(output_path)

    return saved_paths


def resolve_output_size(
    image_paths: list[ImageInput],
    selected_size: int,
    keep_aspect_ratio: bool,
    preferred_image_names: Iterable[str] = (),
) -> tuple[int, int]:
    target_width = max(1, int(selected_size))
    square_size = (target_width, target_width)

    if not keep_aspect_ratio:
        return square_size

    source = _find_first_image_source(image_paths, preferred_image_names)
    if source is None and image_paths:
        source = image_paths[-1]
    if source is None:
        return square_size

    return _size_for_source(source, target_width)


def _resolve_mix_channel(
    image_paths: list[ImageInput],
    selection: MixSelection,
    target_channel: str,
    size: tuple[int, int],
) -> Image.Image:
    if selection.image_name == "White":
        return _constant_channel(size, 255)
    if selection.image_name == "Black":
        return _constant_channel(size, 0)
    if selection.image_name == "Gray":
        return _constant_channel(size, 128)
    if selection.image_name == "None":
        return _constant_channel(size, 255)

    source = _find_image_source(image_paths, selection.image_name)
    if source is None:
        return _constant_channel(size, 255)

    image = _copy_source_image(source)
    if image is None:
        return _constant_channel(size, 255)
    source_channels = dict(zip(CHANNELS, image.convert("RGBA").split(), strict=True))
    return source_channels[selection.source_channel].convert("L").resize(size)


def _resolve_merge_channel(
    image_paths: list[ImageInput],
    selection: MergeSelection,
    target_channel: str,
    size: tuple[int, int],
) -> Image.Image:
    if selection.image_name == "White":
        return _constant_channel(size, 255)
    if selection.image_name == "Black":
        return _constant_channel(size, 0)
    if selection.image_name == "Gray":
        return _constant_channel(size, 128)
    if selection.image_name == "None":
        return _constant_channel(size, 255)

    source = _find_image_source(image_paths, selection.image_name)
    if source is None:
        return _constant_channel(size, 255)

    image = _copy_source_image(source)
    if image is None:
        return _constant_channel(size, 255)
    return image.convert("L").resize(size)


def _constant_channel(size: tuple[int, int], value: int) -> Image.Image:
    return Image.new("L", size, value)


def _normalize_image_size(image_size: ImageSize) -> tuple[int, int]:
    if isinstance(image_size, int):
        return (max(1, image_size), max(1, image_size))

    width, height = image_size
    return (max(1, int(width)), max(1, int(height)))


def _size_for_source(source: ImageInput, target_width: int) -> tuple[int, int]:
    image = _copy_source_image(source)
    if image is None:
        return (target_width, target_width)

    source_width, source_height = image.size
    if source_width <= 0 or source_height <= 0:
        return (target_width, target_width)

    return (target_width, max(1, round(target_width * source_height / source_width)))


def _find_first_image_source(image_paths: Iterable[ImageInput], image_names: Iterable[str]) -> ImageInput | None:
    for image_name in image_names:
        source = _find_image_source(image_paths, image_name)
        if source is not None:
            return source

    return None


def _find_image_source(image_paths: Iterable[ImageInput], image_name: str) -> ImageInput | None:
    if image_name in {"", "None", "White", "Black", "Gray", SEPARATOR_ITEM, EMPTY_ITEM}:
        return None

    for image_path in image_paths:
        path = _source_path(image_path)
        if not path.name.startswith(image_name):
            continue
        if isinstance(image_path, CachedImage) or path.is_file():
            return image_path

    return None


def _copy_source_image(source: ImageInput) -> Image.Image | None:
    if isinstance(source, CachedImage):
        return source.image.copy()

    try:
        with Image.open(source) as image:
            return image.copy()
    except OSError:
        return None


def _source_path(source: ImageInput) -> Path:
    if isinstance(source, CachedImage):
        return source.path
    return Path(source)


def _output_path(image_paths: list[ImageInput], output_name: str, file_format: str) -> Path:
    if not image_paths:
        raise ValueError("At least one image is required before exporting.")
    return _source_path(image_paths[0]).parent / f"{output_name}.{file_format}"
