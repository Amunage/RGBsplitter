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


def image_display_name(image_path: str | Path) -> str:
    return Path(image_path).stem


def channel_items(image_paths: Iterable[str | Path], include_special_items: bool = True) -> list[str]:
    items: list[str] = []
    if include_special_items:
        items.extend(CHANNEL_ITEMS)
        items.append(SEPARATOR_ITEM)
    items.extend(image_display_name(path) for path in image_paths)
    return items


def split_items(image_paths: Iterable[str | Path]) -> list[str]:
    return [EMPTY_ITEM, *(image_display_name(path) for path in image_paths)]


def infer_size_from_last_image(image_paths: list[str | Path], fallback: int = DEFAULT_IMAGE_SIZE) -> int:
    if not image_paths:
        return fallback

    with Image.open(image_paths[-1]) as image:
        return image.width


def save_mix_image(
    image_paths: list[str | Path],
    selections: Mapping[str, MixSelection],
    image_size: int,
    output_name: str,
    file_format: str,
) -> Path:
    output_path = _output_path(image_paths, output_name or "Blend_Mix", file_format)
    image = build_mix_image(image_paths, selections, image_size)
    image.save(output_path)
    return output_path


def build_mix_image(
    image_paths: list[str | Path],
    selections: Mapping[str, MixSelection],
    image_size: int,
) -> Image.Image:
    size = (image_size, image_size)
    channels = []

    for target_channel in CHANNELS:
        selection = selections[target_channel]
        channel = _resolve_mix_channel(image_paths, selection, target_channel, size)
        channels.append(channel)

    if selections["A"].image_name == "None":
        return Image.merge("RGB", channels[:3])
    return Image.merge("RGBA", channels)


def save_merge_image(
    image_paths: list[str | Path],
    selections: Mapping[str, MergeSelection],
    image_size: int,
    output_name: str,
    file_format: str,
) -> Path:
    output_path = _output_path(image_paths, output_name or "Blend_Merge", file_format)
    image = build_merge_image(image_paths, selections, image_size)
    image.save(output_path)
    return output_path


def build_merge_image(
    image_paths: list[str | Path],
    selections: Mapping[str, MergeSelection],
    image_size: int,
) -> Image.Image:
    size = (image_size, image_size)
    channels = []

    for target_channel in CHANNELS:
        selection = selections[target_channel]
        channel = _resolve_merge_channel(image_paths, selection, target_channel, size)
        channels.append(channel)

    if selections["A"].image_name == "None":
        return Image.merge("RGB", channels[:3])
    return Image.merge("RGBA", channels)


def save_split_images(
    image_paths: list[str | Path],
    selections: Mapping[str, SplitSelection],
    image_size: int,
    output_name: str,
    file_format: str,
) -> list[Path]:
    base_name = output_name or "Blend_Split"
    size = (image_size, image_size)
    saved_paths: list[Path] = []

    for selection in selections.values():
        source_path = _find_image_path(image_paths, selection.image_name)
        if source_path is None:
            continue

        with Image.open(source_path) as image:
            channel_image = dict(zip(CHANNELS, image.convert("RGBA").split(), strict=True))[selection.source_channel]
            resized = channel_image.convert("RGB").resize(size)

        suffix = selection.suffix or selection.source_channel
        output_path = Path(source_path).parent / f"{base_name}_{suffix}.{file_format}"
        resized.save(output_path)
        saved_paths.append(output_path)

    return saved_paths


def _resolve_mix_channel(
    image_paths: list[str | Path],
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

    source_path = _find_image_path(image_paths, selection.image_name)
    if source_path is None:
        return _constant_channel(size, 255)

    with Image.open(source_path) as image:
        source_channels = dict(zip(CHANNELS, image.convert("RGBA").split(), strict=True))
        return source_channels[selection.source_channel].convert("L").resize(size)


def _resolve_merge_channel(
    image_paths: list[str | Path],
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

    source_path = _find_image_path(image_paths, selection.image_name)
    if source_path is None:
        return _constant_channel(size, 255)

    with Image.open(source_path) as image:
        return image.convert("L").resize(size)


def _constant_channel(size: tuple[int, int], value: int) -> Image.Image:
    return Image.new("L", size, value)


def _find_image_path(image_paths: Iterable[str | Path], image_name: str) -> Path | None:
    if image_name in {"", "None", "White", "Black", "Gray", SEPARATOR_ITEM, EMPTY_ITEM}:
        return None

    for image_path in image_paths:
        path = Path(image_path)
        if path.name.startswith(image_name):
            return path

    return None


def _output_path(image_paths: list[str | Path], output_name: str, file_format: str) -> Path:
    if not image_paths:
        raise ValueError("At least one image is required before exporting.")
    return Path(image_paths[0]).parent / f"{output_name}.{file_format}"
