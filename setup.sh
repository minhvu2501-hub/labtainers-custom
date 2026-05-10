#!/bin/bash
# setup.sh  -  Build Docker images locally for gateway_content_disarm lab
#
# Chạy script này SAU KHI imodule đã tải lab về:
#   bash ~/labtainer/trunk/labs/gateway_content_disarm/setup.sh
#
# Script sẽ:
#   1) Tìm registry và base image đang dùng
#   2) Build 3 Docker images từ Dockerfiles
#   3) Xác nhận build thành công
#   4) Hướng dẫn chạy lab

set -e

LAB="gateway_content_disarm"
REG="ptitwibu"

# Tự tìm thư mục lab
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$SCRIPT_DIR"

echo "========================================================"
echo "  $LAB  —  Local Docker Image Builder"
echo "========================================================"
echo ""
echo "Lab directory: $LAB_DIR"
echo ""

# ── Kiểm tra base image có sẵn không ───────────────────────────
echo "[Check] Tìm base image labtainer.base2..."
if docker images | grep -q "labtainer.base2"; then
    BASE_REG=$(docker images | grep "labtainer.base2" | awk '{print $1}' | head -1 | sed 's/\/labtainer.base2//')
    echo "  [OK] Found base image: ${BASE_REG}/labtainer.base2"
    REG="$BASE_REG"
else
    echo "  [WARN] labtainer.base2 not found locally."
    echo "         Trying to pull from $REG ..."
    docker pull ${REG}/labtainer.base2 || {
        echo "  [FAIL] Cannot pull base image. Please check network."
        exit 1
    }
fi

# ── Hàm build image ─────────────────────────────────────────────
build_image() {
    local container="$1"
    local image_tag="${REG}/${LAB}.${container}.student"
    local dockerfile="${LAB_DIR}/dockerfiles/Dockerfile.${LAB}.${container}.student"

    echo ""
    echo "[Build] ${container}  →  ${image_tag}"

    if docker images | grep -q "${REG}/${LAB}.${container}"; then
        echo "  [SKIP] Image already exists locally."
        return 0
    fi

    # Cần sys.tar tồn tại (dù rỗng)
    local sys_tar="${LAB_DIR}/${container}/sys_tar/sys.tar"
    if [ ! -f "$sys_tar" ]; then
        mkdir -p "${LAB_DIR}/${container}/sys_tar"
        tar -cf "$sys_tar" -T /dev/null
        echo "  Created empty sys.tar"
    fi

    # Cần home.tar tồn tại
    local home_tar="${LAB_DIR}/${container}/home_tar/home.tar"
    if [ ! -f "$home_tar" ]; then
        mkdir -p "${LAB_DIR}/${container}/home_tar"
        if [ -d "${LAB_DIR}/${container}/home_tar/files" ]; then
            tar -cf "$home_tar" -C "${LAB_DIR}/${container}/home_tar/files" .
        else
            tar -cf "$home_tar" -T /dev/null
        fi
        echo "  Created home.tar"
    fi

    # Cần lab-level tarballs
    local sys_lab="${LAB_DIR}/sys_${LAB}.tar.gz"
    local home_lab="${LAB_DIR}/${LAB}.tar.gz"
    [ -f "$sys_lab"  ] || tar -czf "$sys_lab"  -T /dev/null
    [ -f "$home_lab" ] || tar -czf "$home_lab" -T /dev/null

    docker build \
        --build-arg registry="${REG}" \
        --build-arg lab="${LAB}" \
        --build-arg labdir="${LAB_DIR}" \
        --build-arg imagedir="${container}" \
        --build-arg user_name="ubuntu" \
        --build-arg password="ubuntu" \
        --build-arg apt_source="ubuntu" \
        --build-arg version="1.0" \
        -t "${image_tag}" \
        -f "${dockerfile}" \
        "${LAB_DIR}" \
        && echo "  [OK] ${image_tag}" \
        || { echo "  [FAIL] Build failed for ${container}"; exit 1; }
}

# ── Build all containers ─────────────────────────────────────────
build_image "gateway_proxy"
build_image "user_pc"
build_image "fileserver"

# ── Xác nhận ────────────────────────────────────────────────────
echo ""
echo "========================================================"
echo "  BUILD COMPLETE! Images created:"
docker images | grep "${LAB}" | awk '{printf "  %-55s %s\n", $1":"$2, $7" "$8}'
echo ""
echo "  Chay lab:"
echo "    labtainer ${LAB}"
echo "========================================================"
