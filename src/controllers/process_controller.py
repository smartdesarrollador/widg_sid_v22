"""
Process Controller - Coordinates between UI and ProcessManager/ProcessExecutor

Responsabilidades:
- Coordinar entre UI y managers
- Validar datos antes de guardar
- Manejar eventos de UI
"""

import logging
import sys
from pathlib import Path
from typing import Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.process import Process
from core.process_manager import ProcessManager
from core.process_executor import ProcessExecutor
from database.db_manager import DBManager

logger = logging.getLogger(__name__)


class ProcessController:
    """Controller for process operations"""

    def __init__(self, db_manager: DBManager, config_manager=None, clipboard_manager=None):
        """
        Initialize ProcessController

        Args:
            db_manager: Database manager instance
            config_manager: Config manager instance
            clipboard_manager: Clipboard manager instance
        """
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.clipboard_manager = clipboard_manager

        # Initialize managers
        self.process_manager = ProcessManager(db_manager)
        self.process_executor = ProcessExecutor(db_manager, clipboard_manager)

        logger.info("ProcessController initialized")

    # ==================== PROCESS CRUD ====================

    def create_process(self, process: Process) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new process

        Args:
            process: Process object to create

        Returns:
            Tuple of (success, message, process_id)
        """
        return self.process_manager.create_process(process)

    def save_process(self, process: Process) -> Tuple[bool, str]:
        """
        Save (update) an existing process

        Args:
            process: Process object with updated data

        Returns:
            Tuple of (success, message)
        """
        return self.process_manager.update_process(process)

    def get_process(self, process_id: int) -> Optional[Process]:
        """Get process by ID"""
        return self.process_manager.get_process(process_id)

    def get_all_processes(self):
        """Get all processes"""
        return self.process_manager.get_all_processes()

    def delete_process(self, process_id: int) -> Tuple[bool, str]:
        """Delete a process"""
        return self.process_manager.delete_process(process_id)

    # ==================== EXECUTION ====================

    def execute_process(self, process_id: int) -> bool:
        """
        Execute a process

        Args:
            process_id: Process ID

        Returns:
            Success status
        """
        # Get process
        process = self.process_manager.get_process(process_id)
        if not process:
            logger.error(f"Process {process_id} not found")
            return False

        # Execute
        return self.process_executor.execute_process(process)

    def get_executor(self) -> ProcessExecutor:
        """Get process executor instance"""
        return self.process_executor

    def update_process_pin(self, process_id: int, is_pinned: bool) -> bool:
        """
        Update process pin state

        Args:
            process_id: Process ID
            is_pinned: New pin state

        Returns:
            Success status
        """
        try:
            # Get process
            process = self.process_manager.get_process(process_id)
            if not process:
                logger.error(f"Process {process_id} not found")
                return False

            # Update pin state
            process.is_pinned = is_pinned

            # Save to database
            success, msg = self.process_manager.update_process(process)

            if success:
                logger.info(f"Process {process_id} pin state updated to {is_pinned}")
            else:
                logger.error(f"Failed to update pin state: {msg}")

            return success
        except Exception as e:
            logger.error(f"Exception updating pin state: {e}")
            return False
