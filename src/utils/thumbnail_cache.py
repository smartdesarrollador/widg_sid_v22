# -*- coding: utf-8 -*-
"""
Thumbnail Cache Manager

Sistema de caché multinivel para thumbnails de imágenes:
- Caché en memoria (LRU) para acceso ultra-rápido
- Caché en disco para persistencia entre sesiones
- Generación automática de thumbnails con Pillow
"""

import logging
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from functools import lru_cache
from PIL import Image
from PyQt6.QtGui import QPixmap

logger = logging.getLogger(__name__)


class ThumbnailCache:
    """
    Sistema de caché de thumbnails con dos niveles:
    1. Memoria (LRU cache) - 100 thumbnails
    2. Disco (temp/thumbnails/) - Persistente

    Tamaños de thumbnail:
    - SMALL: 80x80 px (para grid compacto)
    - MEDIUM: 150x150 px (para grid normal)
    - LARGE: 300x300 px (para preview)
    """

    # Tamaños disponibles
    SIZE_SMALL = (80, 80)
    SIZE_MEDIUM = (150, 150)
    SIZE_LARGE = (300, 300)

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Inicializar caché de thumbnails

        Args:
            cache_dir: Directorio para caché en disco (opcional)
        """
        # Directorio de caché
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Por defecto: temp/thumbnails/ en directorio de la app
            import sys
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
            else:
                base_dir = Path(__file__).parent.parent.parent
            self.cache_dir = base_dir / 'temp' / 'thumbnails'

        # Crear directorios si no existen
        self._ensure_cache_dirs()

        # Estadísticas
        self.stats = {
            'hits': 0,
            'misses': 0,
            'disk_hits': 0,
            'generated': 0
        }

        logger.info(f"ThumbnailCache initialized: {self.cache_dir}")

    def _ensure_cache_dirs(self) -> None:
        """Crear directorios de caché si no existen"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            # Subdirectorios por tamaño
            (self.cache_dir / 'small').mkdir(exist_ok=True)
            (self.cache_dir / 'medium').mkdir(exist_ok=True)
            (self.cache_dir / 'large').mkdir(exist_ok=True)

            logger.debug("Cache directories created")

        except Exception as e:
            logger.error(f"Error creating cache directories: {e}")

    def _get_cache_path(self, image_path: str, size: Tuple[int, int]) -> Path:
        """
        Obtener ruta de caché para thumbnail

        Args:
            image_path: Ruta de imagen original
            size: Tamaño del thumbnail

        Returns:
            Path al archivo de caché
        """
        # Hash del path de la imagen (para nombre único)
        path_hash = hashlib.md5(image_path.encode()).hexdigest()

        # Determinar subdirectorio por tamaño
        if size == self.SIZE_SMALL:
            subdir = 'small'
        elif size == self.SIZE_MEDIUM:
            subdir = 'medium'
        else:
            subdir = 'large'

        # Ruta completa: temp/thumbnails/{size}/{hash}.jpg
        return self.cache_dir / subdir / f"{path_hash}.jpg"

    @lru_cache(maxsize=100)
    def _load_from_memory(self, cache_key: str) -> Optional[QPixmap]:
        """
        Caché en memoria usando LRU

        Args:
            cache_key: Clave única (path + size)

        Returns:
            QPixmap o None si no está en caché
        """
        # Esta función es solo un wrapper para el decorador lru_cache
        # El verdadero caché está en el decorador
        return None

    def get_thumbnail(self, image_path: str, size: Tuple[int, int] = None) -> Optional[QPixmap]:
        """
        Obtener thumbnail de imagen (desde caché o generando)

        Flujo:
        1. Verificar caché en memoria
        2. Verificar caché en disco
        3. Generar nuevo thumbnail
        4. Guardar en caché

        Args:
            image_path: Ruta completa a imagen original
            size: Tupla (ancho, alto) del thumbnail (default: MEDIUM)

        Returns:
            QPixmap con el thumbnail o None si falla
        """
        if not image_path:
            return None

        # Tamaño por defecto
        if size is None:
            size = self.SIZE_MEDIUM

        # Verificar que archivo existe
        img_path = Path(image_path)
        if not img_path.exists():
            logger.warning(f"Image file not found: {image_path}")
            return None

        # 1. Intentar cargar desde memoria
        cache_key = f"{image_path}_{size[0]}x{size[1]}"
        memory_result = self._load_from_memory(cache_key)
        if memory_result:
            self.stats['hits'] += 1
            return memory_result

        # 2. Intentar cargar desde disco
        cache_path = self._get_cache_path(image_path, size)
        if cache_path.exists():
            try:
                pixmap = QPixmap(str(cache_path))
                if not pixmap.isNull():
                    # Guardar en caché de memoria para próxima vez
                    self._cache_in_memory(cache_key, pixmap)
                    self.stats['disk_hits'] += 1
                    logger.debug(f"Thumbnail loaded from disk: {cache_path.name}")
                    return pixmap
            except Exception as e:
                logger.error(f"Error loading cached thumbnail: {e}")

        # 3. Generar nuevo thumbnail
        self.stats['misses'] += 1
        thumbnail = self._generate_thumbnail(image_path, size)

        if thumbnail:
            # Guardar en disco
            self._save_to_disk(thumbnail, cache_path)

            # Guardar en memoria
            self._cache_in_memory(cache_key, thumbnail)

            self.stats['generated'] += 1
            logger.debug(f"Thumbnail generated: {img_path.name}")

        return thumbnail

    def _generate_thumbnail(self, image_path: str, size: Tuple[int, int]) -> Optional[QPixmap]:
        """
        Generar thumbnail desde imagen original

        Args:
            image_path: Ruta a imagen original
            size: Tamaño deseado (ancho, alto)

        Returns:
            QPixmap con thumbnail o None si falla
        """
        try:
            # Abrir imagen con Pillow
            with Image.open(image_path) as img:
                # Convertir a RGB si es necesario (para PNGs con transparencia)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Crear fondo blanco
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Crear thumbnail (mantiene aspect ratio)
                img.thumbnail(size, Image.Resampling.LANCZOS)

                # Guardar temporalmente para cargar en QPixmap
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    tmp_path = tmp.name
                    img.save(tmp_path, 'JPEG', quality=85)

                # Cargar en QPixmap
                pixmap = QPixmap(tmp_path)

                # Eliminar archivo temporal
                Path(tmp_path).unlink(missing_ok=True)

                return pixmap if not pixmap.isNull() else None

        except Exception as e:
            logger.error(f"Error generating thumbnail for {image_path}: {e}")
            return None

    def _save_to_disk(self, pixmap: QPixmap, cache_path: Path) -> bool:
        """
        Guardar thumbnail en caché de disco

        Args:
            pixmap: QPixmap a guardar
            cache_path: Ruta donde guardar

        Returns:
            True si se guardó exitosamente
        """
        try:
            # Asegurar que el directorio padre existe
            cache_path.parent.mkdir(parents=True, exist_ok=True)

            # Guardar como JPEG (mejor compresión)
            success = pixmap.save(str(cache_path), 'JPEG', quality=85)

            if success:
                logger.debug(f"Thumbnail saved to disk: {cache_path.name}")

            return success

        except Exception as e:
            logger.error(f"Error saving thumbnail to disk: {e}")
            return False

    def _cache_in_memory(self, cache_key: str, pixmap: QPixmap) -> None:
        """
        Guardar thumbnail en caché de memoria

        Args:
            cache_key: Clave única
            pixmap: QPixmap a cachear
        """
        # El LRU cache está en _load_from_memory
        # Aquí usamos un dict simple adicional para almacenar
        if not hasattr(self, '_memory_cache'):
            self._memory_cache = {}

        self._memory_cache[cache_key] = pixmap

    def clear_memory_cache(self) -> None:
        """Limpiar caché en memoria"""
        if hasattr(self, '_memory_cache'):
            self._memory_cache.clear()

        # Limpiar LRU cache
        self._load_from_memory.cache_clear()

        logger.info("Memory cache cleared")

    def clear_disk_cache(self) -> int:
        """
        Limpiar caché en disco

        Returns:
            Número de archivos eliminados
        """
        deleted_count = 0

        try:
            for size_dir in ['small', 'medium', 'large']:
                dir_path = self.cache_dir / size_dir
                if dir_path.exists():
                    for cache_file in dir_path.glob('*.jpg'):
                        try:
                            cache_file.unlink()
                            deleted_count += 1
                        except Exception as e:
                            logger.error(f"Error deleting {cache_file}: {e}")

            logger.info(f"Disk cache cleared: {deleted_count} files deleted")

        except Exception as e:
            logger.error(f"Error clearing disk cache: {e}")

        return deleted_count

    def clear_all(self) -> int:
        """
        Limpiar todos los cachés (memoria + disco)

        Returns:
            Número de archivos eliminados del disco
        """
        self.clear_memory_cache()
        return self.clear_disk_cache()

    def get_cache_size(self) -> int:
        """
        Obtener tamaño total del caché en disco (bytes)

        Returns:
            Tamaño en bytes
        """
        total_size = 0

        try:
            for size_dir in ['small', 'medium', 'large']:
                dir_path = self.cache_dir / size_dir
                if dir_path.exists():
                    for cache_file in dir_path.glob('*.jpg'):
                        total_size += cache_file.stat().st_size
        except Exception as e:
            logger.error(f"Error calculating cache size: {e}")

        return total_size

    def get_stats(self) -> dict:
        """
        Obtener estadísticas de caché

        Returns:
            Dict con estadísticas
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'total_requests': total_requests,
            'memory_hits': self.stats['hits'],
            'disk_hits': self.stats['disk_hits'],
            'misses': self.stats['misses'],
            'generated': self.stats['generated'],
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_size_mb': self.get_cache_size() / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }

    def preload_thumbnails(self, image_paths: list, size: Tuple[int, int] = None) -> None:
        """
        Pre-cargar thumbnails en background

        Útil para cargar thumbnails antes de mostrar la galería

        Args:
            image_paths: Lista de rutas de imágenes
            size: Tamaño de thumbnails (default: MEDIUM)
        """
        if size is None:
            size = self.SIZE_MEDIUM

        logger.info(f"Preloading {len(image_paths)} thumbnails...")

        for img_path in image_paths:
            # Esto generará y cacheará los thumbnails
            self.get_thumbnail(img_path, size)

        logger.info("Thumbnails preloaded")
