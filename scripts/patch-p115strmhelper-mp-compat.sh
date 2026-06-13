#!/usr/bin/env bash
set -euo pipefail

container="${MP_CONTAINER:-moviepilot-v2}"
plugin_files=(
  "/app/app/plugins/p115strmhelper/__init__.py"
  "/config/plugins/p115strmhelper/__init__.py"
)
tmp_dir="$(mktemp -d)"

show_help() {
  cat <<'EOF'
Usage:
  MP_CONTAINER=<container> bash scripts/patch-p115strmhelper-mp-compat.sh

Applies the local P115StrmHelper compatibility patch inside the target
MoviePilot container, then runs py_compile against the patched plugin file.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

cleanup() {
  rm -rf "${tmp_dir}"
}
trap cleanup EXIT

echo "P115StrmHelper compatibility patch"
echo "container: ${container}"

patch_file() {
  local plugin_file="$1"
  local safe_name
  safe_name="$(echo "${plugin_file}" | tr '/:' '__')"
  local local_file="${tmp_dir}/${safe_name}"

  if ! docker exec "${container}" test -f "${plugin_file}"; then
    echo "skip missing: ${plugin_file}"
    return 0
  fi

  docker cp "${container}:${plugin_file}" "${local_file}"

  if grep -q "_optional_event_register(_TRANSFER_RENAME_BUILD_EVENT)" "${local_file}" && \
     grep -q "_optional_event_register(_TRANSFER_OVERWRITE_CHECK_EVENT)" "${local_file}"; then
    echo "already patched: ${plugin_file}"
  else
    python3 - "${local_file}" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

text = text.replace("    TransferRenameBuildEventData,\n", "")
text = text.replace("    TransferOverwriteCheckEventData,\n", "")

markers = [
    "from app.schemas.types import ChainEventType\n",
    "from app.schemas.types import EventType, MessageChannel, ChainEventType, MediaType\n",
]
compat = '''from app.schemas.types import EventType, MessageChannel, ChainEventType, MediaType

_TRANSFER_RENAME_BUILD_EVENT = getattr(ChainEventType, "TransferRenameBuild", None)
_TRANSFER_OVERWRITE_CHECK_EVENT = getattr(ChainEventType, "TransferOverwriteCheck", None)
try:
    from app.schemas import TransferRenameBuildEventData
except Exception:
    class TransferRenameBuildEventData:
        pass

try:
    from app.schemas import TransferOverwriteCheckEventData
except Exception:
    class TransferOverwriteCheckEventData:
        pass


def _optional_event_register(event_type):
    if event_type is None:
        def decorator(func):
            return func
        return decorator
    return eventmanager.register(event_type)
'''

marker = next((item for item in markers if item in text), None)
if marker is None and "def _optional_event_register(event_type):" not in text:
    raise SystemExit("cannot find ChainEventType import marker")
if marker is not None:
    text = text.replace(marker, compat, 1)

if "_TRANSFER_RENAME_BUILD_EVENT =" not in text:
    anchor = '_TRANSFER_OVERWRITE_CHECK_EVENT = getattr(ChainEventType, "TransferOverwriteCheck", None)\n'
    if anchor not in text:
        raise SystemExit("cannot find overwrite event anchor")
    text = text.replace(
        anchor,
        '_TRANSFER_RENAME_BUILD_EVENT = getattr(ChainEventType, "TransferRenameBuild", None)\n' + anchor,
        1,
    )

rename_fallback = '''try:
    from app.schemas import TransferRenameBuildEventData
except Exception:
    class TransferRenameBuildEventData:
        pass

'''
if "from app.schemas import TransferRenameBuildEventData" not in text:
    overwrite_try = '''try:
    from app.schemas import TransferOverwriteCheckEventData
'''
    if overwrite_try not in text:
        raise SystemExit("cannot find overwrite fallback anchor")
    text = text.replace(overwrite_try, rename_fallback + overwrite_try, 1)

decorator_pairs = [
    (
        "@eventmanager.register(ChainEventType.TransferRenameBuild)",
        "@_optional_event_register(_TRANSFER_RENAME_BUILD_EVENT)",
        "TransferRenameBuild",
    ),
    (
        "@eventmanager.register(ChainEventType.TransferOverwriteCheck)",
        "@_optional_event_register(_TRANSFER_OVERWRITE_CHECK_EVENT)",
        "TransferOverwriteCheck",
    ),
]

for old, new, label in decorator_pairs:
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise SystemExit(f"cannot find {label} decorator")

path.write_text(text)
PY
  fi

  docker cp "${local_file}" "${container}:${plugin_file}"
  docker exec "${container}" /opt/venv/bin/python -m py_compile "${plugin_file}"
  echo "patched and syntax check passed: ${plugin_file}"
}

for plugin_file in "${plugin_files[@]}"; do
  patch_file "${plugin_file}"
done

echo "restart MoviePilot, then verify AgentResourceOfficer /p115/health"
